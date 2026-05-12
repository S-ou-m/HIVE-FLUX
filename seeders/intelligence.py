import os
import sys
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker
from core.models import College
from accounts.models import Student, SuccessSignal, StudentOperationalEvent
from academics.models import StudentSkillMastery
from operations.models import Attendance

fake = Faker()

def seed_intelligence():
    print("Seeding Intelligence & Success OS (Signals & Telemetry)...")
    colleges = College.objects.all()
    
    for college in colleges:
        print(f"  Processing {college.name}...")
        students = Student.objects.filter(college=college)
        
        # 1. Derived Success Signals based on Attendance
        # We'll calculate a simple attendance % and generate signals
        for student in students:
            total_sessions = Attendance.objects.filter(student=student).count()
            if total_sessions == 0: continue
            
            present_sessions = Attendance.objects.filter(student=student, status='PRESENT').count()
            att_pct = (present_sessions / total_sessions) * 100
            
            if att_pct < 60:
                SuccessSignal.objects.create(
                    college=college,
                    student=student,
                    signal_type='ATTENDANCE_DECAY',
                    weight='CRITICAL',
                    description=f"Chronic Absenteeism: Current attendance at {att_pct:.1f}% across all modules.",
                    metadata={'score': att_pct, 'category': 'ATTENDANCE'}
                )
            elif att_pct < 75:
                SuccessSignal.objects.create(
                    college=college,
                    student=student,
                    signal_type='ATTENDANCE_DECAY',
                    weight='NEGATIVE',
                    description=f"Engagement Decay: Downward trend in classroom presence ({att_pct:.1f}%).",
                    metadata={'score': att_pct, 'category': 'ENGAGEMENT'}
                )
            elif att_pct > 90:
                SuccessSignal.objects.create(
                    college=college,
                    student=student,
                    signal_type='CONSISTENCY_AWARD',
                    weight='POSITIVE',
                    description=f"High Momentum Signal: Sustained high engagement ({att_pct:.1f}%).",
                    metadata={'score': att_pct, 'category': 'ACADEMIC'}
                )

        # 2. Skill Mastery
        from academics.models import Skill
        skill_names = [
            ('Python', 'Technical'), ('Problem Solving', 'Cognitive'), 
            ('Communication', 'Professional'), ('Critical Thinking', 'Cognitive'), 
            ('Data Analysis', 'Technical')
        ]
        skills = []
        for name, cat in skill_names:
            skill, _ = Skill.objects.get_or_create(
                college=college, name=name, defaults={'category': cat}
            )
            skills.append(skill)

        for student in students:
            # Randomly assign 3-5 skills to each student
            for skill in random.sample(skills, random.randint(3, 5)):
                StudentSkillMastery.objects.get_or_create(
                    student=student,
                    skill=skill,
                    defaults={
                        'mastery_level': random.randint(20, 95),
                    }
                )

            # 3. Operational Events (Raw Telemetry)
            # Create a few random events for each student to populate the activity bus
            event_types = ['LOGIN', 'PROFILE_VIEW', 'ASSIGNMENT_VIEW', 'ID_SCAN', 'FEE_INQUIRY']
            for _ in range(random.randint(5, 15)):
                StudentOperationalEvent.objects.create(
                    college=college,
                    student=student,
                    event_type=random.choice(event_types),
                    context={'ip': fake.ipv4(), 'device': 'Browser/OSX'},
                    timestamp=timezone.now() - timedelta(hours=random.randint(1, 720))
                )

    print("[OK] Intelligence & Success OS Seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_intelligence()
