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
import json
import os
import random
import sys

coords_up = 89, 498, 230, 211
coords_down = 142, 200, 147, 498
coords_back = 41, 400, 300, 450
coords_update = 258, 150, 261, 480
coords_update2 = 258, 80, 261, 250

def read_usernames(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['usernames']

def initialize_status_file(udid, usernames):
    # Ensure the base directory exists
    base_directory = 'device_follow_status'
    os.makedirs(base_directory, exist_ok=True)

    # Construct the path to the status file using the device's UDID
    device_filename = os.path.join(base_directory, f"{udid}_status.json")

    try:
        with open(device_filename, 'r') as file:
            # Try to read the existing status file
            statuses = json.load(file)
    except FileNotFoundError:
        # If the file does not exist, initialize it
        statuses = {'statuses': [{'name': username, 'status': None} for username in usernames]}
        with open(device_filename, 'w') as file:
            json.dump(statuses, file, indent=4, sort_keys=True)

    return statuses

def filter_statuses_by(udid):
    # Path to the status file for the device
    base_directory = 'device_follow_status'
    status_file_path = os.path.join(base_directory, f"{udid}_status.json")

    filtered_usernames = []
    try:
        with open(status_file_path, 'r') as file:
            statuses = json.load(file)
            # Filter the statuses based on the provided status_filter
            filtered_usernames = [
                entry['name'] for entry in statuses['statuses']
                if entry['status'] == None
            ]
    except FileNotFoundError:
        print(f"No status file found for device {udid}")
    except json.JSONDecodeError:
        print(f"Error reading the status file for device {udid}")

    return filtered_usernames

def update_status(udid, username, status):
    # Construct the path to the status file using the device's UDID
    base_directory = 'device_follow_status'
    device_filename = os.path.join(base_directory, f"{udid}_status.json")

    try:
        with open(device_filename, 'r') as file:
            data = json.load(file)

        # Update the status for the specified username
        for user_status in data['statuses']:
            if user_status['name'] == username:
                user_status['status'] = status
                break

        # Write the updated data back to the file
        with open(device_filename, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)
            
    except FileNotFoundError:
        print(f"The status file {device_filename} does not exist. No updates made.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file {device_filename}.")


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
    sleep(3)
    search_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Search'`]")
    search_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(search_button_locator))
    search_button.click()
    sleep(2)
    user_tab_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label == 'Users'`]")
    user_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located(user_tab_locator))
    user_tab.click()
    sleep(3)
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

def like_comments_if_available(driver):
    attempts = 0
    max_attempts=5
    
    while attempts < max_attempts:
        try:
            screenshot_base64 = driver.get_screenshot_as_base64()
            data = test_model_recognition.run_yolo_object_detection(screenshot_base64)
            tap_coords = common_actions.get_coordinate(data, 'comment')
            select_comments = common_actions.tap_elements(driver, *tap_coords)
            if not select_comments:
                raise Exception("Failed to open comments.")
            sleep(2)
            common_actions.swipe(driver, *coords_up)
            sleep(2)
        except Exception as e:
            print(f"Error while trying to access comments: {e}")
            return        
        # Take a screenshot and analyze for like buttons
        screenshot_base64 = driver.get_screenshot_as_base64()
        coordinates_likes = elements_detector.process_image(screenshot_base64, element_to_analyze='likes')
        if coordinates_likes:
            # Attempt to like the comment if like coordinates are found
            select_likes = common_actions.tap_elements(driver, *coordinates_likes)
            if select_likes:
                common_actions.swipe(driver, *coords_down)
                print("Successfully liked a comment.")
                break  # Exit loop after successful like
            else:
                raise Exception("Failed to like comments, even though likes were visible.")
        else:
            # No like elements found, swipe down to try next set of comments
            common_actions.swipe(driver, *coords_down)
            sleep(2)
            common_actions.swipe(driver, *coords_down)
            print("No likes found, swiping to next comments...")
        
    
        attempts += 1  # Increment attempt counter

    if attempts >= max_attempts:
        print("Reached maximum attempts to find and like comments.")
        # Optionally, raise an exception or handle the max attempt reach as needed

def check_follow_state(driver):
    try:
        # Try to find the Follow button
        follow_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`name CONTAINS 'Follow'`]")
        follow_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(follow_button_locator))
        # Check if the Follow button indicates an "unfollowed" state
        if follow_button:
          # update_status(udid, username, "followed")
            print("The profile is not followed.")
            return {'button': follow_button, 'status': 'unfollowed'}
        else:
            print("The profile is followed.")
    except:
        # Follow button not found, check other elements
        buttons = driver.find_elements(By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeOther[`name == 'TTKProfileCTARelationComponent'`]/XCUIElementTypeButton")
        print(len(buttons))
        if len(buttons) == 2:
            width_first = buttons[0].size['width']
            width_second = buttons[1].size['width']
            # Assuming the second button has no StaticText inside and comparing sizes and positions
            if width_first > width_second:
                print(width_first > width_second)
                static_texts = buttons[1].find_elements(By.IOS_CLASS_CHAIN, f"**//XCUIElementTypeStaticText")
                if not static_texts:  # No StaticText in the second button
                    recommend_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label CONTAINS 'People you may be interested in'`]")
                    recommend_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(recommend_button_locator))
                    # Comparing sizes and positions
                    if buttons[1].size == recommend_button.size and buttons[1].location['y'] == recommend_button.location['y']:
                        print("The profile is in a custom followed state.")
                        return {'button': None, 'status': 'followed'}
                    else:
                        print("State is ambiguous or unexpected.")
                        return {'button': None, 'status': 'unexpected'}
                else:
                    print("Unexpected structure for second button.")
                    return {'button': None, 'status': 'unexpected'}
            else:
                print("Sizes do not match expected conditions for followed state.")
                return {'button': None, 'status': 'unexpected'}
        else:
            print("Unexpected number of buttons in the relation component.")
            return {'button': None, 'status': 'unexpected'}


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

    print(f"session_id = {driver.session_id} for {udid}")
    
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
    
    usernames = read_usernames('user_to_follow.json')
    status_data = initialize_status_file(udid, usernames)
    print("create conf")
    filtered_usernames = filter_statuses_by(udid)
    print(filtered_usernames)

    for username in filtered_usernames:
        print(f"Testing for username: {username}")
        # Open search and perform search for the username
        # Here you would call the specific functions for performing the search and interacting with the profile
        # For example:
        perform_search_and_action(driver, username)
    
        sleep(5)
        common_actions.swipe(driver, *coords_up)
        x = 100
        y = 200
        driver.execute_script('mobile: doubleTap', {'x':x, 'y':y})
        sleep(10)
        common_actions.swipe(driver,*coords_up)
        #sleep(10)
        #x = 100
        #y = 200
        #driver.execute_script('mobile: doubleTap', {'x':x, 'y':y})

        #sleep(10)
        #coords = 189, 510, 230, 211
        #common_actions.swipe(driver,*coords)

        sleep(10)
        like_comments_if_available(driver)
        sleep(2)    
        common_actions.swipe(driver, *coords_up)
        sleep(2)
        common_actions.swipe(driver, *coords_back)
        sleep(2)
        common_actions.swipe(driver, *coords_update)

        new_settings = {
            'waitForIdleTimeout': 10,
            'customSnapshotTimeout': 15,
            'animationCoolOffTimeout': 2,
            'snapshotMaxDepth': 50
        }
        driver.update_settings(new_settings)
        print ("Settings updated on profile")
        sleep(2)
        common_actions.swipe(driver, *coords_update)
        sleep(2)
        common_actions.swipe(driver, *coords_update2)
        sleep(2)
        follow_state_result = check_follow_state(driver)
        if follow_state_result['button'] and follow_state_result['status'] == 'unfollowed':
            print("Clicking the Follow button...")
            follow_state_result['button'].click()  # Click the button if it's unfollowed
            print("Profile followed.")
            update_status(udid, username, 'followed')

        elif follow_state_result['status'] == 'followed':
            update_status(udid, username, 'followed')
            print(f"No action needed. Profile is already followed")
        else:
            print(f"An error occurred or button not found: {follow_state_result.get['status']}")

        sleep(2)
        common_actions.swipe(driver, *coords_update2)
        sleep(2)
        common_actions.swipe(driver, *coords_update2)
        follow_state_recheck_result = check_follow_state(driver)
        if follow_state_recheck_result['button'] and follow_state_recheck_result['status'] == 'unfollowed':
            print("Maybe banned...")
            sys.exit(1)
        
        sleep(5)
        coords_back2 = 55, 110, 300, 112
        common_actions.swipe(driver, *coords_back2)
        print ("swipe to the left")
        sleep(5)
        #back_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label CONTAINS 'Back'`]")
        #back_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(back_button_locator))
        #back_button.click()
        #print ("back 1")

        sleep(5)
        back_button_locator2 = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label CONTAINS 'Back'`]")
        back_button2 = WebDriverWait(driver, 10).until(EC.presence_of_element_located(back_button_locator2))
        back_button2.click()
        print ("back 2")
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
        back_button_locator3 = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label CONTAINS 'Back'`]")
        back_button3 = WebDriverWait(driver, 10).until(EC.presence_of_element_located(back_button_locator3))
        back_button3.click()
        print ("back 3")
        driver.update_settings(new_settings)
        sleep(5)
        feed_swipping.tiktok_swiper(driver, 5)

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
