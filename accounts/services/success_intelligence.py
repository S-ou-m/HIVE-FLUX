from django.utils import timezone
from django.db.models import Avg
from ..models import Student, SuccessSignal, SuccessConfidenceHistory, StudentOperationalEvent
from operations.models import Attendance, AttendanceSession
from lms.models import Submission
from core.feature_orchestration import FeatureReadiness

class SuccessConfidenceEngine:
    """
    🧠 Success Confidence Engine
    Calculates institutional success probability based on multi-dimensional telemetry.
    """
    
    IS_READY = FeatureReadiness.is_ready('accounts_successsignal')
    
    WEIGHTS = {
        'academic': 0.40,      # GPA and Grades
        'attendance': 0.30,    # Regularity
        'engagement': 0.20,    # Activity frequency
        'reputation': 0.10,    # Behavioral trust
    }

    @classmethod
    def calculate_score(cls, student: Student):
        """Synthesizes raw telemetry into a unified Success Confidence Score."""
        
        # 1. Academic Dimension (Submission Grades)
        submissions = Submission.objects.filter(student=student, marks__isnull=False)
        if submissions.exists():
            avg_marks = submissions.aggregate(Avg('marks'))['marks__avg']
            # Assuming marks are out of 100 for now
            academic_score = min(100, int(avg_marks))
        else:
            academic_score = 75 # Institutional baseline
        
        # 2. Attendance Dimension (Subject Enrollment based)
        from .academic_intelligence import AcademicRadarService
        radar_data = AcademicRadarService.get_subject_radar(student)
        if radar_data:
            attendance_score = sum(s['attendance'] for s in radar_data) / len(radar_data)
        else:
            attendance_score = 0
        
        # 3. Engagement Dimension (Safe Query on Core Event Table)
        event_count = StudentOperationalEvent.objects.filter(
            student=student, 
            timestamp__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        engagement_score = min(100, event_count * 10) 
        
        # 4. Reputation Dimension
        reputation_score = student.reputation_score
        
        # 5. Signal Delta Analysis (Guarded by Infrastructure Check)
        total_delta = 0
        if cls.IS_READY:
            signals = SuccessSignal.objects.filter(student=student, is_active=True)
            total_delta = sum(s.confidence_delta for s in signals)
        
        # Weighted Synthesis
        raw_score = (
            (academic_score * cls.WEIGHTS['academic']) +
            (attendance_score * cls.WEIGHTS['attendance']) +
            (engagement_score * cls.WEIGHTS['engagement']) +
            (reputation_score * cls.WEIGHTS['reputation'])
        )
        
        final_score = max(0, min(100, int(raw_score + total_delta)))
        
        # Perspective: Create history snapshot (Guarded)
        if FeatureReadiness.is_ready('accounts_successconfidencehistory'):
            SuccessConfidenceHistory.objects.create(
                student=student,
                score=final_score,
                reason_breakdown={
                    'academic': academic_score,
                    'attendance': attendance_score,
                    'engagement': engagement_score,
                    'reputation': reputation_score,
                    'signal_delta': total_delta
                }
            )
        
        return final_score

class OperationalSignalEngine:
    """
    📉 Operational Signal Engine
    Analyzes event streams to generate derived intelligence signals.
    """
    
    @classmethod
    def analyze_student(cls, student: Student):
        """Runs pattern recognition on recent events and domain state."""
        if not FeatureReadiness.is_ready('accounts_successsignal'):
            return False 
        
        now = timezone.now()
        
        # 1. Subject-Wise Risk Analysis (Attendance/Syllabus)
        from .academic_intelligence import AcademicRadarService
        radar_data = AcademicRadarService.get_subject_radar(student)
        
        for subject in radar_data:
            if subject['attendance'] < 75:
                # Trigger Attendance Decay Signal
                SuccessSignal.objects.get_or_create(
                    student=student,
                    signal_type='ATTENDANCE_DECAY',
                    college=student.college,
                    is_active=True,
                    defaults={
                        'weight': 'NEGATIVE',
                        'confidence_delta': -10,
                        'description': f"Critical Attendance Decay in {subject['subject_code']} ({subject['attendance']}%)."
                    }
                )
                # Auto-Orchestrate Intervention
                if FeatureReadiness.is_ready('accounts_interventionorchestration'):
                    from ..models import InterventionOrchestration
                    InterventionOrchestration.objects.get_or_create(
                        student=student,
                        title=f"Attendance Recovery: {subject['subject_code']}",
                        college=student.college,
                        defaults={
                            'status': 'PENDING',
                            'action_plan': f"Student must meet with faculty for {subject['subject_code']} to discuss attendance deficit."
                        }
                    )

        # 2. Engagement Spike Detection
        last_24h = now - timezone.timedelta(hours=24)
        event_count = StudentOperationalEvent.objects.filter(student=student, timestamp__gte=last_24h).count()
        if event_count > 10:
            SuccessSignal.objects.get_or_create(
                student=student,
                signal_type='ENGAGEMENT_SPIKE',
                college=student.college,
                defaults={
                    'weight': 'POSITIVE',
                    'confidence_delta': 5,
                    'description': f"High operational velocity ({event_count} events in 24h)."
                }
            )
        
        return True

class EscalationService:
    """
    🛡️ Mentor Escalation Engine
    Orchestrates institutional oversight for unresolved student interventions.
    """
    
    @classmethod
    def process_escalations(cls, student):
        """Identifies stagnant interventions and escalates them to the Relationship OS."""
        if not FeatureReadiness.is_ready('accounts_interventionorchestration'):
            return False
            
        from ..models import InterventionOrchestration, SupportRelationship, SuccessSignal
        
        # 1. Identify Stagnant Interventions (e.g., Pending for > 48h)
        stagnant_interventions = InterventionOrchestration.objects.filter(
            student=student,
            status='PENDING',
            created_at__lt=timezone.now() - timezone.timedelta(hours=48)
        )
        
        for intervention in stagnant_interventions:
            # 2. Lookup Mentor from Support Relationship
            mentor_node = SupportRelationship.objects.filter(
                student=student,
                relation_type='MENTOR',
                is_active=True
            ).select_related('staff__user').first()
            
            if mentor_node:
                # 3. Escalate Status
                intervention.status = 'ACTIVE'
                intervention.action_plan += f"\n[ESCALATION] Assigned to Mentor: {mentor_node.staff.user.get_full_name()}"
                intervention.save()
                
                # 4. Trigger High-Weight Risk Signal
                SuccessSignal.objects.create(
                    student=student,
                    signal_type='MENTOR_ESCALATION',
                    college=student.college,
                    weight='NEGATIVE',
                    confidence_delta=-15,
                    description=f"Critical Escalation: Intervention '{intervention.title}' assigned to Mentor."
                )
                
        return True
