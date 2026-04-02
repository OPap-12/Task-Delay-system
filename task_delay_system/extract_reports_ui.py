import os
import django
from django.test import RequestFactory
from django.contrib.auth.models import User
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.views import reports_view

def extract_reports_ui_data():
    print("--- STEP 1 EVIDENCE: UI RENDERING (HTML EXTRACTION) ---")
    user = User.objects.get(username='admin_manager')
    factory = RequestFactory()
    request = factory.get('/reports/')
    request.user = user
    
    response = reports_view(request)
    html_content = response.content.decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Test 5: Summary Cards
    print("\nTest 5 (Aggregate UI Check):")
    stat_values = soup.find_all('div', class_='stat-value')
    if len(stat_values) >= 2:
        print(f"UI Observed Approved: {stat_values[0].get_text().strip()}")
        print(f"UI Observed Rejected: {stat_values[1].get_text().strip()}")
    
    # 2. Test 6: Table Rows
    print("\nTest 6 (Department Breakdown UI Check):")
    table = soup.find('table', class_='data-table')
    if table:
        rows = table.find_all('tr')[1:] # Skip header
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                dept_name = cols[0].get_text().strip()
                # Status badges are in cols[2] and cols[3]
                approved = cols[2].find('span', class_='status-approved').get_text().strip() if cols[2].find('span', class_='status-approved') else "0"
                rejected = cols[3].find('span', class_='status-rejected').get_text().strip() if cols[3].find('span', class_='status-rejected') else "0"
                print(f"Dept: {dept_name} | Approved: {approved} | Rejected: {rejected}")

if __name__ == '__main__':
    extract_reports_ui_data()
