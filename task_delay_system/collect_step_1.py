import os
import django
import json
from django.db.models import Count, Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_delay_system.settings')
django.setup()

from tasks.models import Task, Department

def collect_step_1_json():
    evidence = {
        "step_1": {
            "test_5": {
                "db_approved": Task.objects.filter(status='APPROVED').count(),
                "db_rejected": Task.objects.filter(status='REJECTED').count()
            },
            "test_6": []
        }
    }
    
    depts = Department.objects.annotate(
        approvals=Count('employees__user__tasks', filter=Q(employees__user__tasks__status='APPROVED')),
        rejections=Count('employees__user__tasks', filter=Q(employees__user__tasks__status='REJECTED'))
    ).order_by('name')
    
    for d in depts:
        evidence["step_1"]["test_6"].append({
            "name": d.name,
            "approved": d.approvals,
            "rejected": d.rejections
        })
    
    with open('step_1_evidence.json', 'w') as f:
        json.dump(evidence, f, indent=4)
    
    print("Evidence written to step_1_evidence.json")

if __name__ == '__main__':
    collect_step_1_json()
