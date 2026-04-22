from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Task

# Extend UserAdmin to show roles
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('get_roles',)

    def get_roles(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_roles.short_description = 'Roles'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'created_by', 'priority', 'status', 'deadline', 'is_delayed', 'is_at_risk')
    list_filter = ('status', 'priority', 'deadline', 'created_at')
    search_fields = ('title', 'description', 'assigned_to__username', 'created_by__username')
    date_hierarchy = 'deadline'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'completed_at', 'approved_by', 'approved_at')

    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'deadline', 'priority', 'assigned_to', 'created_by'),
        }),
        ('Workflow Status', {
            'fields': ('status', 'completed_at'),
        }),
        ('Audit Trail', {
            'fields': ('approved_by', 'approved_at', 'rejected_reason'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
