# my_test_script.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from appium.webdriver.extensions.clipboard import ClipboardContentType
from selenium.common.exceptions import TimeoutException
from appium.webdriver.common.touch_action import TouchAction
import time
from datetime import datetime
import json
import tiktok_requests
import text_recognition
import io
from PIL import Image
import base64


# Core functions: ------------------------
def set_clipboard_content(driver, content):
    try:
        print (f"URL{content}")
        byte_data = content.encode('UTF-8')
        print (f"encoded_data = {byte_data}")
        driver.set_clipboard(content=byte_data, content_type='URL')
        print("Clipboard content set successfully.")
    except Exception as e:
        print(f"Error setting clipboard content: {e}")


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

def process_page(drv, button_name, page_number):
    #print_button_names(drv, page_number)
    button_locator = (By.ACCESSIBILITY_ID, button_name)
    result = click_element_if_present(drv, button_locator, button_name)
    if result:
        print(f"Successfully processed page {page_number} for '{button_name}'.")
    else:
        print(f"Failed to process page {page_number} for '{button_name}'.")
    return result

def find_account_name_and_coordinates(ocr_results, account_names):
    # Convert a single account name into a list if necessary
    if isinstance(account_names, str):
        account_names = [account_names]
    print(account_names)
    print(ocr_results)

    for result in ocr_results:
        if isinstance(result, dict) and 'text' in result and 'bounding_box' in result:
            for account_name in account_names:
                if account_name in result['text']:
                    bounding_box = result['bounding_box']
                    coordinates = {
                        'x': bounding_box['x'],
                        'y': bounding_box['y'],
                        'width': bounding_box['width'],
                        'height': bounding_box['height']
                    }
                    return account_name, coordinates

    print("Account name not found in OCR results.")
    return None, None

def get_current_account(device_status_file_path, image_base64):
    try:
        # Load account names from the configuration
        data = get_data_from_config(device_status_file_path, "videos")
        #print(data)
        account_names = []
        for video_info in data:
            account_names.append(video_info['account'])

        # Get OCR results from the screenshot
        ocr_results = text_recognition.process_image(image_base64, should_crop=True)
        # Search OCR results for any of the account names
        account_name, coordinates = find_account_name_and_coordinates(ocr_results, account_names)
        
        return account_name, coordinates
    
    except Exception as e:
        print(f"Error during OCR processing or file reading: {e}")
        return None

def process_account_videos(driver, current_account, device_status_file_path):
    try:
        with open(device_status_file_path, 'r') as file:
            device_video_config = json.load(file)
    except FileNotFoundError:
        raise Exception(f"Configuration file not found: {device_status_file_path}")
    except json.JSONDecodeError:
        raise Exception(f"Error decoding JSON from file: {device_status_file_path}")

    for video_info in device_video_config['videos']:
        if video_info['account'] == current_account:
            if not video_info['post_status']:
                return video_info['url'], current_account, video_info['description']  # URL to process, account name

    # If no video is found for the current account, find the next eligible account
    eligible_accounts = find_eligible_accounts(current_account, device_video_config)
    if eligible_accounts:
        next_account = eligible_accounts[0]
        if switch_account(driver, next_account):
            # Repeat the search for the next account
            return process_account_videos(driver, next_account, device_status_file_path)
        else:
            raise Exception(f"Failed to switch to account: {next_account}")
    else:
        return None, None  # No video to process, no account to switch to

def find_eligible_accounts(current_account, device_video_config):
    eligible_accounts = []
    for video_info in device_video_config['videos']:
        if video_info['account'] != current_account and not video_info['post_status']:
            eligible_accounts.append(video_info['account'])
    print(f"eligible_accounts:{eligible_accounts}")
    return eligible_accounts

