import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task

def rapid_action_audit():
    print("--- STEP 2: WORKFLOW STABILITY (TEST 3) ---")
    user = User.objects.get(username='emp_1')
    manager = User.objects.get(username='admin_manager')
    
    # 1. Create Task
    task = Task.objects.create(
        user=user,
        title="Rapid Audit Task",
        description="Audit",
        deadline=timezone.now().date(),
        priority='medium'
    )
    print(f"Created: {task.status}") # Should be PENDING
    
    # 2. Start
    task.status = 'IN_PROGRESS'
    task.save()
    print(f"Started: {task.status}")
    
    # 3. Submit
    task.status = 'READY_FOR_REVIEW'
    task.save()
    print(f"Submitted: {task.status}")
    
    # 4. Reject
    task.status = 'REJECTED'
    task.rejected_reason = "Rapid rejection"
    task.save()
    print(f"Rejected: {task.status}")
    
    # 5. Rework & Resubmit
    task.status = 'READY_FOR_REVIEW'
    task.save()
    print(f"Resubmitted: {task.status}")
    
    # 6. Approve
    task.status = 'APPROVED'
    task.completed_at = timezone.now()
    task.save()
    print(f"Approved: {task.status}")
    
    # Verify final state
    if task.status == 'APPROVED' and task.completed_at:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")

if __name__ == '__main__':
    rapid_action_audit()
