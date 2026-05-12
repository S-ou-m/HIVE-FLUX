import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import User

admin = User.objects.filter(username='admin').first()
if admin:
    print(f"Admin exists. Staff: {admin.is_staff}, Superuser: {admin.is_superuser}")
    # Reset password just in case
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()
    print("Password reset to 'admin123' and elevated to superuser.")
else:
    print("Admin does not exist. Creating...")
    # Get first college if any
    from core.models import College
    college = College.objects.first()
    User.objects.create_superuser('admin', 'admin@hiveflux.edu', 'admin123', college=college)
    print("Admin 'admin' created with password 'admin123'.")
