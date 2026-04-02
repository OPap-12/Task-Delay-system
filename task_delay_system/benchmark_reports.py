import os
import django
import time
from django.db.models import Count, Q
from django.test import RequestFactory
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.views import reports_view

def benchmark_reports():
    print("--- BACKEND PERFORMANCE BENCHMARK ---")
    user = User.objects.get(username='admin_manager')
    factory = RequestFactory()
    request = factory.get('/reports/')
    request.user = user
    
    start_time = time.time()
    response = reports_view(request)
    duration = time.time() - start_time
    
    print(f"Reports View Execution Time: {duration:.4f} seconds")
    if duration < 1.0:
        print("RESULT: PASS (Under 1s)")
    else:
        print("RESULT: FAIL (Over 1s - Optimization required)")

if __name__ == '__main__':
    benchmark_reports()
