import logging
from django.db import transaction
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from tasks.models import Task

logger = logging.getLogger(__name__)

class TaskStateError(Exception):
    """Raised when an invalid task state transition occurs."""
    pass

class TaskService:
    @staticmethod
    def _notify_websocket(group_name, title, message, type_alert):
        """Helper to safely dispatch websocket notifications after a DB commit."""
        def send_notification():
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "send_notification",
                        "title": title,
                        "message": message,
                        "type_alert": type_alert
                    }
                )
            except Exception as e:
                logger.error(f"WebSocket notification failed: {str(e)}")
        
        # Execute directly instead of on_commit to prevent Windows ASGI event loop dropout
        send_notification()

    @staticmethod
    @transaction.atomic
    def submit_for_review(task_id, user):
        """Submit a task for manager review with transaction protection."""
        # select_for_update prevents race conditions (double submission)
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status not in ['PENDING', 'IN_PROGRESS', 'REJECTED']:
            raise TaskStateError(f"Cannot submit a task that is already {task.status}")

        if task.user != user and not user.is_superuser:
            raise PermissionError("Only the assigned employee can submit this task.")

        task.status = 'READY_FOR_REVIEW'
        # Clear previous rejection reason when re-submitting
        if task.rejected_reason:
            task.rejected_reason = None
        task.save()
        logger.info(f"Task {task.id} submitted for review by {user.username}")

        TaskService._notify_websocket(
            group_name="managers",
            title="Task Ready for Review",
            message=f"Employee {user.username} submitted '{task.title}' for review.",
            type_alert="info"
        )
        return task

    @staticmethod
    @transaction.atomic
    def start_task(task_id, user):
        """Employee starts working on a task — transitions PENDING → IN_PROGRESS."""
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'PENDING':
            raise TaskStateError(f"Can only start a task that is PENDING. Currently {task.status}")

        if task.user != user and not user.is_superuser:
            raise PermissionError("Only the assigned employee can start this task.")

        task.status = 'IN_PROGRESS'
        task.save()
        logger.info(f"Task {task.id} started by {user.username}")
        return task

    @staticmethod
    @transaction.atomic
    def approve_task(task_id, manager):
        """Approve a task, locking the row to stop race conditions."""
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'READY_FOR_REVIEW':
            raise TaskStateError(f"Task must be READY_FOR_REVIEW to approve. Currently {task.status}")

        if not manager.is_manager and not manager.is_superuser:
            raise PermissionError("Only active managers can perform this action.")

        if task.user == manager:
            raise TaskStateError("You cannot approve your own task.")

        task.status = 'APPROVED'
        task.approved_by = manager
        task.approved_at = timezone.now()
        # Clear rejection reason on success
        task.rejected_reason = None
        task.save()
        
        logger.info(f"Task {task.id} approved by {manager}")

        TaskService._notify_websocket(
            group_name=f"user_{task.user.id}",
            title="Task Approved!",
            message=f"Your task '{task.title}' was approved by a manager.",
            type_alert="success"
        )
        return task

    @staticmethod
    @transaction.atomic
    def reject_task(task_id, manager, reason=None):
        """Reject a task and record the reason."""
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'READY_FOR_REVIEW':
            raise TaskStateError(f"Task must be READY_FOR_REVIEW to reject. Currently {task.status}")

        if not manager.is_manager and not manager.is_superuser:
            raise PermissionError("Only active managers can perform this action.")

        if task.user == manager:
            raise TaskStateError("You cannot reject your own task.")

        task.status = 'REJECTED'
        if reason:
            task.rejected_reason = reason
        task.save()
        
        logger.warning(f"Task {task.id} rejected by manager {manager.username}. Reason: {reason}")

        reject_msg = f"Your task '{task.title}' was rejected."
        if reason:
            reject_msg += f" Reason: {reason}"
        TaskService._notify_websocket(
            group_name=f"user_{task.user.id}",
            title="Task Rejected",
            message=reject_msg,
            type_alert="error"
        )
        return task
