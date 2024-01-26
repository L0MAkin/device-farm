from contextlib import asynccontextmanager
from fastapi import FastAPI
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS
import time
import requests
import random
import pprint


gateway = ApiGateway("https://www.tiktok.com")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start API 
    gateway.start(force=True)
    pprint.pprint(gateway.endpoints)
    yield
    # Finish API
    gateway.shutdown()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.get("/get_video_count")
def get_video_count_logic(unique_id: str):
    api_url = f"https://www.tiktok.com/@{unique_id}?is_copy_url=1&is_from_webapp=v1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
    }

    # Assign gateway to session
    session = requests.Session()
    session.mount("https://www.tiktok.com", gateway)

    max_retries = 4
    retries = 0

    while retries < max_retries:
        try:
            response = session.get(api_url, headers=headers)
            if response.status_code == 200:
                html_content = response.text
                count_start = html_content.find('"videoCount":') + len('"videoCount":')
                count_end = html_content.find(',', count_start)
                video_count_str = html_content[count_start:count_end]
                video_count = int(video_count_str)
                return video_count
            else:
                print(f"Error accessing profile: {unique_id} with status code {response.status_code}")
        except Exception as e:
            print(f"Error occurred: {e}")
        retries += 1
        if retries < max_retries:
            sleep_time = random.randint(5, 20)
            time.sleep(sleep_time)

    print("Max retries reached, failed to retrieve data.")
    return None