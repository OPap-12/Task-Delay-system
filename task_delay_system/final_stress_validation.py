import concurrent.futures
import requests
import json
import uuid
import time
from datetime import datetime

BASE_URL = 'http://localhost:8000/api/v1'

def setup_test():
    login_data = {'username': 'sarah_mgr', 'password': 'Password123!'}
    try:
        r = requests.post(f"{BASE_URL}/token/", data=login_data)
        if r.status_code == 200:
            return r.json().get('access')
    except: pass
    return None

def patch_status(token, task_id, key=None):
    idem_key = key if key else str(uuid.uuid4())
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Key': idem_key
    }
    start = time.time()
    r = requests.patch(f"{BASE_URL}/tasks/{task_id}/status/", headers=headers, json={'action': 'approve'})
    try:
        data = r.json()
    except:
        data = {"error": "500 Internal Error / Missing Task"}
    
    return r.status_code, data, time.time() - start

def execute_validation():
    token = setup_test()
    if not token:
        print("Server not accessible. Start `python manage.py runserver`.")
        return

    print("--- 1. IDEMPOTENCY UNDER RACE (Same Key) ---")
    fixed_key = str(uuid.uuid4())
    results_idem = []
    # Using Task 5 (Arbitrary FSM target assuming seed_pg_data.py built 1-10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(patch_status, token, 8, fixed_key) for _ in range(50)]
        for f in concurrent.futures.as_completed(futures):
            results_idem.append(f.result())
            
    successes = [r for r in results_idem if r[0] == 200 and r[1].get('task_status') == 'APPROVED']
    hits = [r for r in results_idem if r[0] == 200 and r[1].get('note') == 'idempotent_hit']
    errors = [r for r in results_idem if r[0] != 200]
    print(f"Executions: {len(successes)} | Idempotent Hits: {len(hits)} | Errors: {len(errors)}")

    print("\n--- 2. LOCK CONTENTION / BYPASS INCURSION (Unique Keys) ---")
    results_race = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(patch_status, token, 9) for _ in range(50)]
        for f in concurrent.futures.as_completed(futures):
            results_race.append(f.result())
            
    r_succ = [r for r in results_race if r[0] == 200]
    r_fail = [r for r in results_race if r[0] == 400]
    r_500 = [r for r in results_race if r[0] == 500]
    latency = [r[2] for r in results_race]
    avg_lat = sum(latency)/len(latency) if latency else 0
    print(f"Total Unique Transitions: {len(r_succ)} | Controlled Rejections (400): {len(r_fail)}")
    print(f"Server Crashes (500): {len(r_500)} | Avg Latency: {avg_lat*1000:.0f}ms")

    print("\n--- 3. DELTA RESYNC CORRECTNESS ---")
    curr_time = datetime.utcnow().isoformat() + "Z"
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f"{BASE_URL}/tasks/?updated_after={curr_time}", headers=headers)
    print(f"Delta payload elements received: {len(r.json().get('results', r.json()))}")

if __name__ == '__main__':
    execute_validation()
