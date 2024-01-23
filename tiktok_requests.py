#TikTok_web_check
import requests
import time
import random
import os

def get_video_count(unique_id):
    api_url = f"https://www.tiktok.com/@{unique_id}?is_copy_url=1&is_from_webapp=v1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
    }

    max_retries = 4
    retries = 0
    html_content = ''

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
                save_html_content(html_content, unique_id, "error_status_code.html")
        except Exception as e:  # Catch any exception and print it
            print(f"Error occurred: {e}")
            save_html_content(html_content, unique_id, "error_status_code.html")

        # If we reach here, it means either the request failed, or conversion failed.
        retries += 1
        if retries < max_retries:
            sleep_time = random.randint(5, 20)
            print(f"Retrying in {sleep_time} seconds due to error...")
            time.sleep(sleep_time)

    print("Max retries reached, failed to retrieve data.")
    return None

def save_html_content(html_content, unique_id, filename_suffix):
    # Ensuring directory exists
    save_dir = "html_error_logs"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Saving the file
    file_path = os.path.join(save_dir, f"{unique_id}_{filename_suffix}")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"HTML content saved to {file_path}")


# Predefined profile ID for direct run
predefined_profile_id = "damnhackerdamn"

# Main function for direct run
def main():
    video_count = get_video_count(predefined_profile_id)
    if video_count is not None:
        print(f"Profile '{predefined_profile_id}' has {video_count} videos.")
    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    main()
