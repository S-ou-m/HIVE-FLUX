import os
import sys
import django
from django.test import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from core.models import College
from accounts.models import User

client = Client()
college = College.objects.get(name='Hiveflux University - Main Campus')

print(f"Testing login for 'admin' at '{college.name}'")

response = client.post('/login/', {
    'role': 'admin',
    'college': str(college.id),
    'username': 'admin',
    'password': 'admin123'
})

print(f"Status Code: {response.status_code}")
if response.status_code == 302:
    print(f"Redirected to: {response.url}")
else:
    # Try to find error message in context
    error = response.context.get('error')
    print(f"Error Message: {error}")
