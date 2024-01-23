#clipboard_test.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
from multiprocessing import Process
import subprocess
import socket
from time import sleep
from appium.options.ios import XCUITestOptions
from appium import webdriver

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

    def set_clipboard_content(driver, content):
        try:
            print (f"URL{content}")
            byte_data = content.encode('UTF-8')
            print (f"encoded_data = {byte_data}")
            driver.set_clipboard(content=byte_data, content_type='URL')
            print("Clipboard content set successfully.")
        except Exception as e:
            print(f"Error setting clipboard content: {e}")
    video_url = "https://drive.google.com/uc?export=download&id=1j1KibCOwBSaeuWQYdgGmB4cG2l8-4grb"
    time.sleep(5)
    driver.execute_script('mobile: activateApp', {'bundleId': 'com.facebook.WebDriverAgentRunner.xctrunner'})
    set_clipboard_content(driver, video_url)

    # Step 5: Open Shortcuts to add video on device
    time.sleep(2)
    driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})
    add_video_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ACCESSIBILITY_ID, "Add Video"))
        )
    add_video_button.click()
        
    # Step 6: wait until video added
    time.sleep(5)
    more_button_locator = (By.XPATH, f"//XCUIElementTypeCell[contains(@name, 'Add Video')]//XCUIElementTypeButton[@name='More']")

    # Wait for the 'More' button to appear, which indicates the download is complete
    WebDriverWait(driver, 60).until(EC.presence_of_element_located(more_button_locator))
        
    # Now that the 'More' button is visible, you can interact with it or verify its state
    more_button = driver.find_element(*more_button_locator)
    if more_button.is_displayed():
        print("Download is complete, 'More' button is now visible.")
    else:
        print("Download might still be in progress, 'More' button is not yet visible.")

    driver.quit()
    

def main():
    udids = get_connected_udids()
    appium_processes = {}
    processes = []

    for index, udid in enumerate(udids):
        device_name = f"iPhone({index+1})"
        appium_port = BASE_PORT + index * 1  # Increment by 1 to avoid port conflicts
        wda_port = WDA_BASE_PORT + index * 1
        
        appium_process = start_appium_server(udid, appium_port, wda_port)
        appium_processes.append(appium_process)

        process = Process(target=run_tests_on_device, args=(udid, appium_port, wda_port, device_name))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

if __name__ == '__main__':
    main()
