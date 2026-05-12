import os
import django
import sys

sys.path.append('d:/ERP_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from operations.models import Attendance, AttendanceSession, Timetable
from django.db import transaction

try:
    with transaction.atomic():
        Attendance.objects.all().delete()
        AttendanceSession.objects.all().delete()
        Timetable.objects.all().delete()
        print("Successfully cleared Attendance, AttendanceSession, and Timetable records.")
except Exception as e:
    print(f"Error clearing data: {e}")
