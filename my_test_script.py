# your_test_script.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from appium.webdriver.extensions.clipboard import ClipboardContentType
import time
import base64
import logging

# Core functions: ------------------------

url_to_copy = f"https://drive.google.com/uc?export=download&id=13Y5UyxU0vOkL3_KuHb1e3ih79Qitgq0X"

def set_clipboard_content(driver, content):
    try:
        print (f"URL{content}")
        byte_data = content.encode('UTF-8')
        print (f"encoded_data = {byte_data}")
        driver.set_clipboard(content=byte_data, content_type='URL')
        print("Clipboard content set successfully.")
    except Exception as e:
        print(f"Error setting clipboard content: {e}")

def execute_with_timeout(driver, timeout, func, *args):
    try:
        driver.set_script_timeout(timeout)
        return func(*args)
    except Exception as e:
        print(f"Error executing with timeout: {e}")
        return None


def click_element_if_present(drv, by_locator, element_name):
    try:
        element = drv.find_element(*by_locator)
        if element.get_attribute('name') == element_name:
            element.click()
            print(f"Clicked on the '{element_name}' button.")
            return True
    except NoSuchElementException:
        print(f"{element_name} was not found on the current page.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return False


def safe_get_page_source(drv):
    try:
        return drv.page_source
    except StaleElementReferenceException:
        print("StaleElementReferenceException while getting page source. Retrying...")
        return safe_get_page_source(drv)


def print_button_names(drv, page_number):
    time.sleep(10)  # Consider parameterizing this sleep duration if needed for flexibility.
    WebDriverWait(drv, 10).until(EC.presence_of_element_located(('-ios class chain', '**/XCUIElementTypeButton[`visible == 1`]')))
    buttons = drv.find_elements('-ios class chain', '**/XCUIElementTypeButton[`visible == 1`]')
    print(f"{page_number} page button names:")
    for button in buttons:
        print(button.get_attribute('name'))


def process_page(drv, button_name, page_number):
    print_button_names(drv, page_number)
    button_locator = (By.ACCESSIBILITY_ID, button_name)
    click_element_if_present(drv, button_locator, button_name)


# Test Sequence Wrapper Function

def test_sequence(driver):
    try:
         # Set a URL to the clipboard before processing pages
        driver.execute_script('mobile: activateApp', {'bundleId': 'com.facebook.WebDriverAgentRunner.xctrunner'})
        set_clipboard_content(driver, url_to_copy)
        driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})

        # Process each page
        process_page(driver, "Add Video", "Add Video")
        process_page(driver, "Tiktok test", "Tiktok test")
        #process_page(driver, "recordPageUploadButton", "Second")
        #process_page(driver, "ic_album_camera_button_bg", "Third")
        #process_page(driver, "(editPageNextButton)", "4th")
        #process_page(driver, "Post", "5th")

        # Additional logic with buttons
        buttons = execute_with_timeout(driver, 5, driver.find_elements_by_class_name, 'XCUIElementTypeButton')
        create_found = False
        templates_found = False
        if buttons:
            for button in buttons:
                try:
                    button_name = execute_with_timeout(driver, 5, button.get_attribute, 'name')
                    if button_name == 'Create':
                        create_found = click_element_if_present(driver, (By.ACCESSIBILITY_ID, "Create"), "Create")
                    elif button_name == 'Templates':
                        templates_found = click_element_if_present(driver, (By.ACCESSIBILITY_ID, "Templates"), "Templates")
                    if create_found or templates_found:
                        print("Required element clicked. Stopping further element search.")
                        break
                except StaleElementReferenceException:
                    print("Caught StaleElementReferenceException - moving to next element.")
                    continue

    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Test DONE")
