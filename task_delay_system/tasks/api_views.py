from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from .models import Task, ROLE_EMPLOYEE, ROLE_MANAGER
from .serializers import TaskSerializer
from .services.task_service import TaskService, TaskStateError

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name=ROLE_EMPLOYEE).exists()

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name=ROLE_MANAGER).exists()

class IsTaskOwnerOrManager(permissions.BasePermission):
    """Object-level permission: only the task owner or a manager can modify/delete."""
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user who can see the object
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for the owner or a manager
        return obj.user == request.user or request.user.is_manager or request.user.is_superuser

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task management.
    - Employees see only their tasks.
    - Managers see all tasks.
    - Object-level ownership enforced on mutations.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrManager]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return Task.objects.all()
        return Task.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit_for_review(self, request, pk=None):
        """Employee submits task for review."""
        if not request.user.is_employee and not request.user.is_superuser:
            return Response({"error": "Only employees can submit for review."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            task = TaskService.submit_for_review(pk, request.user)
            return Response({
                "status": "success",
                "message": "Task submitted for manager review.",
                "data": {"task_id": task.id, "status": task.status}
            })
        except TaskStateError as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({"status": "error", "message": "Task not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsManager])
    def approve(self, request, pk=None):
        """Manager approves the task."""
        try:
            task = TaskService.approve_task(pk, request.user)
            return Response({
                "status": "success",
                "message": "Task approved successfully.",
                "data": {"task_id": task.id, "status": task.status}
            })
        except TaskStateError as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=True, methods=['post'], permission_classes=[IsManager])
    def reject(self, request, pk=None):
        """Manager rejects the task."""
        reason = request.data.get('reason', '')
        try:
            task = TaskService.reject_task(pk, request.user, reason)
            return Response({
                "status": "success",
                "message": "Task rejected successfully.",
                "data": {"task_id": task.id, "status": task.status}
            })
        except TaskStateError as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
