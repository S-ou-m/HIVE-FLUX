from core.models import College
from academics.models import Department, Program, Semester, Subject
from accounts.models import User, Faculty, Student

def seed_core():
    print("Seeding Minimal Academic Core (Corrected Schema)...")
    c, _ = College.objects.get_or_create(name='Main Campus HQ')
    d, _ = Department.objects.get_or_create(
        college=c, 
        name='Computer Science',
        defaults={'code': 'CS'}
    )
    
    p, _ = Program.objects.get_or_create(
        college=c, 
        department=d, 
        name='B.Tech',
        defaults={'duration_years': 4}
    )
    
    s, _ = Semester.objects.get_or_create(
        college=c, 
        program=p, 
        number=1
    )
    
    Subject.objects.get_or_create(
        college=c, 
        semester=s, 
        name='Data Structures', 
        code='CS101',
        defaults={'credits': 4}
    )

    # Link Admin to College
    admin = User.objects.get(username='admin')
    admin.college = c
    admin.save()
    
    print("Core Seeding Complete.")

if __name__ == "__main__":
    seed_core()
