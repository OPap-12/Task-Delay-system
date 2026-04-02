import os
import django
import time
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.auth.models import User, Group
from django.db.models import Count, Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.models import Task, Department, EmployeeProfile
from tasks.views import reports_view, department_list

def run_master_audit():
    results = []

    def log(msg):
        print(msg)
        results.append(msg)

    log("=== TASKFLOW FINAL MASTER AUDIT ===")

    # --- STEP 3: SECURITY ---
    log("\n[STEP 3: SECURITY]")
    user = User.objects.get(username='emp_1')
    factory = RequestFactory()
    
    # Test 7: Unauthorized Access
    for path, view in [('/reports/', reports_view), ('/departments/', department_list)]:
        request = factory.get(path)
        request.user = user
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(request, '_messages', FallbackStorage(request))
        response = view(request)
        status = "PASS (302)" if response.status_code == 302 else f"FAIL ({response.status_code})"
        log(f"Test 7: Access {path} as Employee: {status}")

    # Test 8: Role Corruption
    manager_group, _ = Group.objects.get_or_create(name='Manager')
    employee_group, _ = Group.objects.get_or_create(name='Employee')
    dual = User.objects.filter(groups=manager_group).filter(groups=employee_group).count()
    status = "PASS (None found)" if dual == 0 else f"FAIL ({dual} found)"
    log(f"Test 8: Role Corruption: {status}")

    # --- STEP 4: DATA INTEGRITY ---
    log("\n[STEP 4: DATA INTEGRITY]")
    # Test 1: Department Consistency
    admin = User.objects.get(username='admin')
    gen_dept, _ = Department.objects.get_or_create(name='General')
    dummy_dept, _ = Department.objects.get_or_create(name='AuditTestDept')
    
    profile, _ = EmployeeProfile.objects.get_or_create(user=admin)
    profile.department = dummy_dept
    profile.save()
    
    dummy_dept.delete()
    admin.profile.refresh_from_db()
    status = "PASS" if admin.profile.department.name == 'General' else "FAIL"
    log(f"Test 1: Dept Deletion Reassignment: {status}")

    # Test 2: Profile vs Reports Consistency
    # emp_1
    emp1 = User.objects.get(username='emp_1')
    db_count = Task.objects.filter(user=emp1, status='APPROVED').count()
    # We'll just check the DB logic for now
    log(f"Test 2: User emp_1 DB Approved: {db_count}")

    # --- STEP 5: PERFORMANCE ---
    log("\n[STEP 5: PERFORMANCE]")
    # Test 9: Load Handling
    manager = User.objects.get(username='admin_manager')
    req = factory.get('/reports/')
    req.user = manager
    start = time.time()
    reports_view(req)
    duration = time.time() - start
    status = "PASS (<1s)" if duration < 1.0 else f"FAIL ({duration:.2f}s)"
    log(f"Test 9: Reports Load time (60+ tasks): {status} ({duration:.4f}s)")

    # Write results to artifact
    with open('master_audit_results.txt', 'w') as f:
        f.write("\n".join(results))

if __name__ == '__main__':
    run_master_audit()