def switch_account(driver, desired_account):
    try:
        # Click the 'Switch accounts' button
        switch_account_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ACCESSIBILITY_ID, "Switch accounts"))
        )
        switch_account_button.click()

        # Wait for the account selection popup
        time.sleep(5)
        screenshot_switch_base64 = driver.get_screenshot_as_base64()
        account_to_select = desired_account.lstrip('@')

        # Get OCR results from the screenshot
        ocr_results = text_recognition.process_image(screenshot_switch_base64, should_crop=False)
        account_name, coordinates = find_account_name_and_coordinates(ocr_results, account_to_select)
        
        if account_name is None:
            print(f"Account {account_to_select} not found in OCR results.")
            return False

        # Apply scaling factors
        scale_factor_width, scale_factor_height = calculate_scaling_factor_from_base64(driver, screenshot_switch_base64)
        scaled_x = coordinates['x'] * scale_factor_width
        scaled_y = coordinates['y'] * scale_factor_height
        scaled_width = coordinates['width'] * scale_factor_width
        scaled_height = coordinates['height'] * scale_factor_height
        
        # Calculate center of the bounding box
        center_x = int(scaled_x + scaled_width / 2)
        center_y = int(scaled_y + scaled_height / 2)

        # Select the desired account
        actions = ActionChains(driver)
        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(center_x, center_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.1)
        actions.pointer_action.release()
        actions.perform()

        print(f"Account '{account_to_select}' chosen successfully.")
        return True

    except TimeoutException:
        print("Timed out while trying to switch accounts.")
        return False
    except NoSuchElementException:
        print("Element not found during account switching.")
        return False
    except WebDriverException as e:
        print(f"WebDriver exception occurred: {e}")
        return False

def get_data_from_config(device_status_file_path, data_key):
    try:
        with open(device_status_file_path, 'r') as file:
            data = json.load(file)
            return data.get(data_key)
    except json.JSONDecodeError:
        raise Exception(f"Error decoding JSON from file: {device_status_file_path}")
    
def update_video_post_status(device_status_file_path, account):
    try:
        with open(device_status_file_path, 'r') as file:
            data = json.load(file)

        video_updated = False
        for video in data['videos']:
            if video['account'] == account:
                video['post_status'] = True
                video_updated = True
                video['timestamp'] = datetime.now().isoformat()
                break

        if not video_updated:
            print(f"No video found for account: {account}")
            return False

        with open(device_status_file_path, 'w') as file:
            json.dump(data, file, indent=4)
        return True
    except Exception as e:
        print(f"Error updating video post status: {e}")
        return False

def calculate_scaling_factor_from_base64(driver, image_base64):
    # Decode the base64 image to get the image data
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data))

    # Get the resolution of the decoded image (screenshot resolution)
    screenshot_width, screenshot_height = image.size
    print(screenshot_width, screenshot_height)

    # Get the viewport size from the driver
    viewport_size = driver.get_window_size()
    print(viewport_size)
    viewport_width = viewport_size['width']
    viewport_height = viewport_size['height']

    # Calculate scaling factors
    scale_factor_width = viewport_width / screenshot_width
    scale_factor_height = viewport_height / screenshot_height

    return scale_factor_width, scale_factor_height

def check_element_presence(driver, locator):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located(locator))
        return True
    except TimeoutException:
        return False
    
def wait_for_element_removal_custom(driver, locator, timeout=160):
    end_time = time.time() + timeout
    while True:
        try:
            driver.find_element(*locator)
            time.sleep(3)  # Wait for a short period before checking again
            if time.time() > end_time:
                return False  # Timeout reached, element is still present
        except NoSuchElementException:
            return True  # Element is no longer in the DOM

def select_tiktok_folder(driver):
    # Step 9: Select Folder
    time.sleep(5)
    process_page(driver, "Recents", "Select Folder")

    # Step 10: Folder list
    time.sleep(5)
    tiktok_folder_locator = (By.XPATH, "//XCUIElementTypeStaticText[@name='TikTok']")
    try:
        tiktok_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(tiktok_folder_locator))
        tiktok_button.click()
    except TimeoutException:
        # TikTok button not found, check for the popup
        handle_popup_and_retry(driver)

