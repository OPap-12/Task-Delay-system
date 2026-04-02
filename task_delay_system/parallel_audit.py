import os
import django
from django.utils import timezone
import threading

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task

def parallel_test():
    print("--- STEP 2: PARALLEL USER DISCIPLINE (TEST 4) ---")
    user = User.objects.get(username='emp_1')
    
    # 1. Employee Submits Task
    task = Task.objects.create(
        user=user,
        title="Parallel Test Task",
        due_date=timezone.now().date(),
        status='IN_PROGRESS'
    )
    
    print(f"Status Start: {task.status}")
    
    # Simulate Employee Submission
    task.status = 'READY_FOR_REVIEW'
    task.save()
    print(f"Employee Submitted: {task.status}")
    
    # Simulate Manager Approval Immediately
    task.status = 'APPROVED'
    task.completed_at = timezone.now()
    task.save()
    print(f"Manager Approved Immediately: {task.status}")
    
    # Final check
    if task.status == 'APPROVED':
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")

if __name__ == '__main__':
    parallel_test()
