from django.urls import path
from .views import (
    task_list, 
    create_task, 
    update_task,
    delete_task,
    complete_task,
    toggle_task,
    dashboard
)
from .auth_views import register_view, login_view, logout_view

urlpatterns = [
    # Authentication URLs
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Task URLs
    path('', task_list, name='task_list'),
    path('dashboard/', dashboard, name='dashboard'),
    path('add/', create_task, name='create_task'),
    path('update/<int:task_id>/', update_task, name='update_task'),
    path('delete/<int:task_id>/', delete_task, name='delete_task'),
    path('complete/<int:task_id>/', complete_task, name='complete_task'),
    path('toggle/<int:task_id>/', toggle_task, name='toggle_task'),
]