def handle_popup_and_retry(driver):
    introducing_text_locator = (By.IOS_CLASS_CHAIN, "**/XCUIElementTypeStaticText[`label == 'Introducing 10 minutes video'`]")
    ok_button_locator = (By.IOS_CLASS_CHAIN, "**/XCUIElementTypeButton[`label == 'OK'`]")

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(introducing_text_locator))
        ok_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(ok_button_locator))
        ok_button.click()
        select_tiktok_folder(driver)  # Retry folder selection after handling the popup
    except TimeoutException:
        raise Exception("Can't find TikTok folder or 'introducing popup'.")

# Test Sequence Manager Function

def run_test_sequences(driver, device_status_file_path):
    try:
        all_videos_posted = False

        while not all_videos_posted:
            # Running the test sequence for each account and video
            try:
                test_sequence(driver, device_status_file_path)
                print("test_sequence completed successfully.")
            except WebDriverException as e:
                print(f"WebDriverException occurred: {e}")
                break  # For example, break the loop on WebDriverException
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break 
    
            # Check if all videos are posted
            data = get_data_from_config(device_status_file_path, "videos")
            unposted_videos = [video for video in data if not video.get('post_status')]
            print(unposted_videos)
            all_videos_posted = not unposted_videos

            if not all_videos_posted:
                print("Not all videos posted yet. Running test sequence again.")
            else:
                print("All videos have been successfully posted.")

    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Run test sequences completed.")




# Test Sequence Wrapper Function

