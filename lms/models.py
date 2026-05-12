from django.db import models
from core.models import BaseModel, College

class Assignment(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()

class Submission(BaseModel):
    # --- WORKFLOW STATES (Enterprise Grade) ---
    WORKFLOW_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('COMPLETED', 'Completed'),
    ]
    AI_STATES = [
        ('PENDING', 'Pending Analysis'),
        ('ANALYZED', 'Analyzed'),
        ('FLAGGED', 'Flagged (Risk)'),
    ]
    REVIEW_STATES = [
        ('UNTOUCHED', 'Untouched'),
        ('IN_PROGRESS', 'In Progress'),
        ('REVIEWED', 'Reviewed'),
        ('RETURNED', 'Returned to Student'),
    ]
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    ]

    college = models.ForeignKey(College, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    
    file_url = models.CharField(max_length=500)
    
    # --- DECOUPLED STATE ENGINE ---
    workflow_state = models.CharField(max_length=20, choices=WORKFLOW_CHOICES, default='SUBMITTED')
    ai_state = models.CharField(max_length=20, choices=AI_STATES, default='PENDING')
    review_state = models.CharField(max_length=20, choices=REVIEW_STATES, default='UNTOUCHED')
    
    # --- OPERATIONAL INTELLIGENCE ---
    priority_score = models.IntegerField(default=0) # 0-100
    needs_attention = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='LOW')
    ai_confidence = models.FloatField(default=0.0) # 0.0 - 1.0
    
    # --- GRADING & FEEDBACK ---
    marks = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    voice_feedback = models.FileField(upload_to='feedback/voice/', null=True, blank=True)
    
    # --- STRUCTURED DATA DOMAINS ---
    rubric_data = models.JSONField(default=dict, blank=True)
    ai_analysis = models.JSONField(default=dict, blank=True)
    learning_signals = models.JSONField(default=dict, blank=True)
    fraud_signals = models.JSONField(default=dict, blank=True)
    
    # --- PERFORMANCE METRICS ---
    review_duration_seconds = models.IntegerField(default=0)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # --- REVIEW MEMORY ---
    metadata_json = models.JSONField(default=dict, blank=True) # last_scroll_position, last_opened_at

    def get_similarity(self):
        return self.fraud_signals.get("content_similarity", "0%")

    def get_ai_score(self):
        return self.fraud_signals.get("ai_pattern_match", "0%")

    def __str__(self):
        return f"{self.student} - {self.assignment}"

class EvaluationEvent(BaseModel):
    """Operational audit trail for the Evaluation OS."""
    EVENT_TYPES = [
        ('SUBMISSION_UPLOADED', 'Submission Uploaded'),
        ('AI_ANALYSIS_COMPLETED', 'AI Analysis Completed'),
        ('REVIEW_STARTED', 'Review Started'),
        ('RISK_FLAGGED', 'Risk Flagged'),
        ('FEEDBACK_SENT', 'Feedback Sent'),
        ('GRADE_LOCKED', 'Grade Locked'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

class Exam(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE)

class Marks(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    marks_obtained = models.FloatField()

class Grade(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    min_marks = models.FloatField()
    max_marks = models.FloatField()
    grade = models.CharField(max_length=10)
