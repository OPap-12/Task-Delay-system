"""
Edge Case Test Suite — Live Render API
Tests: illegal FSM transitions, RBAC violations, missing data, rapid double-submit
"""
import requests, uuid, sys

BASE = 'https://task-delay-system.onrender.com/api/v1'
PASS, FAIL, INFO = "[PASS]", "[FAIL]", "[INFO]"
results = []

def log(label, ok, detail=''):
    msg = f"{PASS if ok else FAIL} {label}"
    if detail: msg += f" | {detail}"
    print(msg)
    results.append((label, ok))

def tok(user, pwd):
    r = requests.post(f"{BASE}/token/", json={"username": user, "password": pwd})
    return r.json().get('access') if r.status_code == 200 else None

def hdrs(t, idem=None):
    h = {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}
    if idem: h['Idempotency-Key'] = idem
    return h

def patch(t, task_id, action, reason='', idem=None):
    r = requests.patch(f"{BASE}/tasks/{task_id}/status/",
        headers=hdrs(t, idem or str(uuid.uuid4())),
        json={"action": action, "reason": reason})
    try: return r.status_code, r.json()
    except: return r.status_code, {}

# Auth
mgr = tok('sarah_mgr', 'Password123!') or tok('presentation_admin', 'Presentation123!')
emp = tok('john_emp', 'Password123!')
mike = tok('mike_emp', 'Password123!')
if not mgr or not emp:
    print("Auth failed. Run seed_pg_data.py first."); sys.exit(1)

# Get emp_id
emp_id = requests.get(f"{BASE}/profile/", headers=hdrs(emp)).json().get('id')

# Create a fresh task for edge case testing
r = requests.post(f"{BASE}/tasks/", headers=hdrs(mgr), json={
    "title": f"EdgeCase-{uuid.uuid4().hex[:6]}",
    "description": "Edge case test task",
    "deadline": "2026-06-01",
    "priority": "high",
    "assigned_to": emp_id,
})
assert r.status_code == 201, f"Task creation failed: {r.text}"
task_id = r.json()['id']
print(f"{INFO} Test task created: id={task_id}\n")

print("=== EDGE CASE 1: Approve already-approved task ===")
patch(emp, task_id, 'start')
patch(emp, task_id, 'submit')
patch(mgr, task_id, 'approve')
sc, data = patch(mgr, task_id, 'approve')
log("Double-approve blocked", sc == 400, data.get('error',''))

print("\n=== EDGE CASE 2: Employee tries manager actions ===")
sc, data = patch(emp, task_id, 'approve')
log("Employee approve blocked (403)", sc == 403, data.get('error',''))
sc, data = patch(emp, task_id, 'reject', 'bad faith')
log("Employee reject blocked (403)", sc == 403, data.get('error',''))

print("\n=== EDGE CASE 3: Manager tries employee actions on others task ===")
sc, data = patch(mgr, task_id, 'start')
log("Manager start blocked (403)", sc == 403, data.get('error',''))

print("\n=== EDGE CASE 4: Cross-employee task access ===")
sc, data = patch(mike, task_id, 'start')
log("Other employee start blocked (403/400)", sc in [400, 403], data.get('error',''))

print("\n=== EDGE CASE 5: Submit on APPROVED terminal state ===")
sc, data = patch(emp, task_id, 'submit')
log("Submit on APPROVED blocked (400)", sc in [400, 403], data.get('error',''))

print("\n=== EDGE CASE 6: Reject on APPROVED terminal state ===")
sc, data = patch(mgr, task_id, 'reject', 'late review')
log("Reject on APPROVED blocked (400)", sc == 400, data.get('error',''))

print("\n=== EDGE CASE 7: Invalid action name ===")
sc, data = patch(mgr, task_id, 'delete')
log("Invalid action rejected (400)", sc == 400, data.get('error',''))

print("\n=== EDGE CASE 8: Missing assignment — task with no assignee ===")
r2 = requests.post(f"{BASE}/tasks/", headers=hdrs(mgr), json={
    "title": "NoAssignee Task",
    "description": "Test",
    "deadline": "2026-06-01",
    "priority": "low",
})
try:
    r2_data = str(r2.json())[:80]
except Exception:
    r2_data = r2.text[:80]
log("Task without assignee blocked at creation (400)", r2.status_code == 400, r2_data)

print("\n=== EDGE CASE 9: Rapid double-submit idempotency ===")
# Create a new task in PENDING state
r3 = requests.post(f"{BASE}/tasks/", headers=hdrs(mgr), json={
    "title": f"Idem-{uuid.uuid4().hex[:6]}",
    "description": "Idempotency test",
    "deadline": "2026-06-01",
    "priority": "medium",
    "assigned_to": emp_id,
})
t2_id = r3.json().get('id')
patch(emp, t2_id, 'start')
patch(emp, t2_id, 'submit')

fixed_key = f"idem-test-{t2_id}"
sc1, d1 = patch(mgr, t2_id, 'approve', idem=fixed_key)
sc2, d2 = patch(mgr, t2_id, 'approve', idem=fixed_key)
log("First approve succeeds", sc1 == 200, str(d1))
log("Second same-key returns idempotent or 400", sc2 in [200, 400],
    f"note={d2.get('note','')} error={d2.get('error','')}")

print("\n" + "="*55)
passed = sum(1 for _, ok in results if ok)
print(f"EDGE CASES: {passed}/{len(results)} passed")
failed = [l for l, ok in results if not ok]
if failed: print(f"FAILURES: {failed}")
print("="*55)
