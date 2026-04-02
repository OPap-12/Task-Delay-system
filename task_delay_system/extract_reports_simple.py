import os
import django
import re
from django.test import RequestFactory
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.views import reports_view

def extract_simple_ui_data():
    print("--- STEP 1 EVIDENCE (ROBUST) ---")
    try:
        user = User.objects.get(username='admin_manager')
    except User.DoesNotExist:
        print("FAIL: admin_manager does not exist")
        return

    factory = RequestFactory()
    request = factory.get('/reports/')
    request.user = user
    
    try:
        response = reports_view(request)
        html = response.content.decode('utf-8')
    except Exception as e:
        print(f"FAIL: Rendering failed: {e}")
        return
    
    # Summary Cards
    stat_values = re.findall(r'<div class="stat-value">\s*(.*?)\s*</div>', html, re.DOTALL)
    print("\nTest 5 (Aggregate UI Check):")
    if len(stat_values) >= 2:
        print(f"UI Observed Approved: {stat_values[0]}")
        print(f"UI Observed Rejected: {stat_values[1]}")
    else:
        print(f"FAIL: Stat cards not found (Found {len(stat_values)})")

    # Table Breakdown
    print("\nTest 6 (Department Breakdown UI Check):")
    rows = re.findall(r'<td><strong>(.*?)</strong></td>.*?status-approved">(.*?)</span>.*?status-rejected">(.*?)</span>', html, re.DOTALL)
    if rows:
        for name, approved, rejected in rows:
            print(f"Dept: {name} | Approved: {approved} | Rejected: {rejected}")
    else:
        print("FAIL: No department rows matched in UI.")

if __name__ == '__main__':
    extract_simple_ui_data()
