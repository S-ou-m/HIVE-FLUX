from django.utils import timezone
from ..models import Student, IdentitySession, IdentityScanEvent, IdentityTelemetrySnapshot, IdentityInteractionLog, StudentOperationalPreference
from ..contracts.module_contracts import MODULE_REGISTRY
from .success_intelligence import SuccessConfidenceEngine
import logging

logger = logging.getLogger(__name__)

class IdentityOrchestrationService:
    """
    🧠 Identity Orchestration Service
    Foundational layer for institutional-grade identity command surface.
    Responsible for contract enforcement, telemetry synthesis, and health state calculation.
    """
    @classmethod
    def synthesize_drawer_state(cls, student: Student, requested_modules: list = None):
        """
        Synthesizes the complete operational state for the Identity Command Drawer.
        Adheres to Operational Module Contracts for priority and freshness.
        """
        if requested_modules is None:
            # Default: Load high-priority modules for initial surface
            requested_modules = [
                m_id for m_id, contract in MODULE_REGISTRY.items() 
                if contract.hydration_priority == 1
            ]

        # 1. Fetch/Create Foundational State
        snapshot, _ = IdentityTelemetrySnapshot.objects.get_or_create(student=student)
        prefs, _ = StudentOperationalPreference.objects.get_or_create(student=student)
        
        # 2. Update High-Velocity Telemetry
        if 'telemetry' in requested_modules:
            cls._update_telemetry_signals(student, snapshot)

        # 3. Build Module Response Pack
        module_states = {}
        for m_id in requested_modules:
            contract = MODULE_REGISTRY.get(m_id)
            if not contract or not cls._check_visibility(student, contract):
                continue

            last_sync_delta = (timezone.now() - snapshot.last_updated).total_seconds()
            health = contract.get_health_state(int(last_sync_delta))

            module_states[m_id] = {
                'id': m_id,
                'name': contract.display_name,
                'health': health,
                'status': 'READY' if health in ['LIVE', 'DELAYED'] else 'STALE',
                'priority': contract.hydration_priority
            }

        # 4. Synthesize Identity Operating System Context
        return {
            'identity': {
                'name': student.user.get_full_name(),
                'username': student.user.username,
                'execution_id': f"EXE-STU-{student.admission_year}-{str(student.id)[:6].upper()}" if student.admission_year else "EXE-STU-GEN",
                'department': student.department.name if student.department else "General",
                'semester': student.current_semester.number if student.current_semester else "N/A",
                'bio': student.bio or "Institutional Identity Verified",
                'trust_score': snapshot.trust_score,
                'confidence_layer': snapshot.confidence_layer
            },
            'security': {
                'confidence_score': cls._calculate_security_confidence(student, snapshot),
                'last_login': student.user.last_login,
                'active_sessions': IdentitySession.objects.filter(user=student.user, status='ACTIVE').count(),
                'integrity_state': 'OPTIMAL' if snapshot.trust_score > 90 else 'REVIEW_REQUIRED'
            },
            'preferences': {
                'focus_mode': prefs.focus_mode,
                'quiet_hours': prefs.quiet_hours_enabled,
                'ui_density': prefs.ui_density,
                'theme_accent': prefs.theme_accent or '#FF6B00'
            },
            'academic_identity': {
                'career_goal': student.specialization or "Exploratory",
                'current_focus': "Final Exams" if student.current_semester and student.current_semester.number % 2 == 0 else "Semester Start",
                'mentor': "Dr. Sarah Mitchell" # Placeholder for relationship layer
            },
            'telemetry': {
                'presence': snapshot.presence_state,
                'active_device': snapshot.active_device,
                'last_updated': snapshot.last_updated
            },
            'modules': module_states,
            'operational_state': cls._detect_operational_state(student, snapshot)
        }

    @classmethod
    def _calculate_security_confidence(cls, student, snapshot):
        """Institutional Security Intelligence."""
        score = snapshot.trust_score
        # Factor in session count (too many sessions reduces confidence)
        active_sessions = IdentitySession.objects.filter(user=student.user, status='ACTIVE').count()
        if active_sessions > 3:
            score -= (active_sessions - 3) * 5
        return max(0, min(100, score))

    @classmethod
    def update_preferences(cls, student, updates):
        """Persist personal governance state changes."""
        prefs, _ = StudentOperationalPreference.objects.get_or_create(student=student)
        
        # Map frontend signals to model fields
        field_map = {
            'notifications': 'notification_governance', # Handle as JSON update if needed
            'visibility': 'focus_mode', # Example mapping
            'ui_density': 'ui_density',
            'theme': 'theme_accent'
        }
        
        for key, value in updates.items():
            if key == 'focus_mode':
                prefs.focus_mode = (value == 'true' or value is True)
            elif key == 'quiet_hours':
                prefs.quiet_hours_enabled = (value == 'true' or value is True)
            elif key in ['ui_density', 'theme_accent']:
                setattr(prefs, key, value)
        
        prefs.save()
        return prefs

    @classmethod
    def execute_emergency_freeze(cls, student):
        """Institutional Lockout Protocol."""
        # 1. Terminate all active sessions except current if possible, or all.
        IdentitySession.objects.filter(user=student.user, status='ACTIVE').update(status='LOCKED')
        
        # 2. Record Security Event
        # IdentityScanEvent.objects.create(student=student, event_type='EMERGENCY_FREEZE', risk_level='CRITICAL')
        
        return True

    @classmethod
    def log_interaction(cls, student: Student, action: str, surface: str, context: dict = None, latency: int = None):
        """Logs an identity command interaction for institutional auditability."""
        IdentityInteractionLog.objects.create(
            student=student,
            action=action,
            surface=surface,
            context=context or {},
            latency_ms=latency
        )

    @classmethod
    def _update_telemetry_signals(cls, student: Student, snapshot: IdentityTelemetrySnapshot):
        """Internal logic to refresh time-sensitive operational signals."""
        # 1. Presence Detection
        last_event = IdentityScanEvent.objects.filter(session__user=student.user).order_by('-timestamp').first()
        if last_event and (timezone.now() - last_event.timestamp).total_seconds() < 3600:
            snapshot.presence_state = 'IN_SESSION' if last_event.event_type == 'CLASSROOM_ENTRY' else 'ON_CAMPUS'
        else:
            snapshot.presence_state = 'OFFLINE'

        # 2. Success Confidence Synthesis (Delegated)
        snapshot.confidence_score = SuccessConfidenceEngine.calculate_score(student)
        
        # 3. Identity Trust Score (Institutional Reliability)
        # Placeholder: Implement behavioral trust logic here
        snapshot.trust_score = 94 
        
        snapshot.save()

    @classmethod
    def _check_visibility(cls, student: Student, contract):
        """Institutional Permission Governance."""
        # For now, we assume the student is viewing their own drawer.
        return True

    @classmethod
    def _detect_operational_state(cls, student: Student, snapshot: IdentityTelemetrySnapshot):
        """Contextual logic for Drawer Morphing."""
        if snapshot.confidence_score < 40:
            return 'AT_RISK'
        elif student.current_semester and student.current_semester.number >= 6 and snapshot.confidence_score > 80:
            return 'PLACEMENT_READY'
        return 'NORMAL'
