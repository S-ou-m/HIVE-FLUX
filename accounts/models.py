import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from core.models import BaseModel, College

class CustomUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(max_length=254) # Override to remove unique=True if it was there
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = CustomUserManager()
    all_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email', 'college'], name='unique_email_per_college')
        ]

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.is_active = False
        self.save()

    def __str__(self):
        return f"{self.username} - {self.college.name if self.college else 'System'}"

class Role(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.college.name if self.college else 'Global'})"

class UserRole(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

class Permission(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

class Faculty(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=255)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"

class Student(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enrollment_no = models.CharField(max_length=100, unique=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    current_semester = models.ForeignKey('academics.Semester', on_delete=models.SET_NULL, null=True, blank=True)
    admission_year = models.IntegerField()
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    credit_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # 🛡️ Student Success OS Fields
    OPERATIONAL_STATES = [
        ('ONBOARDING', 'Onboarding'),
        ('ACTIVE', 'Active'),
        ('AT_RISK', 'At Risk'),
        ('ACADEMIC_WARNING', 'Academic Warning'),
        ('FINANCIAL_HOLD', 'Financial Hold'),
        ('DISCIPLINARY_REVIEW', 'Disciplinary Review'),
        ('PLACEMENT_READY', 'Placement Ready'),
        ('GRADUATED', 'Graduated'),
        ('ALUMNI', 'Alumni'),
        ('INACTIVE', 'Inactive'),
    ]
    operational_state = models.CharField(max_length=30, choices=OPERATIONAL_STATES, default='ONBOARDING')
    reputation_score = models.IntegerField(default=100) # 0-100 scale
    
    bio = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['college', 'created_at']),
            models.Index(fields=['college', 'department']),
            models.Index(fields=['college', 'current_semester']),
        ]

    def _invalidate_analytics_cache(self):
        from django.core.cache import cache
        cache.delete(f'student_core_stats_{self.college_id}')
        cache.delete(f'chart_enrollment_{self.college_id}_6m')
        cache.delete(f'chart_dept_{self.college_id}')
        cache.delete(f'chart_sem_{self.college_id}')
        cache.delete(f'chart_finance_{self.college_id}')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._invalidate_analytics_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._invalidate_analytics_cache()

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.enrollment_no}"

class Guardian(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Guardian of {self.student.user.get_full_name()})"

class Address(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')

class AccessDomain(BaseModel):
    """Scoped institutional zones (e.g., ACADEMICS, FINANCE, LABS)."""
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.college.name})"

class TrustedDevice(BaseModel):
    """Registered and fingerprinted user devices."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trusted_devices')
    device_id = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=50)
    browser_signature = models.TextField()
    trust_state = models.CharField(max_length=20, choices=[
        ('PROVISIONAL', 'Provisional'),
        ('TRUSTED', 'Trusted'),
        ('BANNED', 'Banned'),
    ], default='PROVISIONAL')
    
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.platform} - {self.user.username}"

class IdentitySession(BaseModel):
    """High-fidelity identity pairing for a user-device session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(TrustedDevice, on_delete=models.SET_NULL, null=True)
    
    rotation_seed = models.UUIDField(default=uuid.uuid4)
    trust_score = models.IntegerField(default=50) # 0-100 scale
    
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('LOCKED', 'Locked'),
        ('SUSPENDED', 'Suspended'),
        ('EMERGENCY', 'Emergency Mode'),
    ], default='ACTIVE')
    
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Identity: {self.user.username} (Score: {self.trust_score})"

class ScanTerminal(BaseModel):
    """Institutional checkpoints (Gates, Kiosks, Labs)."""
    TRUST_TIERS = [
        ('HIGH_SECURITY', 'High Security (Gate/Vault)'),
        ('STANDARD', 'Standard (Classroom/Office)'),
        ('PUBLIC', 'Public (Library/Cafeteria)'),
        ('UNVERIFIED', 'Unverified/Temporary'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    terminal_type = models.CharField(max_length=50)
    trust_tier = models.CharField(max_length=20, choices=TRUST_TIERS, default='STANDARD')
    
    is_active = models.BooleanField(default=True)
    secret_key = models.CharField(max_length=64, unique=True) # For terminal auth

    def __str__(self):
        return f"{self.name} [{self.trust_tier}]"

class IdentityScanEvent(BaseModel):
    """Normalized audit log of every identity event."""
    EVENT_TYPES = [
        ('CHECK_IN', 'Campus Check-in'),
        ('CHECK_OUT', 'Campus Check-out'),
        ('CLASSROOM_ENTRY', 'Classroom Session Entry'),
        ('LAB_ACCESS', 'Restricted Lab Access'),
        ('EXAM_VERIFY', 'Exam Hall Verification'),
        ('IDENTITY_REFRESH', 'Token Rotation Event'),
        ('FAILED_ATTEMPT', 'Failed Verification'),
    ]
    
    session = models.ForeignKey(IdentitySession, on_delete=models.CASCADE)
    terminal = models.ForeignKey(ScanTerminal, on_delete=models.SET_NULL, null=True)
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    verification_state = models.CharField(max_length=20)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class PresencePolicy(BaseModel):
    """SaaS-level rules for presence inference."""
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    late_entry_threshold_mins = models.IntegerField(default=15)
    min_session_duration_mins = models.IntegerField(default=30)
    multi_scan_required = models.BooleanField(default=False)
    
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"Policy: {self.name} ({self.college.name})"

# ==========================================================================
# 🚀 STUDENT SUCCESS OS: GOVERNANCE & TELEMETRY
# ==========================================================================

class StudentOperationalEvent(BaseModel):
    """Unified telemetry bus for all student actions and intelligence signals."""
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
        ('SYSTEM', 'System'),
    ]
    
    SEVERITY_LEVELS = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='operational_events')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='acted_events')
    
    event_type = models.CharField(max_length=50) # e.g., ATTENDANCE_MARKED, GPA_UPDATED
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='NORMAL')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='INFO')
    
    context = models.JSONField(default=dict, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4, editable=False)
    
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'event_type']),
            models.Index(fields=['student', 'timestamp']),
            models.Index(fields=['correlation_id']),
        ]

    def __str__(self):
        return f"Event: {self.event_type} for {self.student.user.username}"

class StateChangeLog(BaseModel):
    """High-fidelity audit trail for student lifecycle transitions."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='state_logs')
    old_state = models.CharField(max_length=30)
    new_state = models.CharField(max_length=30)
    
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"State: {self.old_state} -> {self.new_state} ({self.student.user.username})"

# ==========================================================================
# 🚀 PHASE 2: LEARNING INTELLIGENCE & BEHAVIORAL TELEMETRY
# ==========================================================================

class SuccessSignal(BaseModel):
    """Derived high-weight intelligence signals from raw telemetry."""
    SIGNAL_TYPES = [
        ('ATTENDANCE_DECAY', 'Attendance Decay'),
        ('ENGAGEMENT_SPIKE', 'Engagement Spike'),
        ('GRADE_VOLATILITY', 'Grade Volatility'),
        ('CONSISTENCY_AWARD', 'Consistency Award'),
        ('SOCIAL_ISOLATION', 'Social Isolation Risk'),
        ('FINANCIAL_STRESS', 'Financial Stress Signal'),
    ]
    
    SIGNAL_WEIGHTS = [
        ('POSITIVE', 'Positive Impact'),
        ('NEUTRAL', 'Neutral'),
        ('NEGATIVE', 'Negative Impact'),
        ('CRITICAL', 'Critical/Actionable'),
    ]

    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='success_signals')
    
    signal_type = models.CharField(max_length=30, choices=SIGNAL_TYPES)
    weight = models.CharField(max_length=20, choices=SIGNAL_WEIGHTS, default='NEUTRAL')
    confidence_delta = models.IntegerField(default=0) # Impact on overall Success Confidence
    
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signal: {self.signal_type} ({self.student.user.username})"

class SuccessConfidenceHistory(BaseModel):
    """Snapshot of Student Success Confidence over time for trend analysis."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='confidence_history')
    score = models.IntegerField()
    reason_breakdown = models.JSONField(default=dict) # e.g., {'academic': 80, 'attendance': 90}
    
    timestamp = models.DateTimeField(auto_now_add=True)

class InterventionOrchestration(BaseModel):
    """Lifecycle management for student success interventions."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Trigger'),
        ('ACTIVE', 'Active Intervention'),
        ('RESOLVED', 'Resolved/Successful'),
        ('ESCALATED', 'Escalated to Management'),
        ('FAILED', 'Intervention Failed'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='interventions')
    trigger_signal = models.ForeignKey(SuccessSignal, on_delete=models.SET_NULL, null=True)
    
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='assigned_interventions')
    
    action_plan = models.TextField()
    resolution_notes = models.TextField(blank=True)
    
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class AcademicAchievement(BaseModel):
    """Verified institutional milestones and digital credentials."""
    ACHIEVEMENT_TYPES = [
        ('CERTIFICATION', 'Course Certification'),
        ('DEANS_LIST', "Dean's List Placement"),
        ('TOPPER', 'Semester Topper'),
        ('RESEARCH', 'Research Contribution'),
        ('VOLUNTEER', 'Service Recognition'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='achievements')
    
    title = models.CharField(max_length=255)
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    issued_at = models.DateField()
    
    verification_hash = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Achievement: {self.title} for {self.student.user.first_name}"

# ==========================================================================
# 🎯 ACHIEVEMENT OS: GOALS & MILESTONES
# ==========================================================================

class StudentGoal(BaseModel):
    """Institutional goals and performance targets."""
    GOAL_TYPES = [
        ('GPA', 'Grade Point Average'),
        ('CREDIT', 'Credit Completion'),
        ('ATTENDANCE', 'Attendance Threshold'),
        ('SKILL', 'Skill Mastery Level'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='goals')
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=255)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0.0)
    
    is_completed = models.BooleanField(default=False)
    deadline = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Goal: {self.title} ({self.current_value}/{self.target_value})"

# ==========================================================================
# 🤝 RELATIONSHIP OS: SUPPORT GRAPH
# ==========================================================================

class SupportRelationship(BaseModel):
    """Maps the institutional support network around a student."""
    RELATION_TYPES = [
        ('MENTOR', 'Academic Mentor'),
        ('ADVISOR', 'Institutional Advisor'),
        ('PEER_COACH', 'Peer Success Coach'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='support_network')
    staff = models.ForeignKey('Faculty', on_delete=models.CASCADE, null=True, blank=True)
    peer = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='coaching_peers')
    
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPES)
    is_active = models.BooleanField(default=True)
    
    # 📊 SaaS Telemetry Layer
    responsiveness_score = models.IntegerField(default=95) # 0-100
    engagement_frequency = models.IntegerField(default=4) # Interactions per month
    trust_level = models.CharField(max_length=20, choices=[('STRONG', 'Strong'), ('MODERATE', 'Moderate'), ('LOW', 'Low')], default='STRONG')
    intervention_count = models.IntegerField(default=0)
    
    # 🧬 Intelligence Heuristics
    relationship_health = models.CharField(max_length=20, choices=[('OPTIMAL', 'Optimal'), ('STABLE', 'Stable'), ('AT_RISK', 'At Risk')], default='OPTIMAL')
    
    last_interaction = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.relation_type}: {self.student.user.first_name}'s Support"

class SupportCase(BaseModel):
    """Institutional intervention tracking for at-risk students."""
    CASE_CATEGORIES = [
        ('ACADEMIC', 'Academic Recovery'),
        ('FINANCIAL', 'Financial Stability'),
        ('WELLNESS', 'Mental Wellness'),
        ('PLACEMENT', 'Career Readiness'),
    ]
    CASE_STATUS = [
        ('ACTIVE', 'Active Intervention'),
        ('RESOLVED', 'Issue Resolved'),
        ('ESCALATED', 'Escalated to HOD'),
    ]
    PRIORITY_LEVELS = [
        ('CRITICAL', 'Critical Priority'),
        ('HIGH', 'High Priority'),
        ('NORMAL', 'Standard Priority'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='active_cases')
    category = models.CharField(max_length=20, choices=CASE_CATEGORIES)
    status = models.CharField(max_length=20, choices=CASE_STATUS, default='ACTIVE')
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='NORMAL')
    
    assigned_staff = models.ForeignKey('Faculty', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    def __str__(self):
        return f"Case #{self.id[:6]}: {self.title}"

class SupportTimelineEvent(BaseModel):
    """Chronological log of relationship-specific interventions."""
    EVENT_TYPES = [
        ('INTERVENTION', 'Institutional Intervention'),
        ('MENTOR_MEETING', 'Mentor Guidance Session'),
        ('WELLNESS_CHECK', 'Wellness Verification'),
        ('ESCALATION', 'Support Escalation'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='support_timeline')
    relationship = models.ForeignKey(SupportRelationship, on_delete=models.SET_NULL, null=True, blank=True)
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

# ==========================================================================
# 🧠 PROACTIVE INTELLIGENCE: RECOMMENDATIONS & BENCHMARKS
# ==========================================================================

class SystemRecommendation(BaseModel):
    """SaaS-grade institutional recommendations for students."""
    PRIORITY_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('URGENT', 'Urgent')]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='recommendations')
    title = models.CharField(max_length=255)
    action_text = models.CharField(max_length=500) # e.g., "Revise DBMS Unit 3"
    
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    category = models.CharField(max_length=100) # e.g., Academic, Career, Finance
    
    is_completed = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    
    linked_object_id = models.UUIDField(null=True, blank=True) # Optional link to Subject/Invoice etc.

    def __str__(self):
        return f"Rec: {self.title} ({self.priority})"

class PlacementBenchmark(BaseModel):
    """Defines target skill levels for specific career trajectories."""
    name = models.CharField(max_length=255) # e.g., "Tier-1 Product Company"
    required_skills = models.JSONField(help_text="Skill-Level mapping: {'SQL': 80, 'Java': 75}")
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class ExplanationTrace(BaseModel):
    """Deterministic audit trail for system decisions (Scores/Recs)."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    object_type = models.CharField(max_length=100) # e.g., SUCCESS_SCORE, RECOMMENDATION
    object_id = models.UUIDField(null=True)
    
    trace_data = models.JSONField(help_text="Weighted factors: {'attendance': 0.4, 'grades': 0.6}")
    rationale = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trace: {self.object_type} for {self.student.user.username}"

class IntelligenceSnapshot(BaseModel):
    """Precomputed institutional intelligence state for high-performance reads."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='snapshots')
    engine_name = models.CharField(max_length=100) # e.g., COMPETENCY_GRAPH, RECOVERY_PREDICTION
    
    snapshot_data = models.JSONField()
    last_recalculated = models.DateTimeField(auto_now=True)
    freshness_state = models.CharField(max_length=20, default='STALE') # HEALTHY, DEGRADED, STALE

    def __str__(self):
        return f"Snapshot: {self.engine_name} for {self.student.user.username}"

class IntelligenceMetric(BaseModel):
    """Tracking institutional intelligence quality and performance."""
    metric_type = models.CharField(max_length=100) # e.g., REC_ACCEPTANCE, SIGNAL_ACCURACY
    value = models.FloatField()
    context = models.JSONField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Metric: {self.metric_type} ({self.value})"

class OperationalDomainEvent(BaseModel):
    """High-velocity institutional event log for async orchestration."""
    EVENT_TYPES = [
        ('ATTENDANCE_DROP', 'Attendance Drop'),
        ('GPA_CHANGE', 'GPA Change'),
        ('GOAL_COMPLETE', 'Goal Completed'),
        ('INTERVENTION_TRIGGER', 'Intervention Triggered'),
        ('BEHAVIORAL_ANOMALY', 'Behavioral Anomaly'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='domain_events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    context = models.JSONField(help_text="Event metadata and payloads")
    actor = models.CharField(max_length=100, default='SYSTEM')
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event: {self.event_type} for {self.student.user.username}"

class InstitutionalOverride(BaseModel):
    """Manual human authority override for system-generated states."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    target_object = models.CharField(max_length=100) # e.g., RISK_LEVEL, CONFIDENCE_SCORE
    
    previous_val = models.CharField(max_length=255)
    new_val = models.CharField(max_length=255)
    
    mentor_remarks = models.TextField()
    mentor_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Override: {self.target_object} for {self.student.user.username}"

class PolicyDefinition(BaseModel):
    """Dynamic institutional logic for the Policy Evaluation Engine."""
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100) # e.g., ESCALATION, FATIGUE
    
    rules = models.JSONField(help_text="Logic parameters: {'max_alerts': 3}")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class KnowledgeGraphNode(BaseModel):
    """Semantic nodes for the institutional knowledge graph."""
    NODE_TYPES = [('SUBJECT', 'Subject'), ('SKILL', 'Skill'), ('CAREER_PATH', 'Career Path'), ('BEHAVIOR', 'Behavior')]
    
    name = models.CharField(max_length=255)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.node_type}: {self.name}"

class KnowledgeGraphEdge(BaseModel):
    """Semantic relationships (Edges) between institutional nodes."""
    source = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='incoming_edges')
    
    edge_type = models.CharField(max_length=100) # e.g., REQUIRES, PREDICTIVE_OF, ENHANCES
    weight = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.source.name} --({self.edge_type})--> {self.target.name}"

# 🏗️ STUDENT SUCCESS OS: IDENTITY GOVERNANCE & AUDIT
class IdentityInteractionLog(BaseModel):
    """Institutional audit trail for identity command surface interactions."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='identity_logs')
    action = models.CharField(max_length=100) # e.g., DRAWER_OPEN, PASS_ROTATE, DEVICE_REVOKE
    surface = models.CharField(max_length=50) # e.g., COMMAND_DRAWER, PASS_HUB
    
    context = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class IdentityTelemetrySnapshot(BaseModel):
    """Precomputed snapshots of student operational state for zero-latency retrieval."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='telemetry_snapshots')
    
    trust_score = models.IntegerField(default=50)
    confidence_score = models.IntegerField(default=50)
    
    presence_state = models.CharField(max_length=50, default='OFFLINE') # IN_SESSION, ON_CAMPUS, OFFLINE
    active_device = models.CharField(max_length=100, blank=True)
    
    signals_summary = models.JSONField(default=dict) # Aggregated explainability signals
    confidence_layer = models.CharField(max_length=20, default='MODERATE') # HIGH, MODERATE, LOW
    
    last_updated = models.DateTimeField(auto_now=True)

def default_notification_governance():
    return {
        'academic_alerts': True,
        'mentor_nudges': True,
        'quiet_hours': False
    }

class StudentOperationalPreference(BaseModel):
    """Student-specific personalization for the Success OS workspace."""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='preferences')
    
    focus_mode = models.BooleanField(default=False)
    quiet_hours_enabled = models.BooleanField(default=False)
    
    ui_density = models.CharField(max_length=20, choices=[
        ('COMPACT', 'Compact'),
        ('COZY', 'Cozy'),
        ('RELAXED', 'Relaxed')
    ], default='COZY')
    
    theme_accent = models.CharField(max_length=7, default='#FF6B00')
    notification_governance = models.JSONField(default=default_notification_governance)
    
    is_deleted = models.BooleanField(default=False)
    
    theme_intelligence = models.CharField(max_length=50, default='ADAPTIVE')
