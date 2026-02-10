import requests
import threading
import time

SHORT_CODE = "w4moPr4"  
BASE_URL = "http://127.0.0.1:8000"

REQUESTS_PER_THREAD = 50
THREAD_COUNT = 5

def hit_url():
    for _ in range(REQUESTS_PER_THREAD):
        try:
            requests.get(f"{BASE_URL}/{SHORT_CODE}")
        except Exception:
            pass

threads = []

start = time.time()

for _ in range(THREAD_COUNT):
    t = threading.Thread(target=hit_url)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

end = time.time()

print(f"Sent {REQUESTS_PER_THREAD * THREAD_COUNT} requests in {end - start:.2f} seconds")
