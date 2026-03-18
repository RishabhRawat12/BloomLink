import requests
import concurrent.futures
import time

# --- CHANGE THIS TO YOUR ACTUAL SHORT CODE ---
SHORT_CODE = "xU0jps" 
BASE_URL = "http://127.0.0.1:8080"

def hit_url():
    try:
        # allow_redirects=False so we only test the backend speed
        res = requests.get(f"{BASE_URL}/{SHORT_CODE}", allow_redirects=False)
        return res.status_code
    except Exception as e:
        return str(e)

print(f"🚀 Firing 30 requests at /{SHORT_CODE} simultaneously...")

start_time = time.time()

# Send 30 requests all at once using 10 parallel threads
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(lambda x: hit_url(), range(30)))

duration = time.time() - start_time
print(f"Finished in {duration:.2f} seconds.")
print(f"Status Codes returned: {set(results)}")
print("Check your Redis CLI to see the new replica keys!")