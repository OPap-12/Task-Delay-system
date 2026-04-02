import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import User, Group

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.views import reports_view, department_list

def security_audit():
    print("--- STEP 3: SECURITY AUDIT (TEST 7 & 8) ---")
    
    # Test 7: Unauthorized Access
    user = User.objects.get(username='emp_1') # Standard Employee
    factory = RequestFactory()
    
    routes = [
        ('/reports/', reports_view),
        ('/departments/', department_list)
    ]
    
    for path, view in routes:
        print(f"Testing route: {path}")
        request = factory.get(path)
        request.user = user
        # Add messages middleware mock if needed, but the view decorators / logic will trigger first
        try:
            from django.contrib.messages.storage.fallback import FallbackStorage
            setattr(request, '_messages', FallbackStorage(request))
            
            response = view(request)
            if response.status_code == 302:
                print(f"Result for {path}: PASS (302 Redirect)")
            else:
                print(f"Result for {path}: FAIL (Code {response.status_code})")
        except Exception as e:
            print(f"Error testing {path}: {e}")

    # Test 8: Role Corruption
    print("\nTest 8: Role Corruption (Mutual Exclusivity)")
    manager_group = Group.objects.get(name='Manager')
    employee_group = Group.objects.get(name='Employee')
    
    dual_role_users = User.objects.filter(groups=manager_group).filter(groups=employee_group)
    if dual_role_users.exists():
        print(f"FAIL: Dual-role users found: {[u.username for u in dual_role_users]}")
    else:
        print("PASS: No dual-role users found.")

if __name__ == '__main__':
    security_audit()
