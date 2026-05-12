import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import Student, Faculty, SupportRelationship, SupportCase, SupportTimelineEvent

def seed_relationship_os():
    student = Student.objects.filter(user__username='arian').first()
    if not student:
        print("Student 'arian' not found.")
        return

    # 1. Clear existing for clean slate
    SupportRelationship.objects.filter(student=student).delete()
    SupportCase.objects.filter(student=student).delete()
    SupportTimelineEvent.objects.filter(student=student).delete()

    # 2. Create Support Nodes
    faculties = list(Faculty.objects.all()[:3])
    if not faculties:
        print("No faculties found to seed relationships.")
        return

    nodes = [
        ('MENTOR', faculties[0], 'STRONG', 'OPTIMAL', 98, 6),
        ('ADVISOR', faculties[1], 'MODERATE', 'STABLE', 75, 2),
    ]

    for r_type, staff, trust, health, resp, freq in nodes:
        rel = SupportRelationship.objects.create(
            student=student,
            staff=staff,
            relation_type=r_type,
            trust_level=trust,
            relationship_health=health,
            responsiveness_score=resp,
            engagement_frequency=freq,
            last_interaction=timezone.now() - timedelta(hours=random.randint(1, 48))
        )

        # Create some timeline events
        SupportTimelineEvent.objects.create(
            student=student,
            relationship=rel,
            event_type='MENTOR_MEETING' if r_type == 'MENTOR' else 'INTERVENTION',
            description=f"Standard monthly {r_type.lower()} sync completed. Performance trajectory reviewed."
        )

    # 3. Create Support Cases
    SupportCase.objects.create(
        student=student,
        category='ACADEMIC',
        priority='HIGH',
        status='ACTIVE',
        assigned_staff=faculties[0],
        title='Advanced SQL Mastery Support',
        description='Student requires additional guidance on complex recursive queries to reach Tier-1 placement readiness.'
    )

    print("Relationship OS seeded successfully for Arian Nayak.")

if __name__ == '__main__':
    seed_relationship_os()
