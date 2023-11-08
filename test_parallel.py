from multiprocessing import Process
from appium import webdriver
from time import sleep
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.common.exceptions import WebDriverException
import time
from appium_manager import main as appium_main_manager

def run_test_on_device(device_name, udid, port, device_port):
    desired_caps = {
        "platformName": "iOS",
        "appium:deviceName": device_name,
        "appium:udid": udid,
        "appium:automationName": "XCUITest",
        "appium:bundleId": "com.zhiliaoapp.musically",  # TikTok's bundle ID
        "appium:xcodeOrgId": "GXHKFX93A",  # Your Apple Team ID
        "appium:xcodeSigningId": "Apple Developer",  # The common name of your signing certificate
        "appium:noReset": True, # To prevent resetting the app state
        "appium:wdaLocalPort": device_port
    }

    print(f"Waiting 10 seconds before connecting to Appium on port {port}...")
    time.sleep(5)

    driver_url = f'http://localhost:{port}'
    print(f"Connecting to Appium with URL: {driver_url}")
    print(f"Using desired capabilities: {desired_caps}")

    # Set the timeout for the RemoteConnection
    RemoteConnection.set_timeout(200)
    
    driver = webdriver.Remote(driver_url, desired_caps)
   
    # This function attempts to execute a command with a timeout
    def execute_with_timeout(timeout, func, *args):
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
            else:
                print(f"Element '{element_name}' is not in the current view.")
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
            return safe_get_page_source(drv)  # Retry getting page source

    def print_button_names(drv):
        # Print all XCUIElementTypeButton elements
        buttons = drv.find_elements_by_class_name('XCUIElementTypeButton')
        for button in buttons:
            print(button.get_attribute('name'))  # This will print the name attribute of the button

    def retry_click_element(drv, by_locator, element_name):
        attempt_count = 0
        success = False

        while attempt_count < 3 and not success:  # Retry up to 3 times
            try:
                print(f"Retry attempt {attempt_count + 1} for clicking on '{element_name}'")
                click_element_if_present(drv, by_locator, element_name)
                success = True  # If click was successful, exit the loop
            except Exception as e:
                print(f"Attempt {attempt_count + 1} failed: {e}")
                attempt_count += 1
                sleep(5)  # Wait for 5 seconds before the next attempt

        if not success:
            print(f"Failed to click on '{element_name}' after {attempt_count} attempts. Proceeding further.")

    try:
        # Print the names of the buttons on the current page
        print("First page button names:")
        print_button_names(driver)

        # Click on 'Create' if it's present and clickable
        create_button_locator = (MobileBy.ACCESSIBILITY_ID, "Create")
        click_element_if_present(driver, create_button_locator, "Create")

        time.sleep(10) 

        # Print the names of the buttons on the new page without clearing the previous list
        print("Second page button names:")
        print_button_names(driver)

        # Click on 'Templates' if it's present and clickable
        templates_button_locator = (MobileBy.ACCESSIBILITY_ID, "recordPageUploadButton")
        click_element_if_present(driver, templates_button_locator, "recordPageUploadButton")

        # If 'Templates' wasn't clicked successfully, retry clicking it
        if not driver.find_elements(*templates_button_locator):
            print("'recordPageUploadButton' button wasn't found or clicked. Retrying...")
            retry_click_element(driver, templates_button_locator, "recordPageUploadButton")

        # Print the names of the buttons on the current page
        print("Third page button names:")
        print_button_names(driver)

        # New code: Locate the element with the provided XPath and perform an action (e.g., click)
        new_element_xpath = "(//XCUIElementTypeImage[@name='ic_album_camera_button_bg'])[1]"
        new_element_locator = (MobileBy.XPATH, new_element_xpath)

        # Perform the desired action with the new element, e.g., click
        click_element_if_present(driver, new_element_locator, "ic_album_camera_button_bg")

        time.sleep(5) 
        # Print the names of the buttons on the current page
        print("4st page button names:")
        print_button_names(driver)

        # Click on 'Create' if it's present and clickable
        create_button_locator = (MobileBy.ACCESSIBILITY_ID, "(editPageNextButton)")
        click_element_if_present(driver, create_button_locator, "(editPageNextButton)")

        time.sleep(5) 

        # Print the names of the buttons on the current page
        print("5st page button names:")
        print_button_names(driver)

        # Click on 'Create' if it's present and clickable
        create_button_locator = (MobileBy.ACCESSIBILITY_ID, "Post")
        click_element_if_present(driver, create_button_locator, "Post")

        # Safely get the page source
        page_source = safe_get_page_source(driver)
        
    

        buttons = execute_with_timeout(5, driver.find_elements_by_class_name, 'XCUIElementTypeButton')
        create_found = False
        templates_found = False

        if buttons:
            for button in buttons:
                try:
                    button_name = execute_with_timeout(5, button.get_attribute, 'name')
                    if button_name:
                        print(button_name)
                        if button_name == 'Create':
                            create_found = click_element_if_present(driver, (MobileBy.ACCESSIBILITY_ID, "Create"), "Create")
                        elif button_name == 'Templates':
                            templates_found = click_element_if_present(driver, (MobileBy.ACCESSIBILITY_ID, "Templates"), "Templates")

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
        # Quit the driver
        driver.quit()

def main():
    udid_to_port_mapping, udid_to_device_port_mapping = appium_main_manager()  # Start Appium and get UDID-to-port mapping
    processes = []

    for udid, port in udid_to_port_mapping.items():
        device_port = udid_to_device_port_mapping.get(udid)
        if udid == "00008020-00144CA40288003A":
            device_name = "iPhoneXs"
        elif udid == "92ebd89ccf7dfe3b698c322678a9630ef9b95823":
            device_name = "iPhone"
        else:
            device_name = "Unknown Device"

        p = Process(target=run_test_on_device, args=(device_name, udid, port, device_port))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    # At this point, all tests are done. You can also shut down the Appium instances if you'd like.

if __name__ == "__main__":
    main()