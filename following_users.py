from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.common.exceptions import TimeoutException
from appium.webdriver.common.touch_action import TouchAction
from multiprocessing import Process
import subprocess
from time import sleep
from appium.options.ios import XCUITestOptions
from appium import webdriver
import base64
import elements_detector
import common_actions
import test_model_recognition
import feed_swipping

coords_up = 89, 498, 230, 211
coords_down = 142, 200, 147, 498
coords_back = 41, 400, 300, 420

usernames = [
    "effyafterdark",
    "xqueenkalin",
    "janicee.janicee",
    "kaylavoid",
    "babyminaox",
    "notburnttoasthehe",
    "glizzyx11",
    "psycheswings",
    "maligoshik",
    "iluvmeww",
    "hippicam",
    "maddythesillygoose0",
    "kimmy_baby_",
    "leanortizz",
    "alyri_tv",
    "momycarterx",
    "elizabethvasilenko",
    "skybribaby",
    "anavavx",
    "ameliagething"
]

def perform_search_and_action(driver, username):
    screenshot_base64 = driver.get_screenshot_as_base64()
    data = test_model_recognition.run_yolo_object_detection(screenshot_base64)
    tap_coords = common_actions.get_coordinate(data, 'search')
    select_search = common_actions.tap_elements(driver, *tap_coords)
    if not select_search:
        raise Exception("Failed to open comments.")
    sleep(5)
    # Step 13: Back to default state and delete video from folder
    new_settings = {
        'waitForIdleTimeout': 10,
        'customSnapshotTimeout': 15,
        'animationCoolOffTimeout': 2,
        'snapshotMaxDepth': 50
    }
    driver.update_settings(new_settings)

    #search_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeStaticText[`label == 'Search'`]")
    #search = WebDriverWait(driver, 10).until(EC.presence_of_element_located(search_locator))
    #search.click()

    search_area_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeSearchField")
    search_area = WebDriverWait(driver, 60).until(EC.presence_of_element_located(search_area_locator))
    description = f'{username}'
    search_area.send_keys(description)
    sleep(5)
    search_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Search'`]")
    search_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(search_button_locator))
    search_button.click()

    user_tab_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Users'`]")
    user_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located(user_tab_locator))
    user_tab.click()
    sleep(5)
    user_select_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`name CONTAINS '{username}'`]")
    user_select = WebDriverWait(driver, 10).until(EC.presence_of_element_located(user_select_locator))
    user_select.click()


    first_video_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeWindow[1]/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeOther/XCUIElementTypeScrollView/XCUIElementTypeOther/XCUIElementTypeCollectionView/XCUIElementTypeCell[3]")
    first_video = WebDriverWait(driver, 10).until(EC.presence_of_element_located(first_video_locator))
    # Settings update
    new_settings = {
        'waitForIdleTimeout': 0,
        'customSnapshotTimeout': 0,
        'animationCoolOffTimeout': 0
    }
    driver.update_settings(new_settings)
    # Open tiktok
    first_video.click()

    new_settings = {
        'snapshotMaxDepth': 1
    }
    driver.update_settings(new_settings)


