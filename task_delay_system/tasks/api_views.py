from rest_framework import viewsets, permissions, status, decorators, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.core.cache import cache
from .models import Task, ROLE_EMPLOYEE, ROLE_MANAGER
from .serializers import TaskSerializer, UserSerializer
from .services.task_service import TaskService, TaskStateError

class IsAdminOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.all() if user.is_manager else Task.objects.filter(assigned_to=user)
        
        # Resync logic for WebSockets
        updated_after = self.request.query_params.get('updated_after')
        if updated_after:
            qs = qs.filter(updated_at__gt=updated_after)
            
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_manager:
            raise permissions.PermissionDenied("Only admins/managers can create tasks.")
        target_user = serializer.validated_data.get('assigned_to', None)
        if not target_user or target_user.is_manager:
            raise permissions.PermissionDenied("Task must be assigned to an employee.")
        serializer.save(created_by=self.request.user, status='PENDING')

    def perform_update(self, serializer):
        if not self.request.user.is_manager:
            raise permissions.PermissionDenied("Only managers can run full updates on tasks.")
        serializer.save()

    @decorators.action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        """Unified endpoint for changing status using FSM centralized engine."""
        idem_key = request.headers.get('Idempotency-Key')
        if idem_key:
            cache_key = f"idem_{request.user.id}_{pk}_{idem_key}"
            if cache.get(cache_key):
                return Response({"status": "success", "note": "idempotent_hit"})

        action = request.data.get('action') 
        reason = request.data.get('reason', '')
        try:
            if action == 'start':
                task = TaskService.start_task(pk, request.user)
            elif action == 'submit':
                task = TaskService.submit_for_review(pk, request.user)
            elif action == 'approve':
                task = TaskService.approve_task(pk, request.user)
            elif action == 'reject':
                task = TaskService.reject_task(pk, request.user, reason)
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            
            if idem_key:
                cache.set(cache_key, True, timeout=86400) # Cache for 24 hours
            
            return Response({"status": "success", "task_status": task.status})
        except TaskStateError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

class DashboardMetricsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Task.objects.all() if user.is_manager else Task.objects.filter(assigned_to=user)
        metrics = qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='PENDING')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            completed=Count('id', filter=Q(status='APPROVED'))
        )
        return Response(metrics)

class ProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
