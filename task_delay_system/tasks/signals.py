from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    """
    Automatically create Employee and Manager groups with correct permissions 
    after database migrations.
    """
    if sender.name != 'tasks':
        return

    from .models import Task, ROLE_EMPLOYEE, ROLE_MANAGER
    content_type = ContentType.objects.get_for_model(Task)

    # 1. Employee Group
    employee_group, created = Group.objects.get_or_create(name=ROLE_EMPLOYEE)
    submit_perm = Permission.objects.get(codename='can_submit_task', content_type=content_type)
    employee_group.permissions.add(submit_perm)

    # 2. Manager Group
    manager_group, created = Group.objects.get_or_create(name=ROLE_MANAGER)
    approve_perm = Permission.objects.get(codename='can_approve_task', content_type=content_type)
    manager_group.permissions.add(approve_perm)
    
    # 3. Manager can also view all tasks by default (Add basic task permissions to Manager)
    view_perm = Permission.objects.get(codename='view_task', content_type=content_type)
    manager_group.permissions.add(view_perm, submit_perm)
