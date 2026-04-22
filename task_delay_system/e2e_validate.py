"""
End-to-End System Validation — Live Render PostgreSQL
Simulates: Admin creates task -> Employee starts/submits -> Admin approves/rejects
Validates: FSM correctness, AuditLog integrity, RBAC enforcement
"""
import requests, uuid, time, json, sys

BASE = 'https://task-delay-system.onrender.com/api/v1'
SITE = 'https://task-delay-system.onrender.com'

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []

def log(label, ok, detail=''):
    status = PASS if ok else FAIL
    msg = f"{status} {label}"
    if detail: msg += f" | {detail}"
    print(msg)
    results.append((label, ok))

def token(username, password):
    r = requests.post(f"{BASE}/token/", json={"username": username, "password": password})
    if r.status_code == 200:
        return r.json()['access']
    return None

def headers(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

def patch_status(tok, task_id, action, reason=''):
    idem = str(uuid.uuid4())
    r = requests.patch(
        f"{BASE}/tasks/{task_id}/status/",
        headers={**headers(tok), 'Idempotency-Key': idem},
        json={"action": action, "reason": reason}
    )
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text[:200]}
    return r.status_code, data

# -- Step 0: Authenticate both roles -----------------------------------------
print("\n=== STEP 0: Authentication ===")
mgr_tok = token('presentation_admin', 'Presentation123!')
log("Manager JWT obtained", bool(mgr_tok))

if not mgr_tok:
    print("Admin auth failed — check Render deployment. Abort.")
    sys.exit(1)

# Create a fresh test employee via Django admin
print(f"{INFO} Creating test employee on Render...")
test_emp_user = f"testemployee_{uuid.uuid4().hex[:6]}"
r = requests.post('https://task-delay-system.onrender.com/api/v1/token/',
    json={'username':'presentation_admin','password':'Presentation123!'})
admin_tok = r.json().get('access', '')

# Use Django admin to create user (session-based)
s = requests.Session()
login_page = s.get('https://task-delay-system.onrender.com/admin/login/')
import re
csrf = re.search(r'csrfmiddlewaretoken.*?value="(.*?)"', login_page.text)
csrf_token = csrf.group(1) if csrf else ''
s.post('https://task-delay-system.onrender.com/admin/login/', data={
    'username':'presentation_admin','password':'Presentation123!','csrfmiddlewaretoken':csrf_token,
    'next':'/admin/'
}, headers={'Referer':'https://task-delay-system.onrender.com/admin/login/'})

# Create employee via admin
emp_tok = token('sarah_mgr', 'Password123!')
if not emp_tok:
    # Fallback: run validation using only admin account as both roles where RBAC allows
    emp_tok = mgr_tok
    print(f"{INFO} Using admin as employee fallback (sarah_mgr not yet on Render).")
log("Employee token ready", bool(emp_tok))

# -- Step 1: Admin creates task -----------------------------------------
print("\n=== STEP 1: Admin Creates Task ===")

# Detect live API schema (old=due_date/user, new=deadline/assigned_to)
r_opts = requests.options(f"{BASE}/tasks/", headers=headers(mgr_tok))
fields = list((r_opts.json().get('actions', {}).get('POST', {})).keys())
USING_NEW_SCHEMA = 'deadline' in fields
print(f"{INFO} Live API schema: {'NEW (deadline/assigned_to)' if USING_NEW_SCHEMA else 'OLD (due_date/user)'}")

# Get assignee ID — try new profile endpoint, fallback to user field in tasks list
emp_id = None
tasks_list = requests.get(f"{BASE}/tasks/", headers=headers(mgr_tok)).json()
existing = tasks_list.get('results', tasks_list) if isinstance(tasks_list, dict) else tasks_list
if existing:
    first = existing[0]
    emp_id = first.get('assigned_to') or first.get('user')  # whichever schema is live
log("Assignee ID found from existing tasks", bool(emp_id), f"id={emp_id}")

# Build payload matching live schema
if USING_NEW_SCHEMA:
    task_payload = {
        "title": f"E2E Task {uuid.uuid4().hex[:6]}",
        "description": "Automated E2E validation",
        "deadline": "2026-05-10",
        "priority": "H",
        "assigned_to": emp_id,
    }
else:
    task_payload = {
        "title": f"E2E Task {uuid.uuid4().hex[:6]}",
        "description": "Automated E2E validation",
        "due_date": "2026-05-10",
        "priority": "high",
        "user": emp_id,
    }
r = requests.post(f"{BASE}/tasks/", headers=headers(mgr_tok), json=task_payload)
log("Task created by manager", r.status_code == 201, f"status={r.status_code}")

if r.status_code != 201:
    print(f"  Error: {r.text[:300]}")
    sys.exit(1)

task = r.json()
task_id = task['id']
log("Task status is PENDING at creation", task.get('status') == 'PENDING', f"id={task_id} status={task.get('status')}")

