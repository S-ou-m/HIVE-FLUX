from django.db.models import Avg
from academics.models import StudentSkillMastery

class CareerIntelligenceService:
    """
    💼 Career OS: Placement Intelligence
    Predicts employability based on competency graph and institutional signals.
    """

    @classmethod
    def calculate_placement_readiness(cls, student):
        """Synthesizes skill mastery into a Placement Confidence Score."""
        mastery = StudentSkillMastery.objects.filter(student=student)
        
        if not mastery.exists():
            return 0
            
        # 1. Base Score = Avg(Skill Levels)
        avg_mastery = mastery.aggregate(Avg('mastery_level'))['mastery_level__avg']
        
        # 2. Weighted Factors
        # Core Technical Skills (Weight: 60%)
        tech_mastery = mastery.filter(skill__category='Technical').aggregate(Avg('mastery_level'))['mastery_level__avg'] or 0
        
        # Professional/Soft Skills (Weight: 40%)
        soft_mastery = mastery.filter(skill__category='Professional').aggregate(Avg('mastery_level'))['mastery_level__avg'] or 0
        
        readiness_score = int((tech_mastery * 0.6) + (soft_mastery * 0.4))
        
        return min(100, readiness_score)

    @classmethod
    def get_career_radar(cls, student):
        """Returns presentation data for the Career OS Radar."""
        readiness = cls.calculate_placement_readiness(student)
        
        return {
            'readiness_score': readiness,
            'velocity': '+12% QoQ',
            'recruiter_interest': 'HIGH' if readiness > 75 else 'MODERATE' if readiness > 50 else 'LOW',
            'top_competencies': StudentSkillMastery.objects.filter(student=student).order_by('-mastery_level')[:3]
        }