def test_sequence(driver, device_status_file_path):
    try:
        # Step 1: Open TikTok Profile page
        # Retrieve the current timeouts

        # Get current settings
        current_settings = driver.get_settings()
        print("Current Settings:", current_settings)

        if not process_page(driver, "Open TikTok Profile", "1st page"):
           raise Exception("Failed to open TikTok profile page.")
        

        # Step 2: Check current account
        time.sleep(5)
        screenshot_main_base64 = driver.get_screenshot_as_base64()
        current_account, coordinates = get_current_account(device_status_file_path, screenshot_main_base64)

        # Step 3: Get URL from config
        video_url, account, description = process_account_videos(driver, current_account, device_status_file_path)
        print(video_url, account, description)
        if not video_url:
           raise Exception(f"No videos found to process for account: {account}")
        

        # Step 4: Set a URL to the clipboard
        time.sleep(5)
        driver.execute_script('mobile: activateApp', {'bundleId': 'com.facebook.WebDriverAgentRunner.xctrunner'})
        set_clipboard_content(driver, video_url)

        # Step 5: Open Shortcuts to add video on device
        driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})
        if not process_page(driver, "Add Video", "Add Video"):
          raise Exception("Failed to start adding video on TikTok.")
        
        # Step 6: wait until video added
        time.sleep(2)
        more_button_locator = (By.XPATH, f"//XCUIElementTypeCell[contains(@name, 'Add Video')]//XCUIElementTypeButton[@name='More']")

        # Wait for the 'More' button to appear, which indicates the download is complete
        WebDriverWait(driver, 60).until(EC.presence_of_element_located(more_button_locator))
        
        # Now that the 'More' button is visible, you can interact with it or verify its state
        more_button = driver.find_element(*more_button_locator)
        if more_button.is_displayed():
            print("Download is complete, 'More' button is now visible.")
        else:
            print("Download might still be in progress, 'More' button is not yet visible.")
        
        # Step 7: Open TikTok to add video on device
        time.sleep(5)
        process_page(driver, "Tiktok Test", "Upload page")
        
        # Step 8: Uploader select
        time.sleep(5)
        process_page(driver, "recordPageUploadButton", "Second")
       
        # Step 9: Select Folder
        time.sleep(5)
        select_tiktok_folder(driver)

        # Step 10 Select video
        time.sleep(5)
        video_choice_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeCollectionView[`name == '(collectionView)'`]/XCUIElementTypeCell[1]")
        video_choice= WebDriverWait(driver, 30).until(EC.presence_of_element_located(video_choice_locator))
        video_choice.click()
        time.sleep(10)


        # Step 10 Video upload and add description
        time.sleep(5)
        next_button_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`label CONTAINS 'Next'`]")
        next_button = WebDriverWait(driver, 60).until(EC.presence_of_element_located(next_button_locator))
        next_button.click()
        # Past description
        time.sleep(5)
        text_description_area_locator = (By.ACCESSIBILITY_ID, f"Create more informative content when you go into greater detail with 4000 characters.")
        text_description_area = WebDriverWait(driver, 60).until(EC.presence_of_element_located(text_description_area_locator))
        text_description_area.send_keys(description)
        # Hide keyboard
        time.sleep(5)
        x, y = 183, 319
        touch_action = TouchAction(driver)
        touch_action.tap(x=x, y=y).perform()
        
        # Checkbox checking
        checkbox_notselected_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`value == 'not selected'`]")
        checkbox_selected_locator = (By.IOS_CLASS_CHAIN, f"**/XCUIElementTypeButton[`value == 'selected'`]")
        try:
            checkbox_selected = WebDriverWait(driver, 2).until(EC.presence_of_element_located(checkbox_selected_locator))
        except TimeoutException:
            checkbox_selected = None
        if not checkbox_selected:
            try:
                checkbox_notselected = WebDriverWait(driver, 2).until(EC.presence_of_element_located(checkbox_notselected_locator))
                if checkbox_notselected:
                    checkbox_notselected.click()
                    print("Not-selected checkbox found and clicked.")
            except TimeoutException:
                print("Not selected checkbox not found.")
        else:
            print("Selected checkbox is already present.")

        # Step 11 Video post

        account_forcheck = account.lstrip('@')
        video_count = tiktok_requests.get_video_count(account_forcheck)
        print(video_count)
        time.sleep(5)
        post_button_locator = (By.XPATH, f"//XCUIElementTypeButton[@name='Post']")
        post_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(post_button_locator))
        new_settings = {
            'waitForIdleTimeout': 0,
            'customSnapshotTimeout': 0,
            'animationCoolOffTimeout': 0
        }
        driver.update_settings(new_settings)
        post_button.click()
        new_settings = {
            'snapshotMaxDepth': 1
        }
        driver.update_settings(new_settings)
        
        # Step 12: Wait until the video uploaded
        print("Before timer", datetime.now().isoformat())
        time.sleep(10)    
        print("After timer", datetime.now().isoformat())
        max_retries = 5
        retry_count = 0
        current_timeout = 10

        while retry_count < max_retries:
            time.sleep(current_timeout)
            video_count_after_post = tiktok_requests.get_video_count(account_forcheck)
            if video_count_after_post > video_count:
                post_status = update_video_post_status(device_status_file_path, account)
                if post_status:
                    print("Status updated")
                else:
                    print("Status not changed")
                driver.execute_script('mobile: terminateApp', {'bundleId': 'com.zhiliaoapp.musically'})
                break
            else:
                retry_count += 1
                current_timeout += 20
        if retry_count >= max_retries and video_count_after_post == video_count:
            raise Exception("Video upload failed: the video count did not increase.")

        # Step 13: Back to default state and delete video from folder
        new_settings = {
            'waitForIdleTimeout': 10,
            'customSnapshotTimeout': 15,
            'animationCoolOffTimeout': 2,
            'snapshotMaxDepth': 50
        }
        driver.update_settings(new_settings)
        print("Reverted to Original Settings:", driver.get_settings())
        driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})
        time.sleep(5)
        process_page(driver, "Delete Video", "Last step")
        time.sleep(10)

    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise



