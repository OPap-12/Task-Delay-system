from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Task
from .forms import TaskForm

@login_required
def task_list(request):
    """Display all tasks with filtering options"""
    tasks = Task.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter == 'completed':
        tasks = tasks.filter(completed=True)
    elif status_filter == 'pending':
        tasks = tasks.filter(completed=False)
    
    # Filter by delay status
    delay_filter = request.GET.get('delay', '')
    if delay_filter == 'delayed':
        tasks = [task for task in tasks if task.is_delayed()]
    elif delay_filter == 'at_risk':
        tasks = [task for task in tasks if task.is_at_risk()]
    
    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'delay_filter': delay_filter,
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def create_task(request):
    """Create a new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm()
    return render(request, 'tasks/create_task.html', {'form': form, 'action': 'Create'})

@login_required
def update_task(request, task_id):
    """Update an existing task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'tasks/create_task.html', {
        'form': form,
        'task': task,
        'action': 'Update'
    })

@login_required
def delete_task(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list')
    
    return render(request, 'tasks/delete_task.html', {'task': task})

@login_required
def complete_task(request, task_id):
    """Mark a task as completed"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if not task.completed:
        task.completed = True
        task.completed_at = timezone.now()
        task.save()
        messages.success(request, f'Task "{task.title}" marked as completed!')
    else:
        messages.info(request, f'Task "{task.title}" is already completed.')
    
    return redirect('task_list')

@login_required
def toggle_task(request, task_id):
    """Toggle task completion status"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if task.completed:
        task.completed = False
        task.completed_at = None
        messages.info(request, f'Task "{task.title}" marked as pending.')
    else:
        task.completed = True
        task.completed_at = timezone.now()
        messages.success(request, f'Task "{task.title}" marked as completed!')
    
    task.save()
    return redirect('task_list')

@login_required
def dashboard(request):
    """Task dashboard with predictions and analytics"""
    tasks = Task.objects.filter(user=request.user)
    
    # Statistics
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    pending_tasks = tasks.filter(completed=False).count()
    delayed_tasks = [t for t in tasks if t.is_delayed()]
    at_risk_tasks = [t for t in tasks if t.is_at_risk()]
    
    # Prediction data
    high_risk_tasks = [t for t in tasks.filter(completed=False) if t.risk_score() >= 70]
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'delayed_tasks': delayed_tasks,
        'at_risk_tasks': at_risk_tasks,
        'high_risk_tasks': high_risk_tasks,
        'completion_rate': round(completion_rate, 1),
        'tasks': tasks.filter(completed=False)[:5],  # Recent pending tasks
    }
    
    return render(request, 'tasks/dashboard.html', context)
