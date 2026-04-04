"""
URL configuration for task_delay_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from tasks.api_views import TaskViewSet

from django.http import HttpResponse
from django.contrib.auth.models import User
import logging

def create_temp_superuser(request):
    try:
        if not User.objects.filter(username='presentation_admin').exists():
            User.objects.create_superuser('presentation_admin', 'admin@example.com', 'Presentation123!')
            return HttpResponse("Superuser 'presentation_admin' created successfully! Password is: Presentation123!")
        return HttpResponse("Superuser 'presentation_admin' already exists. Password is: Presentation123!")
    except Exception as e:
        return HttpResponse(f"Error creating superuser: {str(e)}")

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('setup-admin/', create_temp_superuser),
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    
    # API v1
    path('api/v1/', include(router.urls)),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

