import os
import django
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

names = [
    'student_dashboard_overview_partial',
    'student_academic_radar_partial',
    'student_attendance_trend_partial'
]

for name in names:
    try:
        url = reverse(name)
        print(f"{name} -> {url}")
    except Exception as e:
        print(f"{name} -> ERROR: {e}")