def run_tests_on_device(udid, appium_port, wda_port, device_name):
    print(f"Running tests on device {udid} via Appium server on port {appium_port}...")
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.device_name = device_name  # Replace with your device name variable
    options.udid = udid  # Replace with your UDID variable
    options.automation_name = "XCUITest"
    options.bundle_id = "com.apple.shortcuts"
    options.xcode_org_id = "3GXHKFX93A"
    options.xcode_signing_id = "Apple Development"
    options.show_xcode_log = False
    options.set_capability("appPushTimeout", 5000)
    options.new_command_timeout = 2000
    options.wda_local_port = wda_port  # Replace with your WDA local port variable
    options.clear_system_files = True
    options.auto_dismiss_alerts = True
    options.no_reset = True
    options.set_capability("skipLogCapture", True)

    driver = webdriver.Remote(f'http://localhost:{appium_port}', options=options)

    print(f"session_id = {driver.session_id} for{udid}")
    
    open_tiktok_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ACCESSIBILITY_ID, "Open Tiktok Feed"))
        )
    # Settings update
    new_settings = {
        'waitForIdleTimeout': 0,
        'customSnapshotTimeout': 0,
        'animationCoolOffTimeout': 0
    }
    driver.update_settings(new_settings)
    # Open tiktok
    open_tiktok_button.click()
    new_settings = {
        'snapshotMaxDepth': 1
    }
    driver.update_settings(new_settings)
    sleep(10)
    #Open search
    for username in usernames:
        print(f"Testing for username: {username}")
        # Open search and perform search for the username
        # Here you would call the specific functions for performing the search and interacting with the profile
        # For example:
        perform_search_and_action(driver, username)
    
        sleep(5)
        common_actions.swipe(driver,*coords_up)
        x = 100
        y = 200
        driver.execute_script('mobile: doubleTap', {'x':x, 'y':y})
        sleep(10)
        common_actions.swipe(driver,*coords_up)
        sleep(10)
        x = 100
        y = 200
        driver.execute_script('mobile: doubleTap', {'x':x, 'y':y})

        sleep(10)
        coords = 189, 510, 230, 211
        common_actions.swipe(driver,*coords)
        sleep(10)
        screenshot_base64 = driver.get_screenshot_as_base64()
        data = test_model_recognition.run_yolo_object_detection(screenshot_base64)
        tap_coords = common_actions.get_coordinate(data, 'comment')
        select_comments = common_actions.tap_elements(driver, *tap_coords)
        if not select_comments:
            raise Exception("Failed to open comments.")
        sleep(2)
        coords = 189, 510, 230, 211
        common_actions.swipe(driver,*coords)
        sleep(2)
        screenshot_base64 = driver.get_screenshot_as_base64()
        coordinates_likes = elements_detector.process_image(screenshot_base64, element_to_analyze = 'likes')
        select_likes = common_actions.tap_elements(driver, *coordinates_likes)
        if not select_likes:
            raise Exception("Failed to like comments.")
        sleep(5)
        common_actions.swipe(driver, *coords_back)
        sleep(5)
        common_actions.swipe(driver, *coords_back)
        sleep(2)
        common_actions.swipe(driver, *coords_down)

        new_settings = {
            'waitForIdleTimeout': 10,
            'customSnapshotTimeout': 15,
            'animationCoolOffTimeout': 2,
            'snapshotMaxDepth': 50
        }
        driver.update_settings(new_settings)

        follow_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`name CONTAINS 'Follow'`]")
        follow_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(follow_button_locator))
        follow_button.click()
        sleep(5)
        coords_back2 = 25, 130, 300, 131
        common_actions.swipe(driver, *coords_back2)

        back_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Back to previous screen'`]")
        back_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(back_button_locator))
        back_button.click()
        sleep(3)
        new_settings = {
            'waitForIdleTimeout': 0,
            'customSnapshotTimeout': 0,
            'animationCoolOffTimeout': 0
        }
        driver.update_settings(new_settings)
        new_settings = {
            'snapshotMaxDepth': 1
        }
        back_button_locator2 = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Back to previous screen'`]")
        back_button2 = WebDriverWait(driver, 10).until(EC.presence_of_element_located(back_button_locator2))
        back_button2.click()
        driver.update_settings(new_settings)
        sleep(5)
        feed_swipping.tiktok_swiper(driver, 10)
        driver.quit()
    

def main():
    udids = common_actions.get_connected_udids()
    appium_processes = []
    processes = []

    for index, udid in enumerate(udids):
        device_name = f"iPhone({index+1})"
        appium_port = common_actions.BASE_PORT + index * 1  # Increment by 1 to avoid port conflicts
        wda_port = common_actions.WDA_BASE_PORT + index * 1
        
        appium_process = common_actions.start_appium_server(udid, appium_port, wda_port)
        appium_processes.append(appium_process)

        process = Process(target=run_tests_on_device, args=(udid, appium_port, wda_port, device_name))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

if __name__ == '__main__':
    main()
