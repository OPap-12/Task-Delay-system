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
    list_display = ('title', 'user', 'priority', 'status', 'due_date', 'is_delayed', 'is_at_risk')
    list_filter = ('status', 'priority', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'due_date'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'completed_at', 'approved_by', 'approved_at')

    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'due_date', 'priority', 'user'),
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
