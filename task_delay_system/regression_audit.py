import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task

def regression_audit():
    print("--- STEP 6: FULL REGRESSION TEST ---")
    user = User.objects.get(username='emp_1')
    
    # 1. Create
    task = Task.objects.create(
        user=user,
        title="Regression Audit Task",
        due_date=timezone.now().date(),
        priority='high'
    )
    print(f"1. Created Status: {task.status}")
    
    # 2. Start
    task.status = 'IN_PROGRESS'
    task.save()
    print(f"2. Started Status: {task.status}")
    
    # 3. Submit
    task.status = 'READY_FOR_REVIEW'
    task.save()
    print(f"3. Submitted Status: {task.status}")
    
    # 4. Reject
    task.status = 'REJECTED'
    task.rejected_reason = "Final Audit Rejection"
    task.save()
    print(f"4. Rejected Status: {task.status}")
    
    # 5. Rework & Resubmit
    task.status = 'READY_FOR_REVIEW'
    task.save()
    print(f"5. Resubmitted Status: {task.status}")
    
    # 6. Approve
    task.status = 'APPROVED'
    task.completed_at = timezone.now()
    task.save()
    print(f"6. Final Approved Status: {task.status}")
    
    # Verification
    if task.status == 'APPROVED' and task.completed_at:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")

if __name__ == '__main__':
    regression_audit()
