from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField, F, ExpressionWrapper, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import Task, Department, EmployeeProfile
from .forms import TaskForm, DepartmentForm, AssignEmployeeForm
from .services.task_service import TaskService, TaskStateError


def _invalidate_dashboard_cache(task):
    """Clear cached dashboard stats for the task owner (and all managers)."""
    cache.delete(f"dashboard_stats_user_{task.assigned_to.id}")
    # Managers see all tasks — invalidate their caches too
    from django.contrib.auth.models import User, Group
    from .models import ROLE_MANAGER
    try:
        manager_group = Group.objects.get(name=ROLE_MANAGER)
        for manager in manager_group.user_set.all():
            cache.delete(f"dashboard_stats_user_{manager.id}")
    except Group.DoesNotExist:
        pass


@login_required
def task_list(request):
    """Display tasks with filtering options and pagination. Managers see all, Employees see own."""
    user = request.user
    tasks = Task.objects.with_risk_score().select_related('assigned_to')
    
    if user.is_manager:
        tasks = tasks.all()
    else:
        tasks = tasks.filter(assigned_to=user)
    
    today = timezone.now().date()

    # Filter params
    status_filter = request.GET.get('status', '').upper()
    delay_filter = request.GET.get('delay', '')
    owner_username = request.GET.get('owner', '')
    query = request.GET.get('q', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if delay_filter == 'delayed':
        tasks = tasks.filter(deadline__lt=today).exclude(status='APPROVED')
    elif delay_filter == 'at_risk':
        tasks = tasks.filter(risk_score__gte=70).exclude(status='APPROVED')

    if owner_username and user.is_manager:
        tasks = tasks.filter(assigned_to__username=owner_username)
    
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))

    tasks = tasks.annotate(
        priority_order=Case(
            When(priority='HIGH', then=Value(3)),
            When(priority='MEDIUM', then=Value(2)),
            When(priority='LOW', then=Value(1)),
            output_field=IntegerField()
        )
    ).order_by('-priority_order', 'deadline')

    # Pagination
    paginator = Paginator(tasks, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # List of employees for filter dropdown (Manager only)
    employees = User.objects.filter(groups__name='Employee').order_by('username') if user.is_manager else None

    context = {
        'tasks': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter.lower(),
        'delay_filter': delay_filter,
        'owner_filter': owner_username,
        'query': query,
        'employees': employees,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def profile_view(request, username=None):
    """View user profile with metrics (Phase A Expansion)."""
    if username:
        if request.user.is_manager or request.user.username == username:
            target_user = get_object_or_404(User, username=username)
        else:
            messages.error(request, "You do not have permission to view other users' profiles.")
            return redirect('my_profile')
    else:
        target_user = request.user

    user_tasks = Task.objects.filter(assigned_to=target_user)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='APPROVED').count()
    
    # Rejection Count: Tasks that have ever had a rejection reason
    rejection_count = user_tasks.filter(rejected_reason__isnull=False).exclude(rejected_reason='').count()
    
    approval_rate = 0
    if total_tasks > 0:
        approval_rate = (completed_tasks * 100) // total_tasks

    # Recent activity
    recent_activity = user_tasks.order_by('-updated_at')[:5]

    context = {
        'profile_user': target_user,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'rejection_count': rejection_count,
        'approval_rate': approval_rate,
        'recent_activity': recent_activity,
    }
    return render(request, 'tasks/profile_detail.html', context)


@login_required
def create_task(request):
    """Create a new task. Managers cannot create tasks (separation of duties)."""
    if request.user.is_manager:
        messages.error(request, "Managers cannot create tasks. Only employees can create and own tasks.")
        return redirect('task_list')
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_to = request.user
            task.created_by = request.user
            task.save()
            _invalidate_dashboard_cache(task)
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm()
    return render(request, 'tasks/create_task.html', {'form': form, 'action': 'Create'})


@login_required
def update_task(request, task_id):
    """Update an existing task."""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if task.status in ['APPROVED', 'READY_FOR_REVIEW']:
        messages.error(request, 'Approved or Under-Review tasks cannot be edited.')
        return redirect('task_detail', task_id=task.id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            _invalidate_dashboard_cache(task)
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/create_task.html', {
        'form': form,
        'task': task,
        'action': 'Update',
    })


@login_required
def delete_task(request, task_id):
    """Delete a task (confirmation required via POST)."""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if task.status in ['APPROVED', 'READY_FOR_REVIEW']:
        messages.error(request, 'Approved or Under-Review tasks cannot be deleted.')
        return redirect('task_detail', task_id=task.id)

    if request.method == 'POST':
        task_title = task.title
        task.delete()
        _invalidate_dashboard_cache(task)
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list')

    return render(request, 'tasks/delete_task.html', {'task': task})


@login_required
@require_POST
def submit_task(request, task_id):
    """Employee submits task for review."""
    if not request.user.is_employee and not request.user.is_superuser:
        messages.error(request, "Only employees can submit tasks for review.")
        return redirect('task_list')
    try:
        task = TaskService.submit_for_review(task_id, request.user)
        _invalidate_dashboard_cache(task)
        messages.success(request, f'Task "{task.title}" submitted for review.')
    except TaskStateError as e:
        messages.error(request, str(e))
    except PermissionError as e:
        messages.error(request, str(e))
    except ObjectDoesNotExist:
        messages.error(request, "Task not found.")
        
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


@login_required
@require_POST
def start_task(request, task_id):
    """Employee starts working on a task (PENDING → IN_PROGRESS)."""
    try:
        task = TaskService.start_task(task_id, request.user)
        _invalidate_dashboard_cache(task)
        messages.success(request, f'Task "{task.title}" is now in progress.')
    except TaskStateError as e:
        messages.error(request, str(e))
    except PermissionError as e:
        messages.error(request, str(e))
    except ObjectDoesNotExist:
        messages.error(request, "Task not found.")

    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


@login_required
@require_POST
def approve_task(request, task_id):
    """Manager approves a task."""
    if not request.user.is_manager and not request.user.is_superuser:
        messages.error(request, "Only managers can approve tasks.")
        return redirect('task_list')
        
    try:
        task = TaskService.approve_task(task_id, request.user)
        _invalidate_dashboard_cache(task)
        messages.success(request, f'Task "{task.title}" approved successfully.')
    except TaskStateError as e:
        messages.error(request, str(e))
    except ObjectDoesNotExist:
        messages.error(request, "Task not found.")
        
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


@login_required
@require_POST
def reject_task(request, task_id):
    """Manager rejects a task."""
    if not request.user.is_manager and not request.user.is_superuser:
        messages.error(request, "Only managers can reject tasks.")
        return redirect('task_list')
        
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, "A rejection reason is required.")
        return redirect(request.META.get('HTTP_REFERER', 'task_list'))
    try:
        task = TaskService.reject_task(task_id, request.user, reason)
        _invalidate_dashboard_cache(task)
        messages.warning(request, f'Task "{task.title}" has been rejected.')
    except TaskStateError as e:
        messages.error(request, str(e))
    except ObjectDoesNotExist:
        messages.error(request, "Task not found.")
        
    return redirect(request.META.get('HTTP_REFERER', 'task_list'))


@login_required
def task_detail(request, task_id):
    """Read-only task detail view. Employees see own tasks, managers see all."""
    user = request.user
    if user.is_manager or user.is_superuser:
        task = get_object_or_404(Task.objects.with_risk_score().select_related('assigned_to', 'approved_by'), id=task_id)
    else:
        task = get_object_or_404(Task.objects.with_risk_score().select_related('assigned_to', 'approved_by'), id=task_id, assigned_to=user)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def review_queue(request):
    """Dedicated review queue for managers — only READY_FOR_REVIEW tasks."""
    user = request.user
    if not user.is_manager and not user.is_superuser:
        messages.error(request, "Only managers can access the review queue.")
        return redirect('task_list')

    tasks = (Task.objects.with_risk_score()
             .filter(status='READY_FOR_REVIEW')
             .select_related('assigned_to')
             .order_by('deadline', '-priority'))

    # Pagination
    paginator = Paginator(tasks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tasks': page_obj,
        'page_obj': page_obj,
        'total_pending': tasks.count(),
    }
    return render(request, 'tasks/review_queue.html', context)


@login_required
def dashboard(request):
    """Task dashboard with predictions and analytics. Managers see global view."""
    user = request.user
    cache_key = f"dashboard_stats_user_{user.id}"
    context = cache.get(cache_key)

    if not context:
        base_tasks = Task.objects.with_risk_score().select_related('assigned_to')
        if user.is_manager:
            tasks = base_tasks.all()
        else:
            tasks = base_tasks.filter(assigned_to=user)
            
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Base filters
        active_tasks = tasks.exclude(status='APPROVED')
        overdue_tasks = active_tasks.filter(deadline__lt=today)
        high_risk_tasks = active_tasks.filter(risk_score__gte=70)
        
        # 1. Status Distribution (Donut Chart Data)
        status_map = dict(Task.STATUS_CHOICES)
        status_counts = tasks.values('status').annotate(count=Count('id'))
        status_dist = {label: 0 for code, label in Task.STATUS_CHOICES}
        for item in status_counts:
            label = status_map.get(item['status'], item['status'])
            status_dist[label] = item['count']

        # 2. Tasks Due This Week (Next 7 days)
        next_week = today + timedelta(days=7)
        tasks_due_week = active_tasks.filter(deadline__range=[today, next_week]).order_by('deadline')[:5]

        # 3. Needs Attention (Rejected OR Overdue)
        needs_attention = tasks.filter(
            Q(status='REJECTED') | Q(deadline__lt=today, status__in=['PENDING', 'IN_PROGRESS'])
        ).order_by('-priority', 'deadline')[:5]

        # Build context
        context = {
            'active_count': active_tasks.count(),
            'overdue_count': overdue_tasks.count(),
            'high_risk_count': high_risk_tasks.count(),
            'status_dist': status_dist,
            'tasks_due_week': tasks_due_week,
            'needs_attention': needs_attention,
        }

        # Progress Percentages for Top Tiles
        total = context['active_count'] or 1
        context['overdue_pct'] = min(100, (context['overdue_count'] * 100) // total)
        context['high_risk_pct'] = min(100, (context['high_risk_count'] * 100) // total)

        # Status Mix Percentages
        total_all = tasks.count() or 1
        status_mix = []
        for label, count in status_dist.items():
            if count > 0:
                pct = (count * 100) // total_all
                status_mix.append({'label': label, 'count': count, 'pct': pct})
        context['status_mix'] = status_mix
        
        if user.is_manager:
            # 4. Manager: Review Queue CTA
            review_queue = tasks.filter(status='READY_FOR_REVIEW')
            context['review_count'] = review_queue.count()
            
            # 5. Manager: Employee Workload Breakdown
            workload = User.objects.filter(assigned_tasks__status__in=['PENDING', 'IN_PROGRESS', 'READY_FOR_REVIEW']).distinct().annotate(
                active_count=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['PENDING', 'IN_PROGRESS'])),
                overdue_count=Count('assigned_tasks', filter=Q(assigned_tasks__deadline__lt=today, assigned_tasks__status__in=['PENDING', 'IN_PROGRESS']))
            ).values('username', 'active_count', 'overdue_count').order_by('-active_count')
            
            # Determine max workload for capacity scaling
            max_active = max([emp['active_count'] for emp in workload] + [5])
            
            workload_list = []
            for emp in workload:
                emp['capacity_pct'] = min(100, (emp['active_count'] * 100) // max_active)
                workload_list.append(emp)
            context['workload_distribution'] = workload_list

            # 6. Manager: Risk Heatmap Data
            risk_stats = {
                'Critical (90+)': tasks.filter(risk_score__gte=90).exclude(status='APPROVED').count(),
                'High (70-89)': tasks.filter(risk_score__range=[70, 89]).exclude(status='APPROVED').count(),
                'Medium (50-69)': tasks.filter(risk_score__range=[50, 69]).exclude(status='APPROVED').count(),
                'Low (<50)': tasks.filter(risk_score__lt=50).exclude(status='APPROVED').count(),
            }
            context['risk_stats'] = risk_stats
        else:
            # 7. Employee: Completed last 7 days
            context['completed_7d'] = tasks.filter(status='APPROVED', completed_at__gte=week_ago).count()
            
        context['recent_tasks'] = list(active_tasks.filter(assigned_to=user).order_by('-created_at')[:5]) if not user.is_manager else list(active_tasks.order_by('-created_at')[:5])
        
        cache.set(cache_key, context, timeout=300)

    return render(request, 'tasks/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_manager)
def department_list(request):
    """List all departments (Manager/Superuser)."""
    departments = Department.objects.annotate(employee_count=Count('employees'))
    return render(request, 'tasks/department_list.html', {'departments': departments})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def department_create(request):
    """Create a new department (Superuser only)."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created.")
            return redirect('department_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentForm()
    return render(request, 'tasks/department_form.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def assign_employee(request):
    """Assign an employee to a department (Superuser only)."""
    if request.method == 'POST':
        form = AssignEmployeeForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['employee']
            department = form.cleaned_data['department']
            profile, created = EmployeeProfile.objects.get_or_create(user=user)
            profile.department = department
            profile.save()
            messages.success(request, f"Assigned {user.username} to {department.name}.")
            return redirect('department_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignEmployeeForm()
    return render(request, 'tasks/assign_employee.html', {'form': form})

@login_required
def reports_view(request):
    """Simple reports view for managers/superusers."""
    if not request.user.is_manager and not request.user.is_superuser:
        messages.error(request, "Only managers can access reports.")
        return redirect('dashboard')

    # Global metrics
    total_approvals = Task.objects.filter(status='APPROVED').count()
    total_rejections = Task.objects.filter(status='REJECTED').count()

    # Department breakdown
    dept_metrics = Department.objects.annotate(
        approvals=Count('employees__user__assigned_tasks', filter=Q(employees__user__assigned_tasks__status='APPROVED')),
        rejections=Count('employees__user__assigned_tasks', filter=Q(employees__user__assigned_tasks__status='REJECTED'))
    )

    context = {
        'total_approvals': total_approvals,
        'total_rejections': total_rejections,
        'dept_metrics': dept_metrics,
    }
    return render(request, 'tasks/reports.html', context)
