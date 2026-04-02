from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task

class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'roles')

    def get_roles(self, obj):
        return [group.name for group in obj.groups.all()]

class TaskSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Task
        fields = (
            'id', 'user', 'user_detail', 'title', 'description', 
            'due_date', 'status', 'status_display',
            'priority', 'is_completed', 'completed_at', 'created_at', 'updated_at',
            'approved_by', 'rejected_reason'
        )
        read_only_fields = (
            "user",
            "status",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "completed_at"
        )

    def validate_due_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
