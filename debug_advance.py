import os
import django
import sys

# Setup Django
sys.path.append('d:\\ERP_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from django.test import RequestFactory
from accounts.finance_views import admin_advance_payment_save
from core.models import College
from django.contrib.auth import get_user_model
User = get_user_model()

# Create a mock request
factory = RequestFactory()
user = User.objects.filter(is_superuser=True).first()
college = College.objects.first()
from accounts.models import Student
student = Student.objects.first()

request = factory.post(f'/dashboard/admin/partial/finance/payments/record-advance/{student.id}/', {
    'amount': '19998',
    'mode': 'CASH',
    'remarks': 'early'
})
request.user = user
request.college = college

try:
    response = admin_advance_payment_save(request, student.id)
    print("Response Status:", response.status_code)
except Exception as e:
    import traceback
    print("CRASH DETECTED:")
    print(traceback.format_exc())
