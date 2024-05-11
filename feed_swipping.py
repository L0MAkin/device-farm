#following_test.py
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
from PIL import Image
import random
import test_model_recognition
import common_actions

swipe_count = 10
swipe_up_coords = 89, 498, 230, 211
swipe_back_coords = 41, 420, 320, 425
delay_ranges = {
    'Unfollow': (5, 10),
    'Sponsored': (1, 5),
    'Live': (1, 5),
    'Follow': (15, 20)
}

def determine_state(data):
    data = common_actions.preprocess_data(data)
    indicators = ['comment', 'like', 'profile_img', 'save', 'share']
    indicators_counts = sum(1 for label in indicators if label in data)
    state_criteria = indicators_counts >=3
    
    follow_icon_present = 'follow_icon' in data
    follow_icon_high_confidence = any(item['confidence'] >= 0.5 for item in data.get('follow_icon', []))
    
    sponsored_conf = max(
        [item['confidence'] for label in ['sponsore_button', 'sponsore_label'] for item in data.get(label, [])],
        default=0
    )
    live_conf = max(
        [item['confidence'] for label in ['live_frame', 'live_label'] for item in data.get(label, [])],
        default=0
    )
    
    # Apply rules
    if sponsored_conf >= 0.5:
        return "Sponsored"
    elif live_conf >= 0.5:
        return "Live"
    elif state_criteria:
        if follow_icon_present and not follow_icon_high_confidence:
            # If follow_icon is present but doesn't have high confidence
            return "Follow"
        elif not follow_icon_present or follow_icon_high_confidence:
            # If follow_icon is not present or it's present with high confidence, considering it as "Unfollow"
            return "Unfollow"
    else:
        return "Indeterminate"


def tiktok_swiper(driver, swipe_count):
    for _ in range(swipe_count):
        screenshot_base64 = driver.get_screenshot_as_base64()
        data = test_model_recognition.run_yolo_object_detection(screenshot_base64)

        if not data:
            print("No data retrieved from screenshot.")
            continue  # Skip to the next iteration if no data

        state = determine_state(data)
        print(f"Determined state: {state}")
        delay_range = delay_ranges.get(state, (1, 2))  # Default delay range if state is not defined
        delay = random.randint(*delay_range)

        if state in ['Follow', 'Unfollow']:  # Assuming you want actions for these states
            tap_coords = common_actions.get_coordinate(data) if 'like' in data else None
            common_actions.tap_elements(driver, *tap_coords)  # Tap or double-tap on 'like'
            
            # Swipe logic (adjust coordinates as per your app's swipe direction)
            common_actions.swipe(driver, *swipe_up_coords)
        else:
            print(f"'{state}' swipe without action.")
            common_actions.swipe(driver, *swipe_up_coords)

        sleep(delay)  # Delay between swipes or actions


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

    #Open tiktok
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

    tiktok_swiper(driver, swipe_count)


    



'''# Example data
data = {'share': [{'coordinates': {'x_min': 625, 'y_min': 954, 'x_max': 692, 'y_max': 1010}, 'label': 'share: 0.95', 'confidence': 0.9518455862998962}], 'profile_img': [{'coordinates': {'x_min': 616, 'y_min': 572, 'x_max': 707, 'y_max': 662}, 'label': 'profile_img: 0.95', 'confidence': 0.9517504572868347}], 'search': [{'coordinates': {'x_min': 636, 'y_min': 58, 'x_max': 698, 'y_max': 104}, 'label': 'search: 0.94', 'confidence': 0.9436790347099304}], 'comment': [{'coordinates': {'x_min': 628, 'y_min': 840, 'x_max': 694, 'y_max': 897}, 'label': 'comment: 0.94', 'confidence': 0.9363281726837158}], 'like': [{'coordinates': {'x_min': 629, 'y_min': 715, 'x_max': 696, 'y_max': 772}, 'label': 'like: 0.94', 'confidence': 0.9357420802116394}], 'sponsore_label': [{'coordinates': {'x_min': 25, 'y_min': 1134, 'x_max': 146, 'y_max': 1166}, 'label': 'sponsore_label: 0.92', 'confidence': 0.9198853373527527}]}

state = determine_state(data)
coords = get_coordinate(data)
print(f"Determined state: {state}")
print(f"Determined coords: {coords}")'''

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

