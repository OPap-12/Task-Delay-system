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

from django.db.models.signals import pre_save, post_save
import json

@receiver(pre_save, sender='tasks.Task')
def capture_old_payload(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_payload = {
                'status': old_instance.status,
                'assigned_to': old_instance.assigned_to.id if old_instance.assigned_to else None,
                'deadline': str(old_instance.deadline)
            }
        except sender.DoesNotExist:
            instance._old_payload = None
    else:
        instance._old_payload = None

@receiver(post_save, sender='tasks.Task')
def log_task_mutation(sender, instance, created, **kwargs):
    from .models import AuditLog
    action = 'CREATE' if created else 'UPDATE'
    new_payload = {
        'status': instance.status,
        'assigned_to': instance.assigned_to.id if instance.assigned_to else None,
        'deadline': str(instance.deadline)
    }
    
    # Identify orchestrator from threading local or fallback to tracking system (for now left neutral or mapping via service layer implicitly; here we rely on the backend triggering context).
    # Since signals lack request.user natively without middleware thread tracking, we leave user=None (System) or map to created_by on CREATE.
    user_context = instance.created_by if created else None

    AuditLog.objects.create(
        user=user_context,
        action_type=action,
        entity_type='task',
        entity_id=instance.id,
        old_payload=getattr(instance, '_old_payload', None),
        new_payload=new_payload
    )
