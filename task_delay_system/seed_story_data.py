import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from tasks.models import Task, Department, EmployeeProfile, ROLE_MANAGER, ROLE_EMPLOYEE

def clear_db():
    print("Clearing database...")
    Task.objects.all().delete()
    User.objects.all().delete()
    Group.objects.all().delete()
    Department.objects.all().delete()

def seed_story():
    # 1. Create Roles
    manager_group, _ = Group.objects.get_or_create(name=ROLE_MANAGER)
    employee_group, _ = Group.objects.get_or_create(name=ROLE_EMPLOYEE)

    # 2. Create Departments
    eng = Department.objects.create(name='Engineering', description='Software and infrastructure')
    ops = Department.objects.create(name='Operations', description='Business operations and logistics')
    hr = Department.objects.create(name='Human Resources', description='People and culture')

    # 3. Create Manager
    manager = User.objects.create_user(username='sarah_manager', password='StrongPassword#2026!', email='sarah@taskflow.com', first_name='Sarah')
    manager.groups.add(manager_group)
    print("Created Manager: sarah_manager")

    # 4. Create Story-based Employees
    # Employee 1: High performer
    emp_high = User.objects.create_user(username='alex_high', password='StrongPassword#2026!', first_name='Alex')
    emp_high.groups.add(employee_group)
    EmployeeProfile.objects.get_or_create(user=emp_high, department=eng)

    # Employee 2: Needs improvement
    emp_low = User.objects.create_user(username='bob_low', password='StrongPassword#2026!', first_name='Bob')
    emp_low.groups.add(employee_group)
    EmployeeProfile.objects.get_or_create(user=emp_low, department=ops)

    # Employee 3: New employee
    emp_new = User.objects.create_user(username='charlie_new', password='StrongPassword#2026!', first_name='Charlie')
    emp_new.groups.add(employee_group)
    EmployeeProfile.objects.get_or_create(user=emp_new, department=hr)

    today = timezone.now().date()

    # 5. Create Tasks for High Performer (Alex)
    # Most tasks approved, some in progress
    Task.objects.create(user=emp_high, title='Optimize Database Queries', description='Refactor slow SQL queries in the analytics module.', status='APPROVED', priority='H', deadline=today - timedelta(days=2), completed_at=timezone.now(), approved_by=manager)
    Task.objects.create(user=emp_high, title='Update API Documentation', description='Ensure all new endpoints are documented in Swagger.', status='APPROVED', priority='M', deadline=today - timedelta(days=5), completed_at=timezone.now(), approved_by=manager)
    Task.objects.create(user=emp_high, title='Fix Login Performance', description='Users reporting slow login on mobile.', status='IN_PROGRESS', priority='H', deadline=today + timedelta(days=3))
    Task.objects.create(user=emp_high, title='Security Audit Preparations', status='PENDING', priority='M', deadline=today + timedelta(days=4))

    # 6. Create Tasks for Underperformer (Bob)
    # Many rejections, overdue tasks
    t1 = Task.objects.create(user=emp_low, title='Monthly Sales Report', description='Generate report for March.', status='REJECTED', priority='H', deadline=today - timedelta(days=1))
    t1.rejected_reason = "Data is missing for the last week. Please re-run the export."
    t1.save()

    t2 = Task.objects.create(user=emp_low, title='Fleet Maintenance Log', description='Update logs for delivery trucks.', status='REJECTED', priority='M', deadline=today - timedelta(days=3))
    t2.rejected_reason = "Improper formatting. Use the new template."
    t2.save()

    Task.objects.create(user=emp_low, title='Quarterly Inventory Sync', status='IN_PROGRESS', priority='H', deadline=today - timedelta(days=5)) # EXTENSIONS/OVERDUE
    Task.objects.create(user=emp_low, title='Supplier Contract Review', status='PENDING', priority='M', deadline=today - timedelta(days=10)) # VERY OVERDUE

    # 7. Create Tasks for New Employee (Charlie)
    Task.objects.create(user=emp_new, title='Onboarding Module 1', status='APPROVED', priority='L', deadline=today, completed_at=timezone.now(), approved_by=manager)
    Task.objects.create(user=emp_new, title='Setup Local Environment', status='IN_PROGRESS', priority='M', deadline=today + timedelta(days=1))

    print("Story-based seeding completed.")

if __name__ == "__main__":
    clear_db()
    seed_story()
