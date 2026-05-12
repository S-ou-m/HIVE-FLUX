from django.db.models import Count, Avg, Q
from django.utils import timezone
from lms.models import Submission, EvaluationEvent
from academics.models import Subject
from accounts.models import Faculty

class EvaluationOrchestrator:
    """
    The central brain of the Evaluation Intelligence OS.
    Coordinates workflow states, AI analysis, and faculty productivity.
    """

    @staticmethod
    def get_hub_metrics(faculty, college):
        """Aggregates operational intelligence for the KPI strip."""
        submissions = Submission.objects.filter(
            assignment__faculty=faculty,
            college=college
        )
        
        # 1. Workflow Distribution
        pending = submissions.filter(workflow_state='SUBMITTED').count()
        under_review = submissions.filter(workflow_state='UNDER_REVIEW').count()
        completed = submissions.filter(workflow_state='COMPLETED').count()
        
        # 2. Risk Intelligence
        fraud_flags = submissions.filter(ai_state='FLAGGED').count()
        high_risk = submissions.filter(risk_level__in=['HIGH', 'CRITICAL']).count()
        
        # 3. Productivity Signal
        # Simulated velocity: papers reviewed in last 24 hours
        yesterday = timezone.now() - timezone.timedelta(days=1)
        reviewed_today = submissions.filter(
            review_state='REVIEWED',
            reviewed_at__gte=yesterday
        ).count()
        
        # 4. Class Performance Signal
        avg_score = submissions.filter(workflow_state='COMPLETED').aggregate(Avg('marks'))['marks__avg'] or 0
        
        return {
            "pending": pending,
            "under_review": under_review,
            "completed": completed,
            "fraud_flags": fraud_flags,
            "high_risk": high_risk,
            "reviewed_today": reviewed_today,
            "avg_score": f"{avg_score:.1f}/10",
            "completion_rate": f"{(completed / submissions.count() * 100 if submissions.count() > 0 else 0):.0f}%"
        }

    @staticmethod
    def get_pipeline_board(faculty, college):
        """Groups submissions into operational signal columns."""
        submissions = Submission.objects.filter(
            assignment__faculty=faculty,
            college=college
        ).select_related('student__user', 'assignment__subject')
        
        return {
            "incoming": submissions.filter(workflow_state='SUBMITTED', ai_state='PENDING'),
            "ai_processed": submissions.filter(ai_state='ANALYZED', review_state='UNTOUCHED'),
            "escalated": submissions.filter(Q(ai_state='FLAGGED') | Q(needs_attention=True)),
            "completed": submissions.filter(workflow_state='COMPLETED')[:10] # Recent completions
        }

    @staticmethod
    def log_event(submission, event_type, faculty=None, description="", metadata=None):
        """Creates an operational audit event."""
        return EvaluationEvent.objects.create(
            college=submission.college,
            submission=submission,
            event_type=event_type,
            faculty=faculty,
            description=description,
            metadata=metadata or {}
        )

    @staticmethod
    def bulk_approve_low_risk(faculty, college):
        """
        Enterprise Bulk Action: Approves all submissions with LOW risk and high AI confidence.
        """
        targets = Submission.objects.filter(
            assignment__faculty=faculty,
            college=college,
            risk_level='LOW',
            ai_confidence__gte=0.85,
            workflow_state='SUBMITTED'
        )
        
        count = targets.count()
        if count > 0:
            targets.update(
                workflow_state='COMPLETED',
                review_state='REVIEWED',
                reviewed_at=timezone.now(),
                marks=8.0 # Default safe pass for bulk
            )
            # Log bulk event
            # Logic to log events for each could be added if needed
            
        return count
