from django.urls import path
from .views import (
    task_list,
    create_task,
    update_task,
    delete_task,
    submit_task,
    start_task,
    approve_task,
    reject_task,
    dashboard,
    task_detail,
    review_queue,
    profile_view,
    department_list,
    department_create,
    assign_employee,
    reports_view,
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
    path('review/', review_queue, name='review_queue'),
    path('reports/', reports_view, name='reports_view'),
    path('profile/', profile_view, name='my_profile'),
    path('profile/<str:username>/', profile_view, name='user_profile'),
    path('add/', create_task, name='create_task'),
    path('task/<int:task_id>/', task_detail, name='task_detail'),
    path('update/<int:task_id>/', update_task, name='update_task'),
    path('delete/<int:task_id>/', delete_task, name='delete_task'),
    path('start/<int:task_id>/', start_task, name='start_task'),
    path('submit/<int:task_id>/', submit_task, name='submit_task'),
    path('approve/<int:task_id>/', approve_task, name='approve_task'),
    path('reject/<int:task_id>/', reject_task, name='reject_task'),

    # Department URLs
    path('departments/', department_list, name='department_list'),
    path('departments/add/', department_create, name='department_create'),
    path('departments/assign/', assign_employee, name='assign_employee'),
]
