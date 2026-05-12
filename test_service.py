import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import College
from finance.services.analytics import get_revenue_trend_data, get_payment_mode_data, get_department_revenue_data

# Use the first college
college = College.objects.first()

print("Testing get_revenue_trend_data:")
print(get_revenue_trend_data(college))

print("\nTesting get_payment_mode_data:")
print(get_payment_mode_data(college))

print("\nTesting get_department_revenue_data:")
print(get_department_revenue_data(college))
