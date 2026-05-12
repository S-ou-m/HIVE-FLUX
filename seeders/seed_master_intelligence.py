import os
import sys
import django
import time

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.models import College, Student, Faculty

User = get_user_model()

def clear_existing_data():
    print("Cleaning up existing operational data (preserving Admin)...")
    # Preserve admin:admin123
    # We'll delete all users EXCEPT 'admin'
    User.objects.exclude(username='admin').delete()
    # Most other models will cascade delete because they are linked to User/College
    # But let's be thorough
    College.objects.all().delete()
    print("Environment Purged.")

def run_master_seeder():
    start_time = time.time()
    print("\nHIVE FLUX — MASTER REALISM ENGINE INITIALIZED")
    print("==================================================\n")

    # 0. Cleanup
    clear_existing_data()

    # Import seeders
    from seeders.institutional import seed_institutional_core
    from seeders.faculty import seed_faculty
    from seeders.students import seed_students
    from seeders.academics import seed_academics
    from seeders.operations import seed_operations
    from seeders.finance import seed_finance
    from seeders.intelligence import seed_intelligence

    # Execution Flow (Relational Order)
    try:
        print("[START] Institutional Core...")
        seed_institutional_core()
        
        print("[START] Faculty Profiles...")
        seed_faculty()
        
        print("[START] Student Directory (Bulk)...")
        seed_students()
        
        print("[START] Academic Subjects & Timetables...")
        seed_academics()
        
        print("[START] Operational Telemetry (Attendance)...")
        seed_operations()
        
        print("[START] Financial Records (Invoices & Payroll)...")
        seed_finance()
        
        print("[START] Intelligence Signals...")
        seed_intelligence()
    except Exception as e:
        print(f"\nSEEDING FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print(f"MASTER SEEDING COMPLETE in {duration:.2f}s")
    print(f"Final Audit:")
    print(f"   - Total Colleges: {College.objects.count()}")
    print(f"   - Total Students: {Student.objects.count()}")
    print(f"   - Total Faculty:  {Faculty.objects.count()}")
    print(f"   - Total Users:    {User.objects.count()}")
    print("="*50 + "\n")
    print("READY FOR INSTITUTIONAL AUDIT.\n")

if __name__ == "__main__":
    run_master_seeder()
