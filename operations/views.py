from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Count, Q, F
from .models import (
    AttendanceSession, Timetable, Room, SubjectAssignment, 
    ScanLog, Attendance, QRIdentity, TimetableSlot, TimetableSlotInstance
)
from .services.validation_service import ValidationService
from academics.models import Department, Semester, Subject
import datetime
import logging

logger = logging.getLogger(__name__)

from accounts.dashboard_views import faculty_overview_partial

@login_required
def execution_command_center(request):
    """
    SaaS-Grade Shell for the Academic Execution Engine.
    """
    college = request.college
    today = timezone.now().date()
    
    # Pre-fetch today's session stats
    live_sessions = AttendanceSession.objects.filter(college=college, started_at__date=today, status='LIVE').count()
    total_today = AttendanceSession.objects.filter(college=college, started_at__date=today).count()
    
    context = {
        'live_sessions_count': live_sessions,
        'total_sessions_count': total_today,
        'today': today,
    }
    return render(request, 'dashboard/views/operations/execution_base.html', context)

@login_required
def execution_sessions_partial(request):
    """
    Today's Workload & Session Orchestration View.
    """
    college = request.college
    today = timezone.now().date()
    
    sessions = AttendanceSession.objects.filter(
        college=college, 
        started_at__date=today
    ).select_related('slot_instance__timetable_slot__assignment__subject', 'slot_instance__timetable_slot__room').order_by('started_at')
    
    return render(request, 'dashboard/partials/operations/execution_sessions_list.html', {'sessions': sessions})

@login_required
def execution_scanner_partial(request):
    """
    Admin-Controlled Scanning Panel (Hero Feature).
    """
    session_id = request.GET.get('session_id')
    session = get_object_or_404(AttendanceSession, id=session_id, college=request.college)
    
    context = {
        'session': session,
        'last_scans': session.scan_logs.all()[:10]
    }
    return render(request, 'dashboard/partials/operations/execution_scanner_panel.html', context)

