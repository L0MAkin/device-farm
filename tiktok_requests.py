#TikTok_web_check
import requests
import time
import random

def get_video_count(unique_id):
    api_url = f"https://www.tiktok.com/@{unique_id}?is_copy_url=1&is_from_webapp=v1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
    }

    max_retries = 4
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                html_content = response.text
                count_start = html_content.find('"videoCount":') + len('"videoCount":')
                count_end = html_content.find(',', count_start)
                video_count_str = html_content[count_start:count_end]

                video_count = int(video_count_str)  # Attempt to convert directly
                print(video_count)
                return video_count
            else:
                print(f"Error accessing profile: {unique_id} with status code {response.status_code}")
        except Exception as e:  # Catch any exception and print it
            print(f"Error occurred: {e}")

        # If we reach here, it means either the request failed, or conversion failed.
        retries += 1
        if retries < max_retries:
            sleep_time = random.randint(5, 20)
            print(f"Retrying in {sleep_time} seconds due to error...")
            time.sleep(sleep_time)

    print("Max retries reached, failed to retrieve data.")
    return None

# Predefined profile ID for direct run
predefined_profile_id = "dennythedon4"

# Main function for direct run
def main():
    video_count = get_video_count(predefined_profile_id)
    if video_count is not None:
        print(f"Profile '{predefined_profile_id}' has {video_count} videos.")
    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    main()
