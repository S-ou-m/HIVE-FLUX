from django.db.models import Avg
from ..models import Skill, SubjectSkillMapping, StudentSkillMastery, SubjectEnrollment

class CompetencyEngine:
    """
    🧠 Competency Engine
    Maps academic performance to the institutional skill fingerprint.
    """

    @classmethod
    def calculate_mastery(cls, student):
        """Calculates current mastery levels across all skills."""
        # 1. Identify all skills mapped to the student's current subjects
        enrollments = SubjectEnrollment.objects.filter(student=student).select_related('subject')
        subjects = [e.subject for e in enrollments]
        
        # 2. Get relevant skill mappings
        mappings = SubjectSkillMapping.objects.filter(subject__in=subjects).select_related('skill')
        
        skills = set(m.skill for m in mappings)
        
        for skill in skills:
            # Logic: Mastery = Avg(Grade in Subject * SubjectWeight)
            # For now, we use a base performance factor since full GradeBook isn't integrated
            performance_factor = 85 # Mocked base GPA/Performance
            
            # Aggregate weights from all subjects contributing to this skill
            relevant_mappings = [m for m in mappings if m.skill == skill]
            total_weight = sum(m.weight for m in relevant_mappings)
            
            # mastery_level = (performance_factor * total_weight) / (Count of Subjects * 100)
            mastery = min(100, int((performance_factor * total_weight) / (len(relevant_mappings) * 100) * 1.2)) # Slight boost factor
            
            StudentSkillMastery.objects.update_or_create(
                student=student,
                skill=skill,
                defaults={
                    'mastery_level': mastery,
                    'evidence_log': {
                        'subjects': [m.subject.code for m in relevant_mappings],
                        'avg_weight': total_weight / len(relevant_mappings)
                    }
                }
            )
            
        return True

    @classmethod
    def get_skill_fingerprint(cls, student):
        """Returns the student's mastery data for visualization."""
        mastery = StudentSkillMastery.objects.filter(student=student).select_related('skill')
        
        return [
            {
                'name': m.skill.name,
                'category': m.skill.category,
                'level': m.mastery_level,
                'tone': 'emerald' if m.mastery_level > 80 else 'blue' if m.mastery_level > 60 else 'purple'
            }
            for m in mastery
        ]
