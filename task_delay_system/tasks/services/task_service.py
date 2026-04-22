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

class BusinessValidationError(Exception):
    """Raised when core business constraints are violated."""
    pass

ROLE_MANAGER  = 'manager'
ROLE_EMPLOYEE = 'employee'

class TaskService:
    @staticmethod
    def _check_permission(user, action):
        """
        Centralized RBAC gate — always called BEFORE any FSM logic.
        Raises PermissionError with explicit 403-mapped message.
        """
        manager_actions  = {'approve', 'reject', 'reassign'}
        employee_actions = {'start', 'submit'}

        if action in manager_actions:
            if not user.groups.filter(name=ROLE_MANAGER).exists() and not user.is_superuser:
                raise PermissionError(f"Action '{action}' requires manager role.")

        elif action in employee_actions:
            if not user.groups.filter(name=ROLE_EMPLOYEE).exists() and not user.is_superuser:
                raise PermissionError(f"Action '{action}' requires employee role.")

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
    def submit_for_review(task_id, user, override=False):
        """Submit a task for manager review with transaction protection."""
        TaskService._check_permission(user, 'submit')  # RBAC before FSM
        task = Task.objects.select_for_update().get(id=task_id)

        # Business Layer Validation
        if not task.deadline or not task.assigned_to:
            raise BusinessValidationError("Cannot submit task missing a deadline or assignee.")

        if not override:
            if task.status not in ['PENDING', 'IN_PROGRESS', 'REJECTED']:
                raise TaskStateError(f"Cannot submit a task that is already {task.status}")

            if task.assigned_to != user and not user.is_manager:
                raise PermissionError("Only the assigned employee can submit this task.")

        task.status = 'READY_FOR_REVIEW'
        if override:
            logger.warning(f"ADMIN OVERRIDE: Task {task.id} forced to READY_FOR_REVIEW by {user.username}")
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
        """Employee starts working on a task -- transitions PENDING -> IN_PROGRESS."""
        TaskService._check_permission(user, 'start')  # RBAC before FSM
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'PENDING' and task.status != 'REJECTED':
            raise TaskStateError(f"Can only start a PENDING or REJECTED task. Currently {task.status}")

        if task.assigned_to != user:
            raise PermissionError("Only the assigned employee can start this task.")

        task.status = 'IN_PROGRESS'
        task.save()
        logger.info(f"Task {task.id} started by {user.username}")
        return task

    @staticmethod
    @transaction.atomic
    def approve_task(task_id, manager):
        """Approve a task, locking the row to stop race conditions."""
        TaskService._check_permission(manager, 'approve')  # RBAC before FSM
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'READY_FOR_REVIEW':
            raise TaskStateError(f"Task must be READY_FOR_REVIEW to approve. Currently {task.status}")

        if not manager.is_manager:
            raise PermissionError("Only Admins or Managers can perform this action.")

        if task.assigned_to == manager:
            raise TaskStateError("You cannot approve your own task.")

        task.status = 'APPROVED'
        task.approved_by = manager
        task.approved_at = timezone.now()
        task.rejected_reason = None
        task.save()
        
        logger.info(f"Task {task.id} approved by {manager}")

        TaskService._notify_websocket(
            group_name=f"user_{task.assigned_to.id}",
            title="Task Approved!",
            message=f"Your task '{task.title}' was approved by a manager.",
            type_alert="success"
        )
        return task

    @staticmethod
    @transaction.atomic
    def reject_task(task_id, manager, reason=None):
        """Reject a task and record the reason."""
        TaskService._check_permission(manager, 'reject')  # RBAC before FSM
        task = Task.objects.select_for_update().get(id=task_id)

        if task.status != 'READY_FOR_REVIEW':
            raise TaskStateError(f"Task must be READY_FOR_REVIEW to reject. Currently {task.status}")

        if not manager.is_manager:
            raise PermissionError("Only Admins or Managers can perform this action.")

        if task.assigned_to == manager:
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
            group_name=f"user_{task.assigned_to.id}",
            title="Task Rejected",
            message=reject_msg,
            type_alert="error"
        )
        return task

    @staticmethod
    @transaction.atomic
    def reassign_task(task_id, manager, new_assignee, override=False):
        """Reassign an active task (Admin/Manager only)."""
        task = Task.objects.select_for_update().get(id=task_id)

        if not manager.is_manager:
            raise PermissionError("Only active Admins or Managers can reassign tasks.")

        if task.status == 'APPROVED' and not override:
            raise TaskStateError("Cannot reassign an APPROVED task without an override flag.")

        task.assigned_to = new_assignee
        if override:
            logger.warning(f"ADMIN OVERRIDE: Task {task.id} reassigned to {new_assignee.username} despite state {task.status}")
        
        task.save()

        TaskService._notify_websocket(
            group_name=f"user_{new_assignee.id}",
            title="Task Assigned",
            message=f"You have been assigned '{task.title}' by {manager.username}.",
            type_alert="info"
        )
        return task
