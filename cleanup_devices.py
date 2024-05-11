#Cleanup_devices.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
from multiprocessing import Process
from time import sleep
from appium.options.ios import XCUITestOptions
from appium import webdriver
import common_actions


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
    options.no_reset = False
    options.use_new_wda = True
    options.set_capability("skipLogCapture", True)

    driver = webdriver.Remote(f'http://localhost:{appium_port}', options=options)

    driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})
    time.sleep(5)

    driver.execute_script('mobile: terminateApp', {'bundleId': 'com.apple.shortcuts'})
    
    driver.execute_script('mobile: activateApp', {'bundleId': 'com.apple.shortcuts'})
    delete_video_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ACCESSIBILITY_ID, "Delete Video"))
        )
    delete_video_button.click()
    
    time.sleep(5)
    driver.execute_script('mobile: terminateApp', {'bundleId': 'com.zhiliaoapp.musically'})

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

