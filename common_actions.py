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
import io
import elements_detector



# Base ports for Appium and WebDriverAgent
BASE_PORT = 4723
WDA_BASE_PORT = 9100


def get_connected_udids():
    result = subprocess.run(['idevice_id', '-l'], capture_output=True, text=True)
    udids = result.stdout.strip().split('\n')
    # Print detected UDIDs to the console
    if udids:
        print("Detected connected device UDIDs:")
        for udid in udids:
            print(udid)
    else:
        print("No connected devices detected.")
    return udids

def kill_process_on_port(port):
    # Find process using the port
    try:
        # This command finds the PID (process ID) using the specified port
        result = subprocess.run(['lsof', '-t', '-i', f':{port}'], capture_output=True, text=True)
        pid = result.stdout.strip()
        if pid:
            print(f"Killing process {pid} on port {port}.")
            subprocess.run(['kill', '-9', pid])
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

def start_appium_server(udid, appium_port, wda_port):
    kill_process_on_port(appium_port)
    appium_command = f"appium -p {appium_port} --use-driver=xcuitest --driver-xcuitest-webdriveragent-port {wda_port}"
    process = subprocess.Popen(appium_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Starting Appium server for device {udid} on port {appium_port}.")
    sleep(5)  # Wait a bit for the Appium server to start
    return process

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

def tap_elements(driver, *tap_coordinates):
    try:
        screenshot_base64 = driver.get_screenshot_as_base64()
        if tap_coordinates is None:
            print(f"element not found")
            return False
        else: 
            coordinates = tap_coordinates

        # Apply scaling factors
        scale_factor_width, scale_factor_height = calculate_scaling_factor_from_base64(driver, screenshot_base64)
        x_min = coordinates[0] * scale_factor_width
        y_min = coordinates[1] * scale_factor_height
        x_max = coordinates[2] * scale_factor_width
        y_max = coordinates[3] * scale_factor_height
        
        # Calculate center of the bounding box
        center_x = int(x_min + x_max) / 2
        center_y = int(y_min + y_max) / 2

        # Select the desired account
        actions = ActionChains(driver)
        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.pointer_action.move_to_location(center_x, center_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.1)
        actions.pointer_action.release()
        actions.perform()

        print(f"element chosen successfully.")
        return True
    
    except TimeoutException:
        print("Timed out while trying to select element")
        return False
    except NoSuchElementException:
        print("Element not found")
        return False
    except WebDriverException as e:
        print(f"WebDriver exception occurred: {e}")
        return False

def swipe (driver, *coords):
        actions = ActionBuilder(driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        # Begin the swipe action
        start_x, start_y, end_x, end_y = coords
        actions.pointer_action.move_to_location(start_x, start_y)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.1)  # Pause briefly to mimic human touch
        actions.pointer_action.move_to_location(end_x, end_y)
        actions.pointer_action.release()

        # Perform the swipe action
        actions.perform()

def preprocess_data(data):
    """
    Preprocess the data to keep only the instance with the highest confidence
    for each label that has multiple coordinates.
    """
    preprocessed_data = {}
    for label, items in data.items():
        if len(items) > 1:
            # If there are multiple instances, keep the one with the highest confidence
            highest_confidence_item = max(items, key=lambda x: x['confidence'])
            preprocessed_data[label] = [highest_confidence_item]
        else:
            # If there's only one instance, keep it as is
            preprocessed_data[label] = items
    return preprocessed_data


def get_coordinate(data, label_name):
    # Preprocess the data to keep the highest confidence entry for each label
    data = preprocess_data(data)
    
    # Check if the specified label exists in the preprocessed data
    if label_name in data:
        # Assuming there's at least one entry for the label and taking the first one
        label_data = data[label_name][0]  # Take the highest confidence entry
        coords = label_data['coordinates']
        
        # Extract coordinates into a list
        coordinates = [
            coords.get('x_min'),
            coords.get('y_min'),
            coords.get('x_max'),
            coords.get('y_max'),
        ]
        return coordinates
    else:
        print(f"Label '{label_name}' not found in data.")
        return None