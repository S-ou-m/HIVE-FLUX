import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from core.models import College

User = get_user_model()

print("Flushing database (deleting all existing data)...")
call_command('flush', interactive=False)

print("Creating default College 'Main Campus HQ'...")
college = College.objects.create(
    name="Main Campus HQ",
    code="MAIN-01"
)

print("Creating superuser 'admin' with password 'password123'...")
# Create superuser
admin_user = User.objects.create_superuser(
    username="admin",
    email="admin@maincampus.edu",
    password="password123"
)
# Assign the superuser to the new college
admin_user.college = college
admin_user.save()

print("✅ Database successfully reset and seeded!")
print("👉 You can now log in with:")
print("   Username: admin")
print("   Password: password123")
print("   College:  Main Campus HQ")
