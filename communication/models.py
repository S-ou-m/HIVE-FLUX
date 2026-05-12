from django.db import models
from core.models import BaseModel, College
from django.utils import timezone

class Notification(BaseModel):
    PRIORITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('WARNING', 'Warning'),
        ('INFO', 'Info'),
    ]
    TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty'),
        ('FINANCE', 'Finance'),
        ('ACADEMIC', 'Academic'),
        ('SYSTEM', 'System'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default='New Notification')
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='INFO')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    action_url = models.CharField(max_length=500, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    group_key = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.priority} - {self.title} ({self.user.username})"

class NotificationPreference(BaseModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    # Category Toggles
    finance_alerts = models.BooleanField(default=True)
    academic_alerts = models.BooleanField(default=True)
    student_alerts = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    
    # Priority Threshold
    min_priority = models.CharField(
        max_length=20, 
        choices=Notification.PRIORITY_CHOICES, 
        default='INFO'
    )
    
    # Quiet Hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Prefs for {self.user.username}"

class Message(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Notice(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('PUBLISHED', 'Published'),
        ('EXPIRED', 'Expired'),
        ('ARCHIVED', 'Archived'),
    ]
    
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    notice_type = models.CharField(max_length=50, choices=[
        ('ANNOUNCEMENT', 'Announcement'),
        ('ALERT', 'Alert'),
        ('REMINDER', 'Reminder'),
        ('ACADEMIC', 'Academic'),
        ('FINANCE', 'Finance'),
        ('SYSTEM', 'System'),
    ], default='ANNOUNCEMENT')
    
    priority = models.CharField(max_length=20, choices=[
        ('CRITICAL', 'Critical'),
        ('IMPORTANT', 'Important'),
        ('INFO', 'Info'),
    ], default='INFO')
    
    # Targeting Logic (Option A)
    target_roles = models.JSONField(default=list, blank=True, help_text="List of roles: ['Student', 'Faculty', 'Admin']")
    target_departments = models.ManyToManyField('academics.Department', blank=True)
    target_semesters = models.ManyToManyField('academics.Semester', blank=True)
    
    # Actionable CTA
    action_url = models.CharField(max_length=500, null=True, blank=True)
    action_label = models.CharField(max_length=100, null=True, blank=True)
    
    # Lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_notices')

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['college', 'status', 'published_at']),
        ]

    def __str__(self):
        return f"{self.priority} - {self.title}"

    def publish(self):
        self.status = 'PUBLISHED'
        self.published_at = timezone.now()
        self.save()

class NoticeReadStatus(BaseModel):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notice_reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('notice', 'user')
        indexes = [
            models.Index(fields=['user', 'notice']),
        ]

    def __str__(self):
        return f"{self.user.username} read {self.notice.title}"
