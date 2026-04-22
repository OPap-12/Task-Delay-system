import os
import django
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from tasks.models import Task, AuditLog, ROLE_EMPLOYEE, ROLE_MANAGER
from tasks.services.task_service import TaskService

@transaction.atomic
def seed_database():
    print("--- INITIATING TARGETED REFRESH ---")
    
    # 1. Targeted Safety Reset (Dependent objects first)
    AuditLog.objects.all().delete()
    Task.objects.all().delete()
    User.objects.filter(username__in=['sarah_mgr','john_emp','mike_emp', 'alice_emp']).delete()
    print("Cleaned legacy seed data & task traces.\n")

    # 2. Roles Verification
    emp_group, _ = Group.objects.get_or_create(name=ROLE_EMPLOYEE)
    mgr_group, _ = Group.objects.get_or_create(name=ROLE_MANAGER)

    # Demo only passwords
    manager = User.objects.create_user(username='sarah_mgr', password='Password123!', email='sarah@test.com', first_name='Sarah')
    manager.groups.add(mgr_group)

    emp1 = User.objects.create_user(username='john_emp', password='Password123!', email='john@test.com', first_name='John')
    emp1.groups.add(emp_group)

    emp2 = User.objects.create_user(username='mike_emp', password='Password123!', email='mike@test.com', first_name='Mike')
    emp2.groups.add(emp_group)
    
    emp3 = User.objects.create_user(username='alice_emp', password='Password123!', email='alice@test.com', first_name='Alice')
    emp3.groups.add(emp_group)

    print("Users ('sarah_mgr', 'john_emp', 'mike_emp', 'alice_emp') mapped.\n")

    today = timezone.now().date()
    employees = [emp1, emp2, emp3]
    
    # 3. High Volume FSM Simulation (10+ Tasks)
    tasks_data = [
        ("Deploy PostgreSQL Cluster", 2, 'H', emp1, 'approve'),
        ("Fix Legacy Audit Stringification", -3, 'M', emp2, 'reject'),
        ("Implement Rate Limiting", 1, 'L', emp1, 'start'),
        ("Update Dashboard React UI", 5, 'M', emp3, 'submit'),
        ("Patch Critical Nginx Config", -1, 'H', emp1, 'approve'),
        ("Review Compliance Audits", 14, 'M', emp2, 'pending'),
        ("Configure Redux Store", 3, 'L', emp3, 'start'),
        ("Deploy RabbitMQ Workers", -2, 'H', emp1, 'reject'),
        ("Write Unit Test Coverage", 4, 'M', emp2, 'submit'),
        ("Resolve OAuth Deadlock", 0, 'H', emp3, 'approve'),
    ]

    for title, days_offset, priority, assignee, outcome in tasks_data:
        try:
            t = Task.objects.create(
                title=title,
                description=f"Generated scenario matching '{outcome}' outcome path.",
                deadline=today + timedelta(days=days_offset),
                priority=priority,
                assigned_to=assignee,
                created_by=manager
            )
            
            # 4. Explicit Independent FSM Branches
            if outcome == 'pending':
                pass # Initial state
            elif outcome == 'start':
                TaskService.start_task(t.id, assignee)
            elif outcome == 'submit':
                TaskService.start_task(t.id, assignee)
                TaskService.submit_for_review(t.id, assignee)
            elif outcome == 'approve':
                TaskService.start_task(t.id, assignee)
                TaskService.submit_for_review(t.id, assignee)
                TaskService.approve_task(t.id, manager)
            elif outcome == 'reject':
                TaskService.start_task(t.id, assignee)
                TaskService.submit_for_review(t.id, assignee)
                TaskService.reject_task(t.id, manager, f"Failed automated review check UX-{random.randint(100,999)}.")
                
            print(f"Executed: '{t.title}' [Path: {outcome.upper()}]")
            
        except Exception as e:
            print(f"FAILED [{title}]: {str(e)}")

    print(f"\n--- SEEDING COMPLETE ---")
    print(f"Total Tasks: {Task.objects.count()}")
    print(f"Total Audit Logs Captured: {AuditLog.objects.count()}\n")

    # 5. Native Structure Asserts
    print("--- POST-EXECUTION METRICS & VALIDATION ---")
    for t in Task.objects.all():
        assert t.assigned_to is not None, f"Orphaned task detected: {t.id}"
        assert t.deadline is not None, f"Task missing deadline: {t.id}"
        
    print(f"System Integrity Check: PASSED")
    print(f"APPROVED Volume: {Task.objects.filter(status='APPROVED').count()}")
    print(f"REJECTED Volume: {Task.objects.filter(status='REJECTED').count()}")
    print(f"PENDING/IN_PROGRESS Volume: {Task.objects.filter(status__in=['PENDING', 'IN_PROGRESS']).count()}")

if __name__ == "__main__":
    seed_database()
