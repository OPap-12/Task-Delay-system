from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'due_date', 'completed', 'created_at', 'completed_at', 'is_delayed', 'is_at_risk')
    list_filter = ('completed', 'due_date', 'created_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_date'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'completed_at')
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'due_date')
        }),
        ('Status', {
            'fields': ('completed', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
