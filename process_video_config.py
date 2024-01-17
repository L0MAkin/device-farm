# process_video_config.py
import sys
import json
from datetime import datetime
import os

def get_video_data_for_device(device_udid, video_config, device_mapping):
    if device_udid not in device_mapping:
        return {'videos': []}

    device_accounts = set(device_mapping[device_udid]['accounts'])
    filtered_videos = [video for video in video_config['videos'] if video['account'] in device_accounts]
    return {'videos': filtered_videos}

def load_device_mapping(file_path):
    try:
        with open(file_path, 'r') as file:
            device_data = json.load(file)
            if 'devices' in device_data:
                return {device['udid']: device for device in device_data['devices']}
            else:
                print("The JSON structure is not as expected.")
                return {}
    except FileNotFoundError:
        print(f"Device mapping file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return {}

def get_mapped_devices(video_config, device_mapping):
    accounts_in_video_config = {video_info['account'] for video_info in video_config['videos']}
    return [udid for udid, device in device_mapping.items() if accounts_in_video_config.intersection(set(device['accounts']))]

def load_config_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def process_video_config(config_str, default_config_path):
    if config_str:
        video_config = json.loads(config_str)
    else:
        video_config = load_config_from_file(default_config_path)
    return video_config

def get_video_config():
    # These values are obtained internally within the function
    config_str = sys.argv[1] if len(sys.argv) > 1 else ''
    default_config_path = sys.argv[2] if len(sys.argv) > 2 else 'default_video_config.json'
    return process_video_config(config_str, default_config_path)

def get_status_file_path(udid, status_files_directory):
    filename = f"status_{udid}.json"
    return os.path.join(status_files_directory, filename)

def read_existing_status_file(status_files_directory, udid):
    status_file_path = os.path.join(status_files_directory, f"status_{udid}.json")
    try:
        with open(status_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    
def aggregate_device_statuses(status_files_directory):
    aggregated_status = {}
    for file_name in os.listdir(status_files_directory):
        if file_name.startswith("status_") and file_name.endswith(".json"):
            udid = file_name[len("status_"):-len(".json")]  # Extract UDID from the filename
            status_file_path = os.path.join(status_files_directory, file_name)
            try:
                with open(status_file_path, 'r') as file:
                    status_data = json.load(file)
                    aggregated_status[udid] = status_data
            except FileNotFoundError:
                print(f"Status file not found: {status_file_path}")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {status_file_path}")
    return aggregated_status

def check_video_statuses (status_files_directory, specific_file_path=None):
    unposted_udids = set()

    def check_status_file(file_path):
        try:
            with open(file_path, 'r') as file:
                return [video for video in json.load(file).get('videos', []) if not video.get('post_status', True)]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    if specific_file_path:
        # Check only the specific file
        return check_status_file(specific_file_path)

    for file_name in os.listdir(status_files_directory):
        if file_name.startswith("status_") and file_name.endswith(".json"):
            udid = file_name[len("status_"):-len(".json")]
            status_file_path = os.path.join(status_files_directory, file_name)
            try:
                with open(status_file_path, 'r') as file:
                    status_data = json.load(file)
                    if any(not video.get('post_status', True) for video in status_data.get('videos', [])):
                        unposted_udids.add(udid)
            except FileNotFoundError:
                continue
            except json.JSONDecodeError:
                continue

    return unposted_udids if unposted_udids else None

def create_status_files_from_config(device_video_config, status_files_directory, udid):
    status_file_path = os.path.join(status_files_directory, f"status_{udid}.json")
    status_data = {
        "device_name": device_video_config.get("device_name", "Unknown Device"),
        "udid": udid,
        "videos": []
    }

    for video in device_video_config.get('videos', []):
        video['post_status'] = False
        video['timestamp'] = datetime.now().isoformat()
        status_data['videos'].append(video)

    with open(status_file_path, 'w') as file:
        json.dump(status_data, file, indent=4)

def run_config_manager():
    device_mapping = load_device_mapping("device_mapping_config.json")
    video_config = get_video_config()
    status_files_directory = 'device_status_config'
    os.makedirs(status_files_directory, exist_ok=True)
    devices_video_status = check_video_statuses(status_files_directory)
    if devices_video_status:
        print(f"Not all videos are posted in {devices_video_status}. No new files will be created.")
        return False
    for udid, device_info in device_mapping.items():
        print(device_mapping.items())
        device_video_config = get_video_data_for_device(udid, video_config, device_mapping)
        print(device_video_config)
        device_video_config["device_name"] = device_info.get("name", "Unknown Device")
        create_status_files_from_config(device_video_config, status_files_directory, udid)
    return True
    

if __name__ == "__main__":
    run_config_manager()

    
