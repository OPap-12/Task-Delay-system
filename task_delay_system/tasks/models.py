from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import QuerySet, Case, When, Value, IntegerField, F, ExpressionWrapper
from datetime import timedelta

ROLE_EMPLOYEE = 'Employee'
ROLE_MANAGER = 'Manager'

def is_employee(user):
    groups = {group.name for group in user.groups.all()}
    return ROLE_EMPLOYEE in groups and ROLE_MANAGER not in groups

def is_manager(user):
    groups = {group.name for group in user.groups.all()}
    return ROLE_MANAGER in groups and ROLE_EMPLOYEE not in groups

User.add_to_class('is_employee', property(is_employee))
User.add_to_class('is_manager', property(is_manager))

class TaskQuerySet(QuerySet):
    def with_risk_score(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.annotate(
            raw_risk=Case(
                When(status='APPROVED', then=Value(0)),
                When(due_date__lt=today, then=Value(100)),
                When(due_date=today, then=Value(90)),
                When(due_date=today + timedelta(days=1), then=Value(80)),
                When(due_date=today + timedelta(days=2), then=Value(70)),
                When(due_date__lte=today + timedelta(days=7), then=Value(50)),
                default=Value(20),
                output_field=IntegerField()
            ),
            priority_adj=Case(
                When(status='APPROVED', then=Value(0)),
                When(priority='high', then=Value(10)),
                When(priority='low', then=Value(-10)),
                default=Value(0),
                output_field=IntegerField()
            ),
            risk_score=ExpressionWrapper(F('raw_risk') + F('priority_adj'), output_field=IntegerField())
        )

class Task(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('READY_FOR_REVIEW', 'Ready for Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit Fields
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_tasks')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    completed_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_approve_task", "Can approve or reject tasks"),
            ("can_submit_task", "Can submit tasks for review"),
        ]

    @property
    def is_completed(self):
        return self.status == 'APPROVED'

    @property
    def progress_percentage(self):
        """Map workflow status to a progress percentage for UI progress bars."""
        status_map = {
            'PENDING': 0,
            'IN_PROGRESS': 25,
            'READY_FOR_REVIEW': 60,
            'REJECTED': 30,
            'APPROVED': 100,
        }
        return status_map.get(self.status, 0)



    def clean(self):
        super().clean()
        if self.pk:
            from django.core.exceptions import ValidationError
            old = Task.objects.get(pk=self.pk)
            
            allowed = {
                "PENDING": ["READY_FOR_REVIEW", "IN_PROGRESS", "PENDING"],
                "IN_PROGRESS": ["READY_FOR_REVIEW", "PENDING", "IN_PROGRESS"],
                "READY_FOR_REVIEW": ["APPROVED", "REJECTED", "READY_FOR_REVIEW"],
                "REJECTED": ["PENDING", "IN_PROGRESS", "READY_FOR_REVIEW", "REJECTED"],
                "APPROVED": ["APPROVED"]
            }

            if self.status not in allowed.get(old.status, []):
                raise ValidationError(f"Invalid status transition from {old.status} to {self.status}")

    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'APPROVED' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'APPROVED':
            self.completed_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def is_delayed(self):
        """Check if task is delayed"""
        if self.is_completed and self.completed_at:
            return self.completed_at.date() > self.due_date
        return timezone.now().date() > self.due_date

    def is_at_risk(self):
        """Check if task is at risk (due within 2 days)"""
        if self.is_completed:
            return False
        days_left = (self.due_date - timezone.now().date()).days
        return 0 <= days_left <= 2

    def days_until_due(self):
        """Calculate days until due date"""
        return (self.due_date - timezone.now().date()).days

def get_default_department():
    dept, _ = Department.objects.get_or_create(name='General')
    return dept.id

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return self.name

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_DEFAULT, default=get_default_department, related_name='employees')

    def __str__(self):
        dept_name = self.department.name if self.department else 'Unassigned'
        return f"{self.user.username} - {dept_name}"


