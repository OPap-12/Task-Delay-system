import concurrent.futures
import requests
import json
import uuid

BASE_URL = 'http://localhost:8000/api/v1'

def setup_test():
    # Attempt login to get JWT
    login_data = {
        'username': 'sarah_mgr',
        'password': 'Password123!'
    }
    r = requests.post(f"{BASE_URL}/token/", data=login_data)
    if r.status_code != 200:
        print("Failed to authenticate test. Ensure Server is running.")
        return None
    return r.json().get('access')

def patch_task(token, idempotency_key=None, is_idempotent_test=False):
    key = idempotency_key if idempotency_key else str(uuid.uuid4())
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Idempotency-Key': key
    }
    payload = {'action': 'approve'}
    
    # Target task 1 (usually created by seed_pg_data.py)
    r = requests.patch(f"{BASE_URL}/tasks/1/status/", headers=headers, json=payload)
    
    try:
        data = r.json()
    except Exception:
        data = re.search(r'<title>(.*?)</title>', r.text).group(1) if re.search(r'<title>(.*?)</title>', r.text) else getattr(r, 'text', r.status_code)
        
    return r.status_code, data

def run_concurrency_test(token, workers=20):
    print(f"--- Firing {workers} Concurrent Requests (Random Idempotency) ---")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(patch_task, token) for _ in range(workers)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    
    print("\n[Random Idempotent Load Results]")
    for code, resp in results[:5]:  print(f"Status: {code} | {resp}")
    print("...")

def run_idempotency_test(token, workers=10):
    fixed_key = 'fixed-key-123'
    print(f"\n--- Firing {workers} Concurrent Requests (FIXED Idempotency) ---")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(patch_task, token, fixed_key) for _ in range(workers)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
            
    print("\n[Fixed Idempotent Load Results]")
    for code, resp in results: print(f"Status: {code} | {resp}")

if __name__ == '__main__':
    token = setup_test()
    if token:
        run_concurrency_test(token, 20)
        run_idempotency_test(token, 10)
    else:
        print("Test Aborted.")
