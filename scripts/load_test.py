import asyncio
import aiohttp
import time

SHORT_CODE = "example123"  # Replace with a real code from your DB
BASE_URL = "http://127.0.0.1:8000"

TOTAL_REQUESTS = 5000
CONCURRENCY = 200  # Number of parallel connections

async def fetch(session, url):
    try:
        # Allow redirects to resolve so we know the system works end-to-end
        async with session.get(url, allow_redirects=False) as response:
            return response.status
    except Exception:
        return 0

async def bound_fetch(sem, session, url):
    # Use a semaphore to cap maximum concurrency and avoid socket exhaustion
    async with sem:
        return await fetch(session, url)

async def main():
    print(f"Starting Load Test: {TOTAL_REQUESTS} requests at {CONCURRENCY} concurrency...")
    url = f"{BASE_URL}/{SHORT_CODE}"
    
    sem = asyncio.Semaphore(CONCURRENCY)
    
    # We use a single TCPConnector session to pool connections (just like a real load balancer)
    async with aiohttp.ClientSession() as session:
        tasks = [bound_fetch(sem, session, url) for _ in range(TOTAL_REQUESTS)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

    successes = sum(1 for status in results if status in [200, 301, 302, 307])
    failures = TOTAL_REQUESTS - successes
    duration = end_time - start_time
    tps = TOTAL_REQUESTS / duration

    print("\n--- Load Test Results ---")
    print(f"Total Time: {duration:.2f} seconds")
    print(f"Throughput: {tps:.2f} Requests/Second")
    print(f"Successes:  {successes}")
    print(f"Failures:   {failures}")

if __name__ == "__main__":
    asyncio.run(main())