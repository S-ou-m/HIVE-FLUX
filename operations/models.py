from django.db import models
from django.utils import timezone
from core.models import BaseModel, College
from academics.models import Subject, Semester, Department, Program
import uuid

class Room(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    building = models.CharField(max_length=255, null=True, blank=True)
    capacity = models.IntegerField()
    floor = models.CharField(max_length=50, null=True, blank=True)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.capacity} capacity)"

class SubjectAssignment(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['faculty', 'subject', 'semester', 'college']
        
    def __str__(self):
        return f"{self.faculty.user.get_full_name()} - {self.subject.name}"

class Timetable(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    section = models.CharField(max_length=50) # A / B / C
    
    academic_year = models.CharField(max_length=20) # 2026
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-academic_year', '-version']

    def __str__(self):
        return f"{self.program.name} - Sem {self.semester.number} - Section {self.section} (v{self.version})"

class TimetableSlot(BaseModel):
    SLOT_TYPES = [
        ('REGULAR', 'Regular Class'),
        ('LAB', 'Laboratory'),
        ('TUTORIAL', 'Tutorial'),
        ('SEMINAR', 'Seminar'),
    ]
    DAYS = [
        (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'),
        (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')
    ]

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='slots')
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='REGULAR')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.assignment.subject.name} | Day {self.day_of_week} ({self.start_time})"

class TimetableSlotInstance(BaseModel):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('READY', 'Ready'),
        ('LIVE', 'Live'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed/Cancelled'),
    ]

    timetable_slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE, related_name='instances')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    expected_students = models.IntegerField(default=0)
    actual_students = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['timetable_slot', 'date']
        ordering = ['-date', 'timetable_slot__start_time']

    def __str__(self):
        return f"{self.timetable_slot.assignment.subject.name} on {self.date}"

class AttendanceSession(BaseModel):
    STATUS_CHOICES = [
        ('LIVE', 'Live 🔴'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('LOCKED', 'Audited & Locked'),
    ]
    MODE_CHOICES = [
        ('FACULTY', 'Faculty Marking (Default)'),
        ('SELF', 'Student Self Check-in (QR/OTP)'),
        ('AUTO', 'Smart Auto Attendance'),
        ('HYBRID', 'Hybrid (QR + Manual)'),
    ]
    SESSION_TYPES = [
        ('REGULAR', 'Regular (Timetable)'),
        ('EXTRA', 'Extra Class'),
        ('REPLACEMENT', 'Replacement Class'),
    ]

    college = models.ForeignKey(College, on_delete=models.CASCADE)
    slot_instance = models.OneToOneField(TimetableSlotInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='session')
    
    faculty_snapshot_name = models.CharField(max_length=255)
    subject_snapshot_name = models.CharField(max_length=255)
    
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='REGULAR')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='LIVE')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='QR')
    
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    expected_count = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sessions')
    session_owner = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE, related_name='owned_sessions')
    
    version = models.PositiveIntegerField(default=0)
    snapshot_metadata = models.JSONField(default=dict, blank=True, help_text="Immutable snapshot of context at start time")

    def __str__(self):
        return f"{self.subject_snapshot_name} - {self.started_at.date()}"

class ExecutionControl(BaseModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('READY', 'Ready'),
        ('LIVE', 'Live'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]
    TRIGGER_MODES = [('AUTO', 'Automatic'), ('MANUAL', 'Manual')]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    slot_instance = models.OneToOneField(TimetableSlotInstance, on_delete=models.CASCADE, related_name='execution')
    
    # Time Intelligence
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    grace_minutes = models.IntegerField(default=15)
    
    # State Machine & Safety
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    trigger_mode = models.CharField(max_length=10, choices=TRIGGER_MODES, default='MANUAL')
    version = models.PositiveIntegerField(default=0) # Optimistic Locking
    
    override_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    override_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Execution Control"

class SessionStateLog(BaseModel):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='state_logs')
    from_state = models.CharField(max_length=20)
    to_state = models.CharField(max_length=20)
    
    action_type = models.CharField(max_length=20, default='MANUAL') # AUTO / MANUAL / SYSTEM
    trigger_source = models.CharField(max_length=50, default='ADMIN') # ADMIN / SYSTEM / SCHEDULER
    
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

class FacultyWorklog(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE, related_name='worklogs')
    date = models.DateField()
    
    total_sessions = models.IntegerField(default=0)
    completed_sessions = models.IntegerField(default=0)
    missed_sessions = models.IntegerField(default=0)
    extra_sessions = models.IntegerField(default=0)
    
    total_duration_minutes = models.IntegerField(default=0)
    source_sessions = models.JSONField(default=list, help_text="IDs of sessions contributing to this log")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['faculty', 'date']

class StudentSubjectCache(BaseModel):
    """Performance Layer: Deterministic mapping of student to their active subjects/faculties"""
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='subject_cache')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE)
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    
    cache_version = models.PositiveIntegerField(default=1)
    last_rebuilt_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject', 'timetable']

class EnrollmentMapping(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='batch_enrollments')
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    section = models.CharField(max_length=50)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['student', 'semester', 'is_active']

class SessionEnrollmentSnapshot(BaseModel):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='enrolled_snapshot')
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['session', 'student']

class ScanLog(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='scan_logs')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    scanned_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=[
        ('SUCCESS', 'Success'),
        ('DUPLICATE', 'Duplicate Scan'),
        ('INVALID', 'Invalid QR'),
        ('NOT_ENROLLED', 'Not Enrolled'),
        ('EXPIRED', 'Expired QR'),
    ])
    
    latency_ms = models.IntegerField(null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_type = models.CharField(max_length=50, default='MOBILE_APP') # MOBILE_APP, WEB_PROXY, KIOSK
    scan_source = models.CharField(max_length=50, default='QR_DYNAMIC') # QR_DYNAMIC, MANUAL_ADMIN
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    confidence_score = models.FloatField(default=1.0)
    proxy_flag = models.BooleanField(default=False)
    
    session_version = models.PositiveIntegerField(default=0)
    raw_data = models.TextField(null=True, blank=True)

class Attendance(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    
    status = models.CharField(max_length=10, choices=[
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
    ], default='PRESENT')
    
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

class QRIdentity(BaseModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='qr_identity')
    rotating_token = models.UUIDField(default=uuid.uuid4)
    nonce = models.CharField(max_length=64, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

class OperationsActivityLog(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50) 
    message = models.TextField()
