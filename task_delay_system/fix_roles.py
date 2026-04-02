import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User, Group

try:
    manager_group = Group.objects.get(name='Manager')
    employee_group = Group.objects.get(name='Employee')

    for user in User.objects.all():
        groups = set(g.name for g in user.groups.all())
        if 'Manager' in groups and 'Employee' in groups:
            print(f"Removing Employee group from dual-role user: {user.username}")
            user.groups.remove(employee_group)

    print("Role fix completed.")
except Exception as e:
    print(f"Error: {e}")
