from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.auth.models import User
from tasks.views import reports_view
import re

class Command(BaseCommand):
    help = 'Renders reports view and prints key metrics for audit'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='admin_manager')
        except User.DoesNotExist:
            self.stdout.write("FAIL: admin_manager not found")
            return

        factory = RequestFactory()
        request = factory.get('/reports/')
        request.user = user
        
        response = reports_view(request)
        html = response.content.decode('utf-8')
        
        self.stdout.write("--- RENDERED UI METRICS ---")
        
        # Extract Summary Cards
        stats = re.findall(r'<div class="stat-value">\s*(.*?)\s*</div>', html, re.DOTALL)
        if len(stats) >= 2:
            self.stdout.write(f"UI_TOTAL_APPROVED: {stats[0].strip()}")
            self.stdout.write(f"UI_TOTAL_REJECTED: {stats[1].strip()}")
        
        # Extract Department Table
        self.stdout.write("--- DEPT BREAKDOWN ---")
        rows = re.findall(r'<td><strong>(.*?)</strong></td>.*?status-approved">(.*?)</span>.*?status-rejected">(.*?)</span>', html, re.DOTALL)
        for name, app, rej in rows:
            self.stdout.write(f"DEPT_{name.upper()}_APPROVED: {app.strip()}")
            self.stdout.write(f"DEPT_{name.upper()}_REJECTED: {rej.strip()}")
