import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Department, EmployeeProfile, get_default_department

def test_1():
    print("Running Test 1: Department Consistency")
    admin = User.objects.get(username='admin')
    gen_dept, _ = Department.objects.get_or_create(name='General')
    eng_dept, _ = Department.objects.get_or_create(name='Engineering')
    
    profile, _ = EmployeeProfile.objects.get_or_create(user=admin)
    profile.department = eng_dept
    profile.save()
    
    print(f"Initial: {admin.profile.department.name}")
    
    # Delete engineering
    eng_dept.delete()
    
    # Refresh profile
    admin.profile.refresh_from_db()
    
    print(f"Final (should be General): {admin.profile.department.name}")
    
    if admin.profile.department.name == 'General':
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")

if __name__ == '__main__':
    test_1()
