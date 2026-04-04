import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from django.contrib.auth.models import User, Group

def set_pwd(username, role='Employee'):
    user, created = User.objects.get_or_create(username=username)
    user.set_password('password123')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    print(f"User {username} ({role}) password set to 'password123'")

set_pwd('admin_manager', 'Manager')
set_pwd('emp_1', 'Employee')
