import os
import django
import random
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User, Group
from tasks.models import Task, Department, EmployeeProfile, ROLE_EMPLOYEE

def run_stress_seed():
    # 1. Ensure 3 Departments
    depts = ['Engineering', 'Marketing', 'Sales']
    dept_objs = []
    for dname in depts:
        obj, _ = Department.objects.get_or_create(name=dname)
        dept_objs.append(obj)

    # 2. Ensure 5 Employees
    emp_group, _ = Group.objects.get_or_create(name=ROLE_EMPLOYEE)
    employees = []
    for i in range(1, 6):
        username = f'emp_{i}'
        user, created = User.objects.get_or_create(username=username, defaults={'is_staff': False})
        if created:
            user.set_password('AdminPassword123!')
            user.save()
            user.groups.add(emp_group)
        
        # Assign to random dept
        profile, _ = EmployeeProfile.objects.get_or_create(user=user)
        profile.department = random.choice(dept_objs)
        profile.save()
        employees.append(user)

    # 3. Create 50+ Tasks
    statuses = ['PENDING', 'IN_PROGRESS', 'READY_FOR_REVIEW', 'APPROVED', 'REJECTED']
    priorities = ['low', 'medium', 'high']
    
    for i in range(60):
        user = random.choice(employees)
        status = random.choice(statuses)
        priority = random.choice(priorities)
        due_date = timezone.now().date() + timedelta(days=random.randint(-10, 10))
        
        task = Task.objects.create(
            user=user,
            title=f'Stress Task {i}',
            description=f'Seed description {i}',
            due_date=due_date,
            status=status,
            priority=priority
        )
        
        if status == 'REJECTED':
            task.rejected_reason = "Stress test rejection"
            task.save()
        elif status == 'APPROVED':
            task.completed_at = timezone.now()
            task.save()

    print(f"Stress test seed complete. Total users: {User.objects.count()}, Total tasks: {Task.objects.count()}")

if __name__ == '__main__':
    run_stress_seed()
