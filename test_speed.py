import json
import statistics
import time
import urllib.request

URL = "http://127.0.0.1:8000/score"

normal = {"amount": 500, "hour": 14, "receiver_age_days": 800,
          "is_collect_request": 0, "txns_last_10min": 0,
          "new_device": 0, "distance_from_home": 3}

scam = {"amount": 25000, "hour": 3, "receiver_age_days": 1,
        "is_collect_request": 1, "txns_last_10min": 6,
        "new_device": 1, "distance_from_home": 300}


def send(payment):
    data = json.dumps(payment).encode()
    req = urllib.request.Request(
        URL, data=data, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    return (time.time() - start) * 1000, result["decision"]


times = []
decisions = {"allow": 0, "review": 0, "block": 0}

for i in range(200):
    payment = scam if i % 10 == 0 else normal
    ms, decision = send(payment)
    times.append(ms)
    decisions[decision] += 1

times.sort()
print("----- SPEED TEST: 200 payments -----")
print("Average speed:", round(statistics.mean(times), 1), "ms")
print("Median (p50):", round(times[99], 1), "ms")
print("Slow end (p95):", round(times[189], 1), "ms")
print("Slowest:", round(times[-1], 1), "ms")
print()
print("Guard decisions:", decisions)