# Appium_manager.py

import subprocess
from multiprocessing import Process
from time import sleep
import socket

BASE_DEVICE_PORT = 9100
BASE_PORT = 4723

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

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

def start_appium_on_port(port, device_port):
    if is_port_in_use(port):
        print(f"Appium is already running on port {port}.")
        return None
    cmd = f'appium -p {port} --use-driver=xcuitest --driver-xcuitest-webdriveragent-port {device_port}'
    process = subprocess.Popen(cmd, shell=True)
    print (f'appium -p {port} --use-driver=xcuitest --driver-xcuitest-webdriveragent-port {device_port}')
    sleep(5)  # Give Appium time to start
    return process

def main():
    udids = get_connected_udids()
    if not udids:
        print("No devices detected.")
        return

    udid_to_port_mapping = {}
    udid_to_device_port_mapping = {}
    appium_processes = {}

    for index, udid in enumerate(udids):
        port = BASE_PORT + index * 1  # Increment by 1 to avoid clashes with device ports
        device_port = BASE_DEVICE_PORT + index * 1

        udid_to_port_mapping[udid] = port
        udid_to_device_port_mapping[udid] = device_port

        print(f"Starting Appium for UDID {udid} on port {port}...")
        process = start_appium_on_port(port, device_port)
        if process:
            appium_processes[udid] = process
        print(f"Starting Appium for UDID {udid} webdriveragent-port {device_port}...")
    return udid_to_port_mapping, udid_to_device_port_mapping, appium_processes

if __name__ == "__main__":
    udid_to_port_mapping, udid_to_device_port_mapping, appium_processes = main()

    print("\nUDID to Appium Port Mapping:")
    for udid, port in udid_to_port_mapping.items():
        print(f"{udid} -> {port}")

    print("\nUDID to Device Port Mapping:")
    for udid, device_port in udid_to_device_port_mapping.items():
        print(f"{udid} -> {device_port}")

    print("\nAppium instances are running. Press Enter to shut them down when done.")
    input()  # Wait for user input

    # Shutdown Appium instances
    for port, process in appium_processes.items():
        process.terminate()  # This will send a SIGTERM, then a SIGKILL if the process doesn't exit
        process.wait()  # Wait for the process to terminate

    print("\nAppium servers have been shut down.")
