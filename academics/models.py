from django.db import models
from core.models import BaseModel, College

class Department(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Program(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    duration_years = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Semester(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    number = models.IntegerField()
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.program.name if self.program else 'No Program'} - Sem {self.number}"

class Subject(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    credits = models.IntegerField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.code})"

class SubjectEnrollment(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrolled_students')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['student', 'subject', 'semester']
        indexes = [
            models.Index(fields=['student', 'subject']),
            models.Index(fields=['semester']),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} enrolled in {self.subject.code}"

# ==========================================================================
# 📊 COMPETENCY GRAPH: SKILL MAPPING & MASTERY
# ==========================================================================

class Skill(BaseModel):
    """Institutional skills and competencies."""
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100) # e.g., Technical, Cognitive, Professional
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class SubjectSkillMapping(BaseModel):
    """Maps subjects to the skills they cultivate."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='skill_mappings')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='subject_mappings')
    weight = models.IntegerField(default=50) # 0-100 impact of this subject on the skill

    class Meta:
        unique_together = ['subject', 'skill']

class StudentSkillMastery(BaseModel):
    """Tracks evolving mastery levels for a student's skill fingerprint."""
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='skill_mastery')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    mastery_level = models.IntegerField(default=0) # 0-100 scale
    last_updated = models.DateTimeField(auto_now=True)
    
    evidence_log = models.JSONField(default=dict, blank=True) # e.g., {'subject_code': 'GPA'}

    class Meta:
        unique_together = ['student', 'skill']