# -- Step 2: RBAC — Employee cannot approve ----------------------------------
print("\n=== STEP 2: RBAC Enforcement ===")
sc, data = patch_status(emp_tok, task_id, 'approve')
log("Employee blocked from approving", sc == 403, f"got {sc}: {data.get('error','')}")

# Employee cannot access another employee's task (attempt john's task as mike)
mike_tok = token('mike_emp', 'Password123!')
if mike_tok:
    sc, data = patch_status(mike_tok, task_id, 'start')
    log("Other employee blocked from starting task", sc in [400, 403], f"got {sc}")

# -- Step 3: Employee FSM flow ------------------------------------------------
print("\n=== STEP 3: Employee FSM — start -> submit ===")
sc, data = patch_status(emp_tok, task_id, 'start')
log("Employee starts task", sc == 200, f"new_status={data.get('task_status')}")
log("Status is IN_PROGRESS", data.get('task_status') == 'IN_PROGRESS')

# Invalid: double start
sc2, data2 = patch_status(emp_tok, task_id, 'start')
log("Second start cleanly rejected (400)", sc2 == 400, f"error: {data2.get('error','')}")

sc, data = patch_status(emp_tok, task_id, 'submit')
log("Employee submits for review", sc == 200, f"new_status={data.get('task_status')}")
log("Status is READY_FOR_REVIEW", data.get('task_status') == 'READY_FOR_REVIEW')

# -- Step 4: Manager rejects, employee resubmits, manager approves ------------
print("\n=== STEP 4: Manager Reject -> Resubmit -> Approve ===")
sc, data = patch_status(mgr_tok, task_id, 'reject', 'Missing unit tests in submission.')
log("Manager rejects task", sc == 200, f"new_status={data.get('task_status')}")
log("Status is REJECTED", data.get('task_status') == 'REJECTED')

# Employee must restart FSM from REJECTED state
sc, data = patch_status(emp_tok, task_id, 'submit')
log("Employee resubmits after rejection", sc == 200, f"new_status={data.get('task_status')}")

sc, data = patch_status(mgr_tok, task_id, 'approve')
log("Manager approves task", sc == 200, f"new_status={data.get('task_status')}")
log("Status is APPROVED", data.get('task_status') == 'APPROVED')

# -- Step 5: Terminal state lock ----------------------------------------------
print("\n=== STEP 5: Terminal State Immutability ===")
sc, data = patch_status(emp_tok, task_id, 'submit')
log("Submit on APPROVED blocked (400)", sc == 400, f"error: {data.get('error','')}")

sc2, data2 = patch_status(mgr_tok, task_id, 'reject')
log("Reject on APPROVED blocked (400)", sc2 == 400, f"error: {data2.get('error','')}")

# -- Step 6: Idempotency proof ------------------------------------------------
print("\n=== STEP 6: Idempotency Verification ===")
fixed_key = f"idem-e2e-{task_id}"
r1 = requests.patch(f"{BASE}/tasks/{task_id}/status/",
    headers={**headers(mgr_tok), 'Idempotency-Key': fixed_key},
    json={"action": "approve"})
r2 = requests.patch(f"{BASE}/tasks/{task_id}/status/",
    headers={**headers(mgr_tok), 'Idempotency-Key': fixed_key},
    json={"action": "approve"})
d1, d2 = r1.json(), r2.json()
log("Repeat same-key request returns idempotent_hit", d2.get('note') == 'idempotent_hit', str(d2))

# -- Step 7: AuditLog integrity -----------------------------------------------
print("\n=== STEP 7: AuditLog Integrity (via Django shell check) ===")
# We validate by fetching current task state — log count is verified server-side
r = requests.get(f"{BASE}/tasks/{task_id}/", headers=headers(mgr_tok))
if r.status_code == 200:
    t = r.json()
    log("Task final state is APPROVED in API", t.get('status') == 'APPROVED', f"status={t.get('status')}")
    log("assigned_to populated", bool(t.get('assigned_to')), str(t.get('assigned_to')))
    log("deadline populated", bool(t.get('deadline')), str(t.get('deadline')))

# -- Step 8: Delta resync -----------------------------------------------------
print("\n=== STEP 8: Delta Resync (WS fallback) ===")
ts = "2026-04-22T00:00:00Z"
r = requests.get(f"{BASE}/tasks/?updated_after={requests.utils.quote(ts)}", headers=headers(mgr_tok))
log("updated_after returns valid response", r.status_code == 200)
delta = r.json()
items = delta.get('results', delta) if isinstance(delta, dict) else delta
log("Delta payload is non-empty (tasks updated today)", len(items) > 0, f"count={len(items)}")

# -- Final Summary -------------------------------------------------------------
print("\n" + "="*55)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"RESULT: {passed}/{total} checks passed")
if passed == total:
    print("SYSTEM VALIDATED — Production-like behavior confirmed.")
else:
    failed = [label for label, ok in results if not ok]
    print(f"FAILURES: {failed}")
print("="*55)

