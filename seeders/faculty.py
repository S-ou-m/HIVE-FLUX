import random
from faker import Faker
from django.contrib.auth import get_user_model
from core.models import College
from academics.models import Department, Subject
from accounts.models import Faculty

User = get_user_model()
fake = Faker()

def seed_faculty():
    print("Seeding Faculty...")
    colleges = College.objects.all()
    if not colleges: 
        print("[ERROR] No colleges found. Run institutional seeder first.")
        return

    designations = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer']
    
    total_faculty = 0
    for college in colleges:
        departments = Department.objects.filter(college=college)
        for dept in departments:
            # Generate 10-15 faculty per department
            for _ in range(random.randint(10, 15)):
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}@hiveflux.edu"
                username = f"fac_{dept.code.lower()}_{random.randint(1000, 9999)}"
                
                # Use get_or_create to avoid duplicates if run multiple times
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'college': college
                    }
                )
                if created:
                    user.set_password('Changeme123!')
                    user.save()
                
                faculty, f_created = Faculty.objects.get_or_create(
                    user=user,
                    defaults={
                        'college': college,
                        'department': dept,
                        'designation': random.choice(designations),
                        'phone_no': fake.phone_number()[:20]
                    }
                )
                if f_created: total_faculty += 1

    print(f"[OK] {total_faculty} Faculty members seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_faculty()
