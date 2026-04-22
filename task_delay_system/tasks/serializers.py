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
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Task
        fields = (
            'id', 'assigned_to', 'assigned_to_detail', 'created_by', 'created_by_detail', 
            'title', 'description', 'deadline', 'status', 'status_display',
            'priority', 'is_completed', 'completed_at', 'created_at', 'updated_at',
            'approved_by', 'rejected_reason'
        )
        read_only_fields = (
            "created_by",
            "status",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
            "completed_at"
        )
        extra_kwargs = {
            'assigned_to': {'required': True, 'allow_null': False},
        }

    def validate_deadline(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Deadline cannot be in the past.")
        return value

    def validate(self, data):
        if not data.get('assigned_to'):
            raise serializers.ValidationError({
                "assigned_to": "This field is required and cannot be empty."
            })
        return data
