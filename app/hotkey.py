import time
import random

HOT_KEY_THRESHOLD = 20
WINDOW_SECONDS = 10
REPLICA_COUNT = 3

# key -> [count, window_start]
access_counter = {}

def record_access(key: str):
    now = time.time()

    if key not in access_counter:
        access_counter[key] = [1, now]
        return

    count, start = access_counter[key]

    if now - start > WINDOW_SECONDS:
        access_counter[key] = [1, now]
    else:
        access_counter[key][0] += 1

    if access_counter[key][0] >= HOT_KEY_THRESHOLD:
        print("HOT KEY DETECTED:", key)

def is_hot_key(key: str) -> bool:
    return key in access_counter and access_counter[key][0] >= HOT_KEY_THRESHOLD

def replica_key(key: str) -> str:
    return f"{key}:replica:{random.randint(1, REPLICA_COUNT)}"