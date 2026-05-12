import random
from core.models import College
from academics.models import Department, Program, Semester
from operations.models import Room

def seed_institutional_core():
    print("Seeding Institutional Core...")
    
    # 1. Colleges
    colleges_data = [
        {"name": "Hiveflux University - Main Campus", "code": "HUX-MN"},
        {"name": "Hiveflux Institute of Technology", "code": "HIT-EN"},
        {"name": "Hiveflux School of Management", "code": "HSM-BA"}
    ]
    
    colleges = []
    for data in colleges_data:
        college, created = College.objects.get_or_create(code=data['code'], defaults={'name': data['name']})
        colleges.append(college)
        if created: print(f"  Created College: {college.name}")

    # 2. Departments
    depts_data = {
        "HUX-MN": [
            ("Computer Science", "CSE"), ("Electronics", "ECE"), ("Mechanical", "ME"), 
            ("Civil", "CE"), ("Applied Sciences", "AS")
        ],
        "HIT-EN": [
            ("Information Technology", "IT"), ("Cyber Security", "CS"), ("Artificial Intelligence", "AI")
        ],
        "HSM-BA": [
            ("Marketing", "MKT"), ("Finance", "FIN"), ("Human Resources", "HR"), ("Operations", "OPS")
        ]
    }
    
    for college in colleges:
        for name, code in depts_data.get(college.code, []):
            dept, created = Department.objects.get_or_create(
                college=college, code=code, 
                defaults={'name': name}
            )
            if created: print(f"  Created Dept: {name} ({college.code})")

    # 3. Programs & Semesters
    programs_data = [
        {"dept": "CSE", "name": "B.Tech Computer Science", "duration": 4},
        {"dept": "ECE", "name": "B.Tech Electronics", "duration": 4},
        {"dept": "MKT", "name": "MBA Marketing", "duration": 2},
        {"dept": "FIN", "name": "MBA Finance", "duration": 2},
        {"dept": "IT", "name": "B.Tech Information Technology", "duration": 4},
    ]
    
    for p_data in programs_data:
        dept = Department.objects.filter(code=p_data['dept']).first()
        if not dept: continue
        
        program, created = Program.objects.get_or_create(
            college=dept.college,
            department=dept,
            name=p_data['name'],
            defaults={'duration_years': p_data['duration']}
        )
        if created:
            print(f"  Created Program: {program.name}")
            # Create Semesters
            for i in range(1, (p_data['duration'] * 2) + 1):
                Semester.objects.get_or_create(
                    college=dept.college,
                    program=program,
                    number=i
                )

    # 4. Rooms
    for college in colleges:
        for i in range(1, 21):
            Room.objects.get_or_create(
                college=college,
                name=f"Room {100 + i}",
                defaults={
                    'building': random.choice(['Block A', 'Block B', 'Main Block']),
                    'capacity': random.randint(30, 100),
                    'floor': random.choice(['1st', '2nd', '3rd'])
                }
            )
    print("[OK] Institutional Core Seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_institutional_core()