@login_required
def api_process_scan(request, session_id):
    """
    Real-Time Scan Processing API.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    
    session = get_object_or_404(AttendanceSession, id=session_id, college=request.college)
    raw_data = request.POST.get('qr_data')
    device_id = request.POST.get('device_id', 'WEBCAM_ADMIN')
    
    success, message, result_code = ValidationService.process_scan(
        session=session,
        raw_data=raw_data,
        admin_user=request.user,
        device_id=device_id
    )
    
    return JsonResponse({
        'status': 'success' if success else 'error',
        'message': message,
        'result_code': result_code,
        'present_count': session.present_count,
        'expected_count': session.expected_count
    })

@login_required
def api_session_control(request, execution_id, action):
    """
    API for starting/stopping sessions using the SessionStateService.
    """
    from .services.state_service import SessionStateService
    
    # Map UI actions to State Machine statuses
    ACTION_MAP = {
        'start': 'LIVE',
        'pause': 'PAUSED',
        'end': 'COMPLETED',
        'ready': 'READY',
        'cancel': 'CANCELLED'
    }
    
    target_status = ACTION_MAP.get(action)
    if not target_status:
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
    
    try:
        execution = SessionStateService.transition_to(
            execution_id=execution_id,
            target_status=target_status,
            user=request.user,
            reason=f"Manual trigger: {action}"
        )
        
        if request.headers.get('HX-Request'):
            # Return the updated partial for HTMX
            return faculty_overview_partial(request)
            
        return JsonResponse({'status': 'success', 'new_status': execution.status})
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def execution_insights_partial(request):
    """
    SaaS-Grade Execution Intelligence.
    Detects anomalies, duplicate spikes, and coverage gaps.
    """
    college = request.college
    today = timezone.now().date()
    
    insights = []
    
    # 1. Anomaly Detection: Duplicate Spikes
    duplicate_count = ScanLog.objects.filter(college=college, scanned_at__date=today, result='DUPLICATE').count()
    if duplicate_count > 5:
        insights.append({
            'type': 'critical',
            'text': f"High Anomaly Alert: {duplicate_count} duplicate scan attempts detected today.",
            'icon': 'user-ninja'
        })
    
    missed_sessions = TimetableSlotInstance.objects.filter(
        timetable_slot__timetable__college=college, 
        date=today, 
        status='SCHEDULED', 
        timetable_slot__end_time__lt=timezone.now().time()
    ).count()
    
    if missed_sessions > 0:
        insights.append({
            'type': 'warning',
            'text': f"{missed_sessions} sessions missed their scheduled window without going LIVE.",
            'icon': 'clock-rotate-left'
        })
    
    # 3. Efficiency Metric
    success_rate = 0
    total_scans = ScanLog.objects.filter(college=college, scanned_at__date=today).count()
    if total_scans > 0:
        success_scans = ScanLog.objects.filter(college=college, scanned_at__date=today, result='SUCCESS').count()
        success_rate = (success_scans / total_scans) * 100
        
    if success_rate < 80 and total_scans > 20:
        insights.append({
            'type': 'warning',
            'text': f"System throughput efficiency is at {success_rate:.1f}% due to high rejection rates.",
            'icon': 'bolt'
        })
        
    return render(request, 'dashboard/partials/operations/execution_insights.html', {
        'insights': insights,
        'stats': {
            'success_rate': f"{success_rate:.1f}%",
            'total_scans': total_scans
        }
    })

@login_required
def execution_identity_partial(request):
    """
    SaaS-Grade Identity Binding Matrix View.
    """
    college = request.college
    
    context = {
        'active_bindings': QRIdentity.objects.filter(user__college=college).count(),
        'high_trust_percentage': "99.2%", # Default for now
        'potential_proxies': ScanLog.objects.filter(college=college, result='DUPLICATE', scanned_at__date=timezone.now().date()).count()
    }
    
    # Calculate High Trust more accurately
    total_users = QRIdentity.objects.filter(user__college=college).count()
    if total_users > 0:
        malicious_users = ScanLog.objects.filter(college=college, result='DUPLICATE').values('user').distinct().count()
        trust = ((total_users - malicious_users) / total_users) * 100
        context['high_trust_percentage'] = f"{trust:.1f}%"

    return render(request, 'dashboard/partials/operations/execution_identity_matrix.html', context)

@login_required
def execution_audit_partial(request):
    """
    Operational Audit & Traceability Logs.
    """
    return render(request, 'dashboard/partials/operations/execution_audit_logs.html')

@login_required
def api_manual_marking_drawer(request, session_id):
    """
    Returns the side drawer for manual attendance marking.
    """
    session = get_object_or_404(AttendanceSession, id=session_id, college=request.college)
    
    # Get enrolled students not yet marked
    from academics.models import SubjectEnrollment
    already_marked = Attendance.objects.filter(session=session).values_list('student_id', flat=True)
    
    enrolled_students = SubjectEnrollment.objects.filter(
        subject=session.slot_instance.timetable_slot.assignment.subject,
        semester=session.slot_instance.timetable_slot.assignment.semester,
        college=request.college
    ).exclude(student_id__in=already_marked).select_related('student__user')
    
    context = {
        'session': session,
        'students': enrolled_students,
    }
    return render(request, 'dashboard/partials/operations/manual_marking_drawer.html', context)

@login_required
def api_manual_mark_execute(request, session_id, student_id):
    """
    Executes a manual attendance mark with audit trail.
    """
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)
        
    session = get_object_or_404(AttendanceSession, id=session_id, college=request.college)
    from accounts.models import Student
    student = get_object_or_404(Student, id=student_id, college=request.college)
    
    with transaction.atomic():
        attendance, created = Attendance.objects.get_or_create(
            session=session,
            student=student,
            defaults={
                'college': request.college,
                'status': 'PRESENT',
                'marked_by': request.user
            }
        )
        
        if created:
            AttendanceSession.objects.filter(id=session.id).update(present_count=F('present_count') + 1)
            
            ScanLog.objects.create(
                college=request.college,
                session=session,
                user=student.user,
                result='SUCCESS',
                device_id='MANUAL_OVERRIDE',
                raw_data=f"Manual mark by {request.user.username}",
                session_version=session.version
            )
            
    return HttpResponse(f"""
        <div class="manual-success-badge animate-fade-in" style="color: #10B981; font-size: 11px; font-weight: 800;">
            <i class="fa-solid fa-check-circle mr-1"></i> MARKED
        </div>
    """)
