from multiprocessing import Process
from appium_manager import main as appium_main_manager
from appium.options.ios import XCUITestOptions
from appium import webdriver
import my_test_script  # This will be the name of your modified test script file.
import process_video_config
import appium_manager
import json



def all_required_devices_connected(mapped_devices, connected_devices):
    return all(device in connected_devices for device in mapped_devices)

def run_tests_for_device(udid, appium_port, device_port, device_name, device_status_file_path):
    options = XCUITestOptions()
    options.platform_name = "iOS"
    options.device_name = device_name  # Replace with your device name variable
    options.udid = udid  # Replace with your UDID variable
    options.automation_name = "XCUITest"
    options.bundle_id = "com.apple.shortcuts"
    options.xcode_org_id = "3GXHKFX93A"
    options.xcode_signing_id = "Apple Development"
    options.show_xcode_log = True
    options.set_capability("appPushTimeout", 5000)
    options.new_command_timeout = 2000
    options.wda_local_port = device_port  # Replace with your WDA local port variable
    options.clear_system_files = True
    options.auto_dismiss_alerts = True
    options.no_reset = True
    options.set_capability("skipLogCapture", True)

    driver = webdriver.Remote(f'http://localhost:{appium_port}', options=options)

    # You would transfer all of your existing test logic into a function like this one:
    my_test_script.run_test_sequences(driver, device_status_file_path)

    driver.quit()

if __name__ == '__main__':
    # Assuming video_config is already defined
    divice_status_config_state = process_video_config.run_config_manager()
    if divice_status_config_state:  
        print("New config created")
    else: 
        print("Use a previous data. No new files will be created.")

    status_files_directory = 'device_status_config'
    final_common_config = process_video_config.aggregate_device_statuses(status_files_directory)

    connected_devices = appium_manager.get_connected_udids()
    devices_to_test = [udid for udid, data in final_common_config.items() if any(not video['post_status'] for video in data['videos'])]
    print(devices_to_test)

    # Check if there are devices to test
    if not all(udid in connected_devices for udid in devices_to_test):
        print("Not all devices required for the video configuration are connected. Exiting...")
        exit(1)

    # Start the Appium servers for all connected devices
    udid_to_port_mapping, udid_to_device_port_mapping, appium_processes = appium_manager.main()

    # Filter out devices that are not needed for testing and terminate their Appium servers
    #print(udid_to_port_mapping)
    #print(devices_to_test)
    #print(appium_processes.items())
    for udid in list(udid_to_port_mapping):
        if udid not in devices_to_test:
            appium_processes[udid].terminate()  # Terminate the Appium server for this device
            del udid_to_port_mapping[udid]      # Remove from port mapping
            del udid_to_device_port_mapping[udid]  # Remove from device port mapping

    # Create a list to keep track of the test processes for each required device
    test_processes = []

    # Start a test process for each required and connected device
    for udid in devices_to_test:
        appium_port = udid_to_port_mapping.get(udid)
        device_port = udid_to_device_port_mapping.get(udid)
        device_name = final_common_config[udid]['device_name'] if udid in final_common_config else "Unknown Device"
        device_status_file_path = process_video_config.get_status_file_path(udid, status_files_directory)
        print (json.dumps(device_status_file_path, indent=4))

        test_process = Process(target=run_tests_for_device, args=(udid, appium_port, device_port, device_name, device_status_file_path))
        test_processes.append(test_process)
        test_process.start()

    # Wait for all tests to complete
    for test_process in test_processes:
        test_process.join()