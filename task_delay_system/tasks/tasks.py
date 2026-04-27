from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group
from .models import Task, ROLE_MANAGER
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_manager_daily_digest():
    """
    Finds all tasks at risk or delayed, and sends a daily summary to all Managers.
    """
    today = timezone.now().date()
    # At risk means not completed, but due in 2 days or less (including overdue)
    issues = Task.objects.exclude(status='APPROVED').filter(
        deadline__lte=today + timedelta(days=2)
    )

    if not issues.exists():
        logger.info("No at-risk tasks today. Skipping manager digest.")
        return "No tasks to report."

    # Get all users in Manager group who have email
    try:
        manager_group = Group.objects.get(name=ROLE_MANAGER)
        managers = manager_group.user_set.exclude(email='')
        manager_emails = [m.email for m in managers]
    except Group.DoesNotExist:
        return "Manager group does not exist."

    if not manager_emails:
        return "No manager emails found."

    subject = f"Daily Digest: {issues.count()} Tasks At Risk or Delayed"
    
    body_lines = [f"Hello Manager,\n\nYou have {issues.count()} tasks that need attention:\n"]
    for task in issues:
        status_note = "OVERDUE" if task.deadline < today else "DUE SOON"
        body_lines.append(f"- [{status_note}] {task.title} (Assigned to {task.assigned_to.username if task.assigned_to else 'Unassigned'}) - Due: {task.deadline}")
    
    body_lines.append("\nPlease log into the system to review them.")
    message = "\n".join(body_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        manager_emails,
        fail_silently=False,
    )
    
    return f"Sent digest to {len(manager_emails)} managers."


@shared_task
def send_employee_reminders():
    """
    Sends targeted emails to employees who have tasks due within the next 24 hours.
    """
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    imminent_tasks = Task.objects.exclude(status='APPROVED').filter(
        deadline__gte=today,
        deadline__lte=tomorrow
    ).select_related('assigned_to')

    count = 0
    for task in imminent_tasks:
        if task.assigned_to and task.assigned_to.email:
            send_mail(
                f"Action Required: Task '{task.title}' is due soon!",
                f"Hello {task.assigned_to.first_name or task.assigned_to.username},\n\nThis is a reminder that your task '{task.title}' is due on {task.deadline}.\nPlease complete it or submit it for review.",
                settings.DEFAULT_FROM_EMAIL,
                [task.assigned_to.email],
                fail_silently=True,
            )
            count += 1

    return f"Sent {count} reminder emails to employees."
