from selenium import webdriver
from selenium.webdriver.common.by import By
from appium.webdriver.common.mobileby import MobileBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.remote.remote_connection import RemoteConnection
from multiprocessing import Process
from appium_manager import main as appium_main_manager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCATOR_MAPPING = {
    'accessibility_id': 'accessibility id',
    'id': By.ID,
    'xpath': By.XPATH,
    'name': By.NAME,
    'css': By.CSS_SELECTOR,
    'class_name': By.CLASS_NAME,
}

# Class to manage the WebDriver
class WebDriverManager:
    def __init__(self, device_name, udid, port, device_port):
        self.capabilities = self.get_capabilities(udid, device_name, device_port)
        RemoteConnection.set_timeout(200)
        self.driver = webdriver.Remote(f'http://localhost:{port}', self.capabilities)

    @staticmethod
    def get_capabilities(udid, device_name, device_port):
        capabilities = {
        "appium:platformName": "iOS",
        "appium:deviceName": device_name,
        "appium:udid": udid,
        "appium:wdaLocalPort": device_port,
        "appium:automationName": "XCUITest",
        "appium:bundleId": "com.apple.shortcuts", 
        "appium:xcodeOrgId": "3GXHKFX93A",
        "appium:xcodeSigningId": "Apple Development", 
        "appium:showXcodeLog": False,
        "appium:appPushTimeout": 5000,
        "appium:waitForQuiescence": True,
        "appium:noReset": True 
        }
        return capabilities

    def quit_driver(self):
        self.driver.quit()

# Utility functions

def safe_get_page_source(drv):
    try:
        return drv.page_source
    except StaleElementReferenceException:
        print("StaleElementReferenceException while getting page source. Retrying...")
        return safe_get_page_source(drv)

def print_button_names(drv, page_number):
    time.sleep(10)
    WebDriverWait(drv, 10).until(EC.presence_of_element_located(('-ios class chain', '**/XCUIElementTypeButton[`visible == 1`]')))
    buttons = drv.find_elements('-ios class chain', '**/XCUIElementTypeButton[`visible == 1`]')
    print(f"{page_number} page button names:")
    for button in buttons:
        try:
            button_name = button.get_attribute('name')
            logger.info(f"Button name: {button_name}")
        except StaleElementReferenceException:
            logger.warning("Encountered StaleElementReferenceException while retrieving button name.")
        except Exception as e:
            logger.error(f"An error occurred while getting button attribute: {e}")

def click_element(drv, by_locator, element_name, timeout=2):
    try:
        element = drv.find_element(*by_locator)
        if element.get_attribute('name') == element_name:
            WebDriverWait(drv, timeout).until(EC.element_to_be_clickable(by_locator))
            element.click()
            print(f"Clicked on the '{element_name}' button.")
            return True
        else:
            print(f"Element found, but its name '{element.get_attribute('name')}' does not match the expected '{element_name}'. Not clicking.")
            return False
    except NoSuchElementException:
        print(f"{element_name} was not found on the current page.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return False

def process_page(drv, button_name, page_number, locator_type):
    print_button_names(drv, page_number)
    locator_type_value = LOCATOR_MAPPING.get(locator_type.lower())
    if locator_type_value is None:
        print(f"Locator type '{locator_type}' is not defined.")
        return
    button_locator = (locator_type_value, button_name)
    click_element(drv, button_locator, button_name)  

def run_test_on_device(device_name, udid, port, device_port):
    driver_manager = WebDriverManager(device_name, udid, port, device_port)
    try:
    # Process each page
        process_page(driver_manager.driver, "6A000000-0000-0000-CA45-000000000000", "Tiktok test",'id')
        process_page(driver_manager.driver, "recordPageUploadButton", "Second","accessibility_id")
        process_page(driver_manager.driver, "ic_album_camera_button_bg", "Third","accessibility_id")
        process_page(driver_manager.driver, "(editPageNextButton)", "4th","accessibility_id")
        process_page(driver_manager.driver, "Post", "5th","accessibility_id")

    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        driver_manager.quit_driver()

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

    for p in processes:
        p.join()

if __name__ == "__main__":
    main()
