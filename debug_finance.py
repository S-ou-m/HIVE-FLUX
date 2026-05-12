import os
import django
import sys

# Setup Django
sys.path.append('d:\\ERP_cms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from django.test import RequestFactory
from accounts.finance_views import admin_finance_partial
from core.models import College
from django.contrib.auth import get_user_model
User = get_user_model()

# Create a mock request
factory = RequestFactory()
user = User.objects.filter(is_superuser=True).first()
college = College.objects.first()

request = factory.get('/dashboard/admin/partial/finance/')
request.user = user
request.college = college

try:
    response = admin_finance_partial(request)
    print("Response Status:", response.status_code)
except Exception as e:
    import traceback
    print("CRASH DETECTED:")
    print(traceback.format_exc())
