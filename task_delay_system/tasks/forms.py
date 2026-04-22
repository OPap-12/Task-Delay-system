from django import forms
from django.utils import timezone
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'deadline', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter task description (optional)',
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def clean_deadline(self):
        """Reject due dates in the past when creating a new task."""
        deadline = self.cleaned_data['deadline']
        # Only enforce on creation, not on update (instance already exists)
        if not self.instance.pk and deadline < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")
        return deadline

from django.contrib.auth.models import User
from .models import Department, EmployeeProfile

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter department name'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }

class AssignEmployeeForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )