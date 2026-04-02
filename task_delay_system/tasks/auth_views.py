from functools import wraps
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from .auth_forms import UserRegistrationForm, UserLoginForm
from .models import ROLE_EMPLOYEE


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('task_list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role', ROLE_EMPLOYEE)
            from django.contrib.auth.models import Group
            from .models import ROLE_MANAGER
            
            group_name = ROLE_MANAGER if role == 'Manager' else ROLE_EMPLOYEE
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created! You have been assigned the {group_name} role. You can now sign in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'tasks/register.html', {'form': form})


def restrict_auth_access(view_func):
    """Redirect to dashboard if already logged in."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@restrict_auth_access
@ratelimit(key='ip', rate='100/15m', method='POST', block=True)
def login_view(request):
    """User login view with rate limiting."""
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                # Validate redirect URL to prevent open redirect attacks
                next_url = request.GET.get('next', '')
                if not url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                ):
                    next_url = 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    
    return render(request, 'tasks/login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    """User logout view — POST only to prevent CSRF-based logout attacks."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')
