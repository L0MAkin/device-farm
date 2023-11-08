from multiprocessing import Process
from appium_manager import main as appium_main_manager
from appium import webdriver
import my_test_script  # This will be the name of your modified test script file.

def run_tests_for_device(udid, appium_port, device_port, device_name):
    capabilities = {
        "platformName": "iOS",
        "deviceName": device_name,
        "udid": udid,
        "automationName": "XCUITest",
        "bundleId": "com.apple.shortcuts",
        "xcodeOrgId": "3GXHKFX93A",
        "xcodeSigningId": "Apple Development",
        "showXcodeLog": False,
        "appPushTimeout": "5000",
        "waitForQuiescence": True,
        "wda_local_port": device_port,
        "clearSystemFiles": True,
        "useNewWDA": True,
        "noReset": True
    }

    driver = webdriver.Remote(f'http://localhost:{appium_port}', capabilities)
    
    # You would transfer all of your existing test logic into a function like this one:
    my_test_script.test_sequence(driver)

    driver.quit()

if __name__ == '__main__':
    # Start the Appium servers and get the mappings
    udid_to_port_mapping, udid_to_device_port_mapping, appium_processes = appium_main_manager()

    # Create a list to keep track of the test processes for each device
    test_processes = []
    print(test_processes)

    # Start a test process for each device
    for udid, appium_port in udid_to_port_mapping.items():
        device_port = udid_to_device_port_mapping[udid] 
        if udid == "00008020-00144CA40288003A":
            device_name = "iPhoneXs"
        elif udid == "92ebd89ccf7dfe3b698c322678a9630ef9b95823":
            device_name = "iPhone"
        else:
            device_name = "Unknown Device" 
        print(device_name)
        # Get the device port for this UDID
        # Start the test in a separate process
        test_process = Process(target=run_tests_for_device, args=(udid, appium_port, device_port, device_name))
        test_processes.append(test_process)
        test_process.start()

    # Wait for all tests to complete
    for test_process in test_processes:
        test_process.join()

    # At this point, all the processes have completed
    # You could add code here to process any overall results or cleanup if necessary
