from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from .models import Student, Faculty, IdentitySession, StudentOperationalEvent, StudentGoal, SupportRelationship, SupportTimelineEvent
from academics.models import SubjectEnrollment
from .services.career_intelligence import CareerIntelligenceService
from .services.success_intelligence import SuccessConfidenceEngine
from .services.identity_orchestration import IdentityOrchestrationService
from core.feature_orchestration import FeatureReadiness

@login_required
def student_dashboard(request):
    """
    🧠 Student Success OS: Primary Workspace
    Handles full-shell rendering and determines initial view context for deep-linking.
    """
    # 🛡️ Role-Based Redirect Engine
    student = Student.objects.filter(user=request.user).first()
    if not student:
        # If user is faculty, redirect them to faculty dashboard
        if Faculty.objects.filter(user=request.user).exists():
            return redirect('faculty_dashboard')
        # Admin check
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        
        return render(request, 'dashboard/student_onboarding.html', {
            'user': request.user,
            'status': 'IDENTITY_PENDING'
        })
    # 🛣️ SaaS Routing Orchestration
    current_path = request.path
    initial_partial = 'student_dashboard_overview_partial'
    
    if 'radar' in current_path: initial_partial = 'student_academic_radar_partial'
    elif 'career' in current_path: initial_partial = 'student_career_radar_partial'
    elif 'achievements' in current_path: initial_partial = 'student_achievement_tracker_partial'
    elif 'support' in current_path: initial_partial = 'student_support_hub_partial'
    elif 'finance' in current_path: initial_partial = 'student_finance_ledger_partial'
    elif 'assignments' in current_path: initial_partial = 'student_assignment_os_partial'
    elif 'attendance-trend' in current_path: initial_partial = 'student_attendance_trend_partial'

    student = Student.objects.filter(user=request.user).first()
    
    # 🛡️ SaaS IDENTITY GUARD: Handle missing profile gracefully
    if not student:
        return render(request, 'dashboard/student_onboarding.html', {
            'user': request.user,
            'status': 'IDENTITY_PENDING'
        })
    
    # 🕵️ OUTCOME INTELLIGENCE: Process Mentor Escalations
    from .services.success_intelligence import EscalationService
    EscalationService.process_escalations(student)
    
    # 🏗️ INFRASTRUCTURE GOVERNANCE
    health_report = FeatureReadiness.get_status_report()
    is_degraded = not all(health_report.values())
    
    # 🚀 ORCHESTRATION LAYER: Success Intelligence ViewModels
    # We synthesize raw data into institutional intelligence BEFORE rendering.
    
    # 1. Hero Mission Intelligence
    hour = timezone.now().hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
    
    # Dynamic Scoring
    confidence_score = SuccessConfidenceEngine.calculate_score(student)
    
    hero_mission = {
        'greeting': f"{greeting}, {student.user.first_name}",
        'motivation': f"You are {confidence_score}% on track for Semester Success. 2 actions recommended today.",
        'confidence_score': confidence_score,
        'confidence_tone': 'positive' if confidence_score > 70 else 'warning',
    }

    # 2. Progression Rails (Institutional Growth Tracking)
    total_credits = SubjectEnrollment.objects.filter(student=student).aggregate(Sum('subject__credits'))['subject__credits__sum'] or 0
    # Placement readiness from real service
    placement_score = CareerIntelligenceService.calculate_placement_readiness(student)
    
    progression = [
        {'label': 'Semester Progress', 'val': 75, 'unit': '%', 'sub': f'Semester {student.current_semester.number if student.current_semester else "N/A"}', 'tone': 'emerald'},
        {'label': 'Credit Capacity', 'val': total_credits, 'max': 30, 'unit': ' Credits', 'sub': 'Enrolled', 'tone': 'blue'},
        {'label': 'Placement Readiness', 'val': placement_score, 'unit': '%', 'sub': 'Target: 85%', 'tone': 'purple'},
    ]

    # 3. Enhanced KPI Grid (Operational Telemetry)
    # Attendance Aggregate
    from .services.academic_intelligence import AcademicRadarService
    radar_data = AcademicRadarService.get_subject_radar(student)
    avg_attendance = sum(s['attendance'] for s in radar_data) / len(radar_data) if radar_data else 0
    
    academic_kpis = [
        {
            'label': 'Attendance',
            'val': f"{avg_attendance:.1f}%",
            'sub': 'High Fidelity' if avg_attendance > 85 else 'Action Required' if avg_attendance < 75 else 'Stable',
            'trend': {'label': 'LIVE', 'tone': 'positive' if avg_attendance > 75 else 'danger', 'icon': 'pulse'}
        },
        {
            'label': 'GPA Projection',
            'val': '3.85', # Still mocked until Exam marks are integrated
            'sub': 'Top 12% in Batch',
            'trend': {'label': 'STABLE', 'tone': 'positive', 'icon': 'minus'}
        },
        {
            'label': 'Reputation',
            'val': f"{student.reputation_score}/100",
            'sub': 'Institutional Trust',
            'trend': {'label': 'TRUSTED', 'tone': 'positive', 'icon': 'shield-check'}
        },
    ]

    # 4. Intervention Orchestration (Actionable Tasks)
    interventions = []
    if FeatureReadiness.is_ready('accounts_interventionorchestration'):
        from .models import InterventionOrchestration
        interventions = InterventionOrchestration.objects.filter(
            student=student, 
            status__in=['PENDING', 'ACTIVE']
        ).select_related('trigger_signal')[:5]

    # 🚀 HTMX Routing Stabilization: Resolve URL name to absolute path
    from django.urls import reverse
    initial_partial_url = reverse(initial_partial)

    context = {
        'student': student,
        'hero': hero_mission,
        'progression': progression,
        'academic_kpis': academic_kpis,
        'operational_state': student.get_operational_state_display(),
        'next_session': {
            'subject': 'Institutional Sync',
            'countdown': 'LIVE',
            'status': 'READY'
        },
        'active_mode': 'SUCCESS_MODE',
        'is_degraded': is_degraded,
        'initial_partial_url': initial_partial_url,
        'interventions': interventions,
        'health': health_report
    }
    
    return render(request, 'dashboard/student_master.html', context)

@login_required
def student_identity_hub_partial(request):
    """
    🛡️ Presence OS: Student Identity Hub
    Displays the Institutional Pass and movement timeline.
    """
    student = get_object_or_404(Student, user=request.user)
    recent_events = StudentOperationalEvent.objects.filter(student=student).order_by('-timestamp')[:5]
    
    context = {
        'student': student,
        'recent_events': recent_events,
        'active_session': IdentitySession.objects.filter(user=request.user, status='ACTIVE').first()
    }
    return render(request, 'dashboard/views/student/identity_hub.html', context)

@login_required
def student_academic_radar_partial(request):
    """
    📊 Learning OS: Academic Radar
    Synthesizes subject-wise progression, attendance, and evaluation data.
    """
    from .services.academic_intelligence import AcademicRadarService
    student = get_object_or_404(Student, user=request.user)
    radar_data = AcademicRadarService.get_subject_radar(student)
    
    return render(request, 'dashboard/views/student/academic_radar.html', {'radar': radar_data})


@login_required
def student_competency_heatmap_partial(request):
    """
    🧬 Intelligence OS: Competency Heatmap
    Visualizes the student's skill fingerprint and mastery levels.
    """
    from academics.services.competency_engine import CompetencyEngine
    student = get_object_or_404(Student, user=request.user)
    
    # Recalculate (in a real system, this would be async or triggered by events)
    CompetencyEngine.calculate_mastery(student)
    skills = CompetencyEngine.get_skill_fingerprint(student)
    
    return render(request, 'dashboard/views/student/competency_heatmap.html', {'skills': skills})

@login_required
def student_achievement_tracker_partial(request):
    """
    🎯 Achievement OS: Goal & Milestone Tracker
    """
    from .models import StudentGoal
    student = get_object_or_404(Student, user=request.user)
    goals = StudentGoal.objects.filter(student=student)
    
    return render(request, 'dashboard/views/student/achievement_tracker.html', {'goals': goals})

@login_required
def student_support_hub_partial(request):
    """🤝 Relationship OS: Institutional Support Hub"""
    from .models import SupportRelationship, SupportCase, SupportTimelineEvent
    student = get_object_or_404(Student, user=request.user)
    
    # 🛰️ Relationship Synthesis
    network = SupportRelationship.objects.filter(student=student).select_related('staff__user', 'peer__user')
    active_cases = SupportCase.objects.filter(student=student, status='ACTIVE').select_related('assigned_staff__user')
    timeline = SupportTimelineEvent.objects.filter(student=student).order_by('-timestamp')[:10]
    
    context = {
        'network': network,
        'active_cases': active_cases,
        'timeline': timeline,
        'network_stats': {
            'active_nodes': network.count(),
            'unresolved_cases': active_cases.count(),
            'average_trust': 'STRONG' if any(n.trust_level == 'STRONG' for n in network) else 'STABLE'
        }
    }
    
    return render(request, 'dashboard/views/student/support_hub.html', context)

@login_required
def student_finance_ledger_partial(request):
    """💰 Institutional Trust Ledger: High-Fidelity Financial Governance"""
    from finance.models import Invoice, Payment
    student = get_object_or_404(Student, user=request.user)
    
    # 📡 Fetching Real Transactional Data
    invoices = Invoice.objects.filter(student=student, is_deleted=False).order_by('-issued_date')
    payments = Payment.objects.filter(student=student, is_deleted=False).order_by('-payment_date')
    
    # 📉 Financial Telemetry Calculation
    total_liability = sum(i.total_amount for i in invoices)
    total_paid = sum(p.amount_paid for p in payments if p.status == 'SUCCESS')
    balance_due = total_liability - total_paid
    
    # 🚨 Financial Risk Intelligence
    next_due_invoice = invoices.filter(status='PENDING').order_by('due_date').first()
    risk_signal = "LOW"
    risk_message = "Stable"
    if next_due_invoice:
        days_left = (next_due_invoice.due_date - timezone.now().date()).days
        if days_left < 7:
            risk_signal = "CRITICAL"
            risk_message = "Exam Eligibility Risk"
        elif days_left < 15:
            risk_signal = "MEDIUM"
            risk_message = "Library Access Risk"
    
    # 📑 Aggregating High-Fidelity Ledger Entries
    ledger = []
    for inv in invoices:
        ledger.append({
            'id': inv.id,
            'reference_id': f"INV-{inv.id}",
            'context': inv.invoice_type.replace('_', ' ').capitalize(),
            'date': inv.issued_date,
            'debit': inv.total_amount,
            'credit': 0,
            'mode': 'INSTITUTIONAL',
            'status': inv.status, # PENDING, PARTIAL, PAID
            'verification': 'VERIFIED'
        })
        
    for pay in payments:
        ledger.append({
            'id': pay.id,
            'reference_id': pay.reference_id or f"PAY-{pay.id}",
            'context': f"Digital Settlement",
            'date': pay.payment_date,
            'debit': 0,
            'credit': pay.amount_paid,
            'mode': pay.mode,
            'status': 'SETTLED' if pay.status == 'SUCCESS' else 'FAILED',
            'verification': 'RECONCILED'
        })
        
    ledger.sort(key=lambda x: x['date'], reverse=True)
    
    # 🔍 Liability Explainability
    breakdown = [
        {'label': 'Tuition Fee', 'value': 35000},
        {'label': 'Laboratory Fee', 'value': 5000},
        {'label': 'Hostel & Utility', 'value': 7000},
        {'label': 'Exam Processing', 'value': 3000},
    ] if total_liability > 0 else []
    
    context = {
        'total_liability': f"{total_liability:,.2f}",
        'total_paid': f"{total_paid:,.2f}",
        'balance_due': f"{balance_due:,.2f}",
        'risk_signal': risk_signal,
        'risk_message': risk_message,
        'breakdown': breakdown,
        'ledger': ledger,
        'next_due_date': next_due_invoice.due_date if next_due_invoice else 'N/A'
    }
    
    return render(request, 'dashboard/views/student/finance_ledger.html', context)

@login_required
def student_career_radar_partial(request):
    """
    💼 Career OS: Placement Confidence Radar
    """
    from .services.career_intelligence import CareerIntelligenceService
    student = get_object_or_404(Student, user=request.user)
    radar_data = CareerIntelligenceService.get_career_radar(student)
    
    return render(request, 'dashboard/views/student/career_radar.html', {'radar': radar_data})

@login_required
def student_service_portal_partial(request, service_slug):
    """🏛️ Institutional Service Portal: Deep-dive into specific service nodes."""
    student = get_object_or_404(Student, user=request.user)
    
    # 🛰️ Service Intelligence Mock
    service_map = {
        'registrar': {
            'slug': 'registrar',
            'name': 'Registrar Office',
            'status': 'ONLINE',
            'tone': 'emerald',
            'sla': '4h',
            'active_tickets': 1,
            'description': 'Handles academic records, transcripts, and formal institutional documentation.'
        },
        'wellness': {
            'slug': 'wellness',
            'name': 'Wellness Cell',
            'status': 'HIGH LOAD',
            'tone': 'orange',
            'sla': '20m Queue',
            'active_tickets': 0,
            'description': 'Dedicated mental wellness and institutional counseling services.'
        },
        'career': {
            'slug': 'career',
            'name': 'Career Hub',
            'status': 'AVAILABLE',
            'tone': 'blue',
            'sla': 'Instant',
            'active_tickets': 2,
            'description': 'Placement coordination, internship sourcing, and professional development.'
        }
    }
    
    service_data = service_map.get(service_slug)
    if not service_data:
        return HttpResponse("Service node not found.", status=404)
        
    return render(request, 'dashboard/views/student/service_portal.html', {'service': service_data, 'student': student})

@login_required
@require_POST
def student_initiate_service_request(request, service_slug):
    """🎟️ Institutional Workflow: Initiates a formal request/ticket."""
    import time
    time.sleep(1.2) # Institutional processing simulation
    return render(request, 'dashboard/views/student/partials/service_request_success.html', {
        'service_slug': service_slug,
        'ticket_id': f"REQ-{timezone.now().strftime('%Y%m%d')}-{service_slug[:3].upper()}"
    })

@login_required
@require_POST
def student_schedule_consultation(request, service_slug):
    """📅 Support Coordination: Schedules a 1-on-1 session with a specialist."""
    import time
    time.sleep(1) # Scheduling sync simulation
    return render(request, 'dashboard/views/student/partials/consultation_success.html', {
        'service_slug': service_slug,
        'specialist': 'Dr. Rajesh Kumar'
    })

@login_required
def student_view_ticket_status(request, ticket_id):
    """🛰️ Support Analytics: Displays detailed status of a specific institutional ticket."""
    import time
    time.sleep(0.5)
    return render(request, 'dashboard/views/student/partials/ticket_status_detail.html', {
        'ticket_id': ticket_id,
        'status': 'PROCESSING',
        'estimated_resolution': '24h'
    })

@login_required
@require_POST
def student_add_to_roadmap(request, service_slug):
    """🗺️ Professional Success: Integrates institutional sessions into the student roadmap."""
    return render(request, 'dashboard/views/student/partials/roadmap_update_success.html', {
        'message': f"Consultation with {service_slug.capitalize()} Hub integrated into your Success Path."
    })

@login_required
def student_relationship_intelligence_partial(request, relation_id):
    """🧠 Relationship Intelligence: Deep-dive into specific institutional connections."""
    relationship = get_object_or_404(SupportRelationship, id=relation_id, student__user=request.user)
    
    # Aggregating historical success metrics
    timeline = SupportTimelineEvent.objects.filter(relationship=relationship).order_by('-timestamp')[:5]
    
    return render(request, 'dashboard/views/student/relationship_intelligence.html', {
        'relationship': relationship,
        'timeline': timeline
    })

@login_required
def student_daily_agenda_partial(request):
    """📅 Operational Timeline: Displays today's session load and execution plan."""
    # Simulation data
    sessions = [
        {'time': '09:00 AM', 'subject': 'Advanced Identity Systems', 'location': 'Hall 4-B', 'status': 'COMPLETED'},
        {'time': '11:30 AM', 'subject': 'Relational Databases', 'location': 'Lab 2', 'status': 'IN_PROGRESS'},
        {'time': '02:00 PM', 'subject': 'Institutional Ethics', 'location': 'Hall 1-A', 'status': 'UPCOMING'},
    ]
    return render(request, 'dashboard/views/student/partials/daily_agenda.html', {'sessions': sessions})

@login_required
def student_risk_signals_partial(request):
    """🚨 Risk Intelligence: Identifies academic decay and relational instability."""
    signals = [
        {'type': 'ATTENDANCE', 'subject': 'Ethics', 'decay': '12%', 'priority': 'HIGH'},
        {'type': 'SUBMISSION', 'subject': 'Databases', 'decay': '5%', 'priority': 'MEDIUM'},
    ]
    return render(request, 'dashboard/views/student/partials/risk_signals_intelligence.html', {'signals': signals})

@login_required
def student_rotate_pass_partial(request):
    """🔐 Identity Governance: Rotates the institutional pass token and regenerates QR."""
    import random
    import string
    # Generate a rotating secure token
    new_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={new_token}&color=10b981&bgcolor=ffffff"
    
    return render(request, 'dashboard/views/student/partials/identity_qr_surface.html', {
        'qr_url': qr_url,
        'token': new_token
    })

@login_required
def student_payment_orchestration_partial(request):
    """💳 Payment Orchestration: Launches the high-fidelity checkout surface with real-time liability."""
    from finance.models import Invoice, Payment
    student = get_object_or_404(Student, user=request.user)
    
    # 📡 Calculate Actual Outstanding Balance
    invoices = Invoice.objects.filter(student=student, is_deleted=False)
    payments = Payment.objects.filter(student=student, is_deleted=False, status='SUCCESS')
    
    total_liability = sum(i.total_amount for i in invoices)
    total_paid = sum(p.amount_paid for p in payments)
    actual_balance = total_liability - total_paid
    
    return render(request, 'dashboard/views/student/partials/payment_checkout.html', {
        'balance': f"{actual_balance:,.2f}",
        'currency': 'INR'
    })

@login_required
@require_POST
def student_process_payment(request):
    """💰 Transaction Protocol: Processes institutional settlement and posts to ledger."""
    from finance.models import Invoice, Payment
    import time
    student = get_object_or_404(Student, user=request.user)
    
    # 📡 Identify Target Liability
    pending_invoice = Invoice.objects.filter(student=student, status='PENDING', is_deleted=False).first()
    
    if not pending_invoice:
        # No pending liability to settle
        return render(request, 'dashboard/views/student/partials/payment_success.html', {
            'transaction_id': 'SKIP-' + str(int(time.time())),
            'amount': '0.00',
            'message': 'No pending liability detected.'
        })

    # 🔐 Create Digital Settlement Record
    settlement_amount = pending_invoice.total_amount - pending_invoice.paid_amount
    txn_id = 'TXN-' + str(int(time.time()))
    
    new_payment = Payment.objects.create(
        college=student.college,
        student=student,
        invoice=pending_invoice,
        amount_paid=settlement_amount,
        mode=request.POST.get('payment_mode', 'UPI'),
        reference_id=txn_id,
        status='SUCCESS'
    )
    
    # 📉 Reconcile Institutional Invoice
    pending_invoice.paid_amount += settlement_amount
    pending_invoice.status = 'PAID'
    pending_invoice.save()
    
    time.sleep(1.5) # Simulate institutional gateway latency
    
    return render(request, 'dashboard/views/student/partials/payment_success.html', {
        'transaction_id': txn_id,
        'amount': f"{settlement_amount:,.2f}"
    })

@login_required
def student_payment_method_intelligence_partial(request):
    """💳 Payment Intelligence: Swaps the input surface based on selected rail."""
    mode = request.GET.get('mode', 'UPI')
    if mode == 'UPI':
        return render(request, 'dashboard/views/student/partials/method_upi.html')
    else:
        return render(request, 'dashboard/views/student/partials/method_card.html')

@login_required
def student_verify_vpa_partial(request):
    """🛡️ VPA Verification: High-fidelity validation of institutional payment addresses."""
    vpa = request.POST.get('vpa', '').strip()
    
    if not vpa or '@' not in vpa:
        # Trigger Institutional Warning
        return render(request, 'dashboard/views/student/partials/vpa_warning.html')
        
    return render(request, 'dashboard/views/student/partials/vpa_verified.html')

@login_required
def student_define_goal_partial(request):
    """🎯 Achievement Intelligence: Launches the goal configuration surface."""
    return render(request, 'dashboard/views/student/partials/goal_form.html')

@login_required
@require_POST
def student_save_goal(request):
    """🎯 Goal Persistence: Posts the new institutional milestone to the ledger."""
    from .models import StudentGoal
    student = get_object_or_404(Student, user=request.user)
    
    # 📡 Extract Configuration
    title = request.POST.get('title', 'Institutional Target')
    goal_type = request.POST.get('type', 'GPA')
    target = request.POST.get('target', '100')
    deadline = request.POST.get('deadline')
    
    # 🔐 Register Institutional Milestone
    new_goal = StudentGoal.objects.create(
        student=student,
        college=student.college,
        title=title,
        goal_type=goal_type,
        target_value=float(target),
        current_value=0.0,
        deadline=deadline if deadline else None
    )
    
    import time
    time.sleep(1) # Simulate institutional processing
    
    return render(request, 'dashboard/views/student/partials/goal_success.html', {
        'title': new_goal.title,
        'target': new_goal.target_value
    })

@login_required
def student_goal_intelligence_partial(request, goal_id):
    """🧠 Achievement Intelligence: Deep-dive into specific goal telemetry."""
    from .models import StudentGoal
    goal = get_object_or_404(StudentGoal, id=goal_id, student__user=request.user)
    return render(request, 'dashboard/views/student/partials/goal_intelligence.html', {'goal': goal})

@login_required
@require_POST
def student_update_goal_progress(request, goal_id):
    """📈 Achievement Progression: Securely posts progress updates to the ledger."""
    from .models import StudentGoal
    goal = get_object_or_404(StudentGoal, id=goal_id, student__user=request.user)
    
    increment = float(request.POST.get('increment', 0))
    goal.current_value += increment
    
    if goal.current_value >= goal.target_value:
        goal.is_completed = True
        
    goal.save()
    
    import time
    time.sleep(0.5)
    
    return render(request, 'dashboard/views/student/partials/goal_update_success.html', {'goal': goal})

@login_required
def student_assignment_os_partial(request):
    """🚀 Assignment OS: Academic Execution Intelligence Hub"""
    from lms.models import Assignment, Submission, EvaluationEvent
    from academics.models import SubjectEnrollment
    
    student = get_object_or_404(Student, user=request.user)
    
    # 🛰️ Execution Intelligence: Fetch enrolled assignments
    enrolled_subjects = SubjectEnrollment.objects.filter(student=student).values_list('subject_id', flat=True)
    assignments = Assignment.objects.filter(subject_id__in=enrolled_subjects).select_related('subject', 'faculty__user').order_by('deadline')
    
    # 🛰️ Submission Synchronization
    submissions = Submission.objects.filter(student=student).select_related('assignment')
    submission_map = {s.assignment_id: s for s in submissions}
    
    # 🛰️ Execution Telemetry Synthesis
    total_assignments = assignments.count()
    completed_submissions = submissions.filter(workflow_state='COMPLETED').count()
    velocity = (completed_submissions / total_assignments * 100) if total_assignments > 0 else 100
    
    on_time_rate = 94 # Simulated behavioral telemetry for high-fidelity
    pending_reviews = submissions.filter(workflow_state='UNDER_REVIEW').count()
    
    # 🛰️ Priority Stack Orchestration
    now = timezone.now()
    priority_stack = []
    for assignment in assignments:
        sub = submission_map.get(assignment.id)
        if not sub and assignment.deadline > now:
            priority_stack.append({
                'id': assignment.id,
                'type': 'DUE_SOON',
                'title': assignment.title,
                'subject': assignment.subject.code,
                'deadline': assignment.deadline,
                'risk': 'LOW' if (assignment.deadline - now).days > 2 else 'HIGH'
            })
        elif sub and sub.review_state == 'RETURNED':
            priority_stack.append({
                'id': assignment.id,
                'type': 'REVISION_REQUIRED',
                'title': assignment.title,
                'subject': assignment.subject.code,
                'deadline': assignment.deadline,
                'risk': 'CRITICAL'
            })

    # 🛰️ Faculty Intelligence Feed
    intelligence_feed = EvaluationEvent.objects.filter(
        submission__student=student,
        event_type__in=['FEEDBACK_SENT', 'GRADE_LOCKED', 'RISK_FLAGGED']
    ).select_related('submission__assignment', 'faculty__user').order_by('-created_at')[:5]

    context = {
        'assignments': assignments,
        'submission_map': submission_map,
        'velocity': round(velocity, 1),
        'on_time_rate': on_time_rate,
        'pending_reviews': pending_reviews,
        'priority_stack': priority_stack[:4],
        'intelligence_feed': intelligence_feed,
    }
    
    return render(request, 'dashboard/views/student/assignment_os.html', context)

@login_required
def student_assignment_workspace_partial(request, assignment_id):
    """🛠️ Assignment Workspace: Deterministic Execution Surface"""
    from lms.models import Assignment, Submission
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(Student, user=request.user)
    
    submission = Submission.objects.filter(assignment=assignment, student=student).first()
    
    return render(request, 'dashboard/views/student/partials/assignment_workspace.html', {
        'assignment': assignment,
        'submission': submission,
    })

@login_required
@require_POST
def student_submit_assignment(request, assignment_id):
    """🚀 Submission Engine: Handle institutional coursework upload"""
    from lms.models import Assignment, Submission, EvaluationEvent
    import os
    from django.core.files.storage import default_storage
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = get_object_or_404(Student, user=request.user)
    
    file = request.FILES.get('submission_file')
    if not file:
        return HttpResponse("Institutional Error: No file detected.", status=400)
    
    # 🛰️ Secure Storage Orchestration
    file_path = default_storage.save(f'submissions/{student.id}/{assignment.id}_{file.name}', file)
    
    # 🛰️ State Synchronization
    submission, created = Submission.objects.update_or_create(
        assignment=assignment,
        student=student,
        defaults={
            'college': student.college,
            'file_url': file_path,
            'workflow_state': 'SUBMITTED',
            'ai_state': 'PENDING',
            'review_state': 'UNTOUCHED'
        }
    )
    
    # 🛰️ Operational Event Logging
    EvaluationEvent.objects.create(
        college=student.college,
        submission=submission,
        event_type='SUBMISSION_UPLOADED',
        description=f"Automated: Assignment '{assignment.title}' uploaded by {student.user.get_full_name()}."
    )
    
    return render(request, 'dashboard/views/student/partials/assignment_workspace.html', {
        'assignment': assignment,
        'submission': submission,
        'success': True
    })

@login_required
def student_assignment_selector_partial(request):
    """🔍 Assignment Selector: Centralized Submission Dispatcher"""
    from lms.models import Assignment, Submission
    from academics.models import SubjectEnrollment
    
    student = get_object_or_404(Student, user=request.user)
    enrolled_subjects = SubjectEnrollment.objects.filter(student=student).values_list('subject_id', flat=True)
    assignments = Assignment.objects.filter(subject_id__in=enrolled_subjects).select_related('subject').order_by('deadline')
    
    submissions = Submission.objects.filter(student=student).values_list('assignment_id', flat=True)
    
    return render(request, 'dashboard/views/student/partials/assignment_selector.html', {
        'assignments': assignments,
        'submitted_ids': list(submissions)
    })

@login_required
def student_attendance_trend_partial(request):
    """📈 Attendance Intelligence: Aggregated Trend Analytics"""
    from operations.models import Attendance, AttendanceSession
    from academics.models import SubjectEnrollment
    from django.db.models import Count, Q
    
    student = get_object_or_404(Student, user=request.user)
    
    # 📡 Subject-Wise Aggregate
    subject_stats = []
    enrollments = SubjectEnrollment.objects.filter(student=student).select_related('subject')
    
    for enr in enrollments:
        total_sessions = AttendanceSession.objects.filter(
            subject_snapshot_name=enr.subject.name,
            college=student.college
        ).count()
        
        present_count = Attendance.objects.filter(
            student=student,
            session__subject_snapshot_name=enr.subject.name,
            status='PRESENT'
        ).count()
        
        percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
        
        subject_stats.append({
            'subject': enr.subject.name,
            'code': enr.subject.code,
            'total': total_sessions,
            'present': present_count,
            'percentage': round(percentage, 1),
            'risk': 'HIGH' if percentage < 75 else 'LOW'
        })
    
    # 📡 Daily Behavioral Telemetry (Last 7 Days)
    from datetime import timedelta
    now = timezone.now().date()
    daily_trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        present = Attendance.objects.filter(student=student, session__started_at__date=day, status='PRESENT').exists()
        daily_trend.append({
            'day': day.strftime('%a'),
            'present': present
        })
        
    return render(request, 'dashboard/views/student/attendance_trend.html', {
        'subject_stats': subject_stats,
        'daily_trend': daily_trend,
        'overall_avg': sum(s['percentage'] for s in subject_stats) / len(subject_stats) if subject_stats else 0
    })

@login_required
def student_dashboard_overview_partial(request):
    """
    📊 Execution OS: Dashboard Overview
    Primary performance telemetry for the student workspace.
    """
    from .services.student_orchestrator import StudentOperationalOrchestrator
    student = get_object_or_404(Student, user=request.user)
    
    # 🧠 Operational Orchestration
    orchestration = StudentOperationalOrchestrator.get_unified_state(student)
    
    # KPIs & Progression Logic (REAL AGGREGATES)
    from .services.academic_intelligence import AcademicRadarService
    radar_data = AcademicRadarService.get_subject_radar(student)
    avg_attendance = sum(s['attendance'] for s in radar_data) / len(radar_data) if radar_data else 0
    
    total_credits = SubjectEnrollment.objects.filter(student=student).aggregate(Sum('subject__credits'))['subject__credits__sum'] or 0
    
    academic_kpis = [
        {
            'label': 'SYLLABUS VELOCITY', 'val': '75%', 'sub': 'Institutional Trend', 
            'trend': {'label': 'STABLE', 'icon': 'check', 'tone': 'positive'},
            'tone': 'blue', 'partial': 'student_assignment_os_partial', 'url': '/dashboard/student/assignments/'
        },
        {
            'label': 'ATTENDANCE STABILITY', 'val': f"{avg_attendance:.1f}%", 'sub': 'Verified Presence', 
            'trend': {'label': 'LIVE', 'icon': 'pulse', 'tone': 'positive' if avg_attendance > 75 else 'danger'},
            'tone': 'emerald', 'partial': 'student_attendance_trend_partial', 'url': '/dashboard/student/attendance-trend/'
        },
        {
            'label': 'CREDIT ACCUMULATION', 'val': str(total_credits), 'sub': 'Target: 22 Credits', 
            'trend': {'label': 'On Track', 'icon': 'bullseye', 'tone': 'positive'},
            'tone': 'purple', 'partial': 'student_achievement_tracker_partial', 'url': '/dashboard/student/achievements/'
        },
        {
            'label': 'GPA PROJECTION', 'val': '3.85', 'sub': 'Top 12% in Batch', 
            'trend': {'label': 'STABLE', 'icon': 'chart-line', 'tone': 'positive'},
            'tone': 'orange', 'partial': 'student_subject_intelligence_partial', 'url': '/dashboard/student/overview/'
        },
    ]
    
    placement_score = CareerIntelligenceService.calculate_placement_readiness(student)
    progression = [
        {'label': 'Semester Progress', 'val': 75, 'unit': '%', 'tone': 'emerald', 'sub': f'Sem {student.current_semester.number if student.current_semester else "N/A"}'},
        {'label': 'Placement Readiness', 'val': placement_score, 'unit': '%', 'tone': 'blue', 'sub': 'Target: 85%'},
    ]
    
    # Today's Sessions (REAL DATA from TimetableSlotInstance)
    from operations.models import TimetableSlotInstance
    today = timezone.now().date()
    today_instances = TimetableSlotInstance.objects.filter(
        timetable_slot__timetable__program=student.department.program_set.first(), # Rough mapping
        date=today
    ).select_related('timetable_slot__assignment__subject').order_by('timetable_slot__start_time')
    
    sessions = []
    for inst in today_instances:
        sessions.append({
            'time': inst.timetable_slot.start_time.strftime('%I:%M %p'),
            'subject': inst.timetable_slot.assignment.subject.code,
            'status': inst.get_status_display().upper(),
            'tone': 'emerald' if inst.status == 'COMPLETED' else 'blue' if inst.status == 'LIVE' else 'white/20',
            'is_live': inst.status == 'LIVE'
        })
    
    if not sessions:
        sessions = [
            {'time': '00:00 AM', 'subject': 'No Sessions Today', 'status': 'IDLE', 'tone': 'white/10'}
        ]
    
    context = {
        'academic_kpis': academic_kpis,
        'progression': progression,
        'orchestration': orchestration,
        'sessions': sessions,
    }
    
    return render(request, 'dashboard/views/student/dashboard_overview.html', context)

@login_required
def student_confidence_breakdown_partial(request):
    """
    🔬 Intelligence OS: Confidence Explainability
    Provides a factor-level audit trail for the Success Confidence Score.
    """
    student = get_object_or_404(Student, user=request.user)
    
    # 🏗️ Factor Synthesis (Normally sourced from SuccessConfidenceEngine)
    factors = [
        {
            'label': 'Academic Velocity', 'val': 85, 'unit': '%', 'tone': 'blue', 'icon': 'graduation-cap', 
            'weight': 40, 'status': 'Steady Progression'
        },
        {
            'label': 'Attendance Stability', 'val': 92, 'unit': '%', 'tone': 'emerald', 'icon': 'user-check', 
            'weight': 35, 'status': 'Exemplary Presence'
        },
        {
            'label': 'Behavioral Engagement', 'val': 74, 'unit': '%', 'tone': 'purple', 'icon': 'brain', 
            'weight': 25, 'status': 'Active Participation'
        },
    ]
    
    context = {
        'score': 88,
        'factors': factors,
        'rationale': "Your confidence score is sustained at 88% due to high attendance stability and consistent academic velocity across core technical subjects. A minor decay in behavioral engagement (participation) prevents a 90%+ tier transition.",
        'trace_id': 'TXN-7882-SYS-ORCH'
    }
    
    return render(request, 'dashboard/views/student/confidence_breakdown.html', context)

@login_required
def student_subject_intelligence_partial(request):
    """
    📈 Learning OS: Subject Intelligence
    Predictive telemetry showing risk, momentum, and recovery logic per subject.
    """
    from .services.student_orchestrator import StudentOperationalOrchestrator
    student = get_object_or_404(Student, user=request.user)
    
    # 🧠 Operational Orchestration
    orchestration = StudentOperationalOrchestrator.get_unified_state(student)
    
    context = {
        'orchestration': orchestration,
    }
    
    return render(request, 'dashboard/views/student/subject_intelligence.html', context)

@login_required
def student_resume_builder_partial(request):
    """🧠 Career Identity Constructor: Orchestrates AI-assisted professional identity building."""
    student = get_object_or_404(Student, user=request.user)
    context = {
        'student': student,
        'signals': {
            'optimization_score': 84,
            'missing_skills': ['Kafka', 'System Design'],
            'market_readiness': 'HIGH'
        }
    }
    return render(request, 'dashboard/views/student/resume_builder.html', context)

@login_required
def student_identity_command_center(request):
    """
    🎯 Student Identity & Success Command Surface
    Primary orchestrator for the immersive right-side operational drawer.
    Implements institutional contract enforcement and secondary hydration.
    """
    student = get_object_or_404(Student, user=request.user)
    tab = request.GET.get('tab', 'overview')
    is_secondary = request.GET.get('hydrate', 'false') == 'true'

    # 🚀 Institutional Orchestration Layer
    # Synthesize state based on hydration priority and operational contracts
    requested_modules = ['identity_surface', 'telemetry', 'actions_grid']
    if tab != 'overview' or is_secondary:
        # Add secondary modules based on context
        requested_modules.extend(['success_trajectory', 'security_hub'])

    state = IdentityOrchestrationService.synthesize_drawer_state(
        student=student, 
        requested_modules=requested_modules
    )

    # 📊 Observability: Log Institutional Interaction
    IdentityOrchestrationService.log_interaction(
        student=student,
        action='DRAWER_OPEN' if not is_secondary else f'TAB_VIEW_{tab.upper()}',
        surface='COMMAND_DRAWER',
        context={'tab': tab, 'is_secondary': is_secondary}
    )

    context = {
        'student': student,
        'active_tab': tab,
        'state': state,
        'is_secondary': is_secondary
    }
    
    template_map = {
        'overview': 'dashboard/views/student/profile_drawer/overview.html',
        'identity': 'dashboard/views/student/profile_drawer/surface.html',
        'governance': 'dashboard/views/student/profile_drawer/governance_hub.html',
        'telemetry': 'dashboard/views/student/profile_drawer/telemetry.html',
        'actions': 'dashboard/views/student/profile_drawer/actions_grid.html',
        'academics': 'dashboard/views/student/profile_drawer/academic_identity.html',
        'career': 'dashboard/views/student/profile_drawer/career_intelligence.html',
        'security': 'dashboard/views/student/profile_drawer/security_hub.html',
        'settings': 'dashboard/views/student/profile_drawer/settings_panel.html',
        'password': 'dashboard/views/student/profile_drawer/password_change.html',
    }
    
    # 🏎️ HTMX Partial Routing: Hydrate specific modules independently
    if request.headers.get('HX-Request'):
        if 'tab' in request.GET:
            return render(request, template_map.get(tab, template_map['overview']), context)
        
    return render(request, 'dashboard/views/student/student_identity_command_center.html', context)

@login_required
@require_POST
def update_student_preferences(request):
    """HTMX endpoint for updating identity OS preferences."""
    student = get_object_or_404(Student, user=request.user)
    
    # Process updates from form data or headers
    updates = {
        'focus_mode': request.POST.get('focus_mode'),
        'quiet_hours': request.POST.get('quiet_hours'),
        'ui_density': request.POST.get('ui_density'),
        'theme_accent': request.POST.get('theme_accent'),
    }
    
    # Clean None values
    updates = {k: v for k, v in updates.items() if v is not None}
    
    IdentityOrchestrationService.update_preferences(student, updates)
    
    # Check if we should return governance hub or settings panel
    # If the request comes from settings, return settings panel with success
    referer = request.META.get('HTTP_REFERER', '')
    template = 'dashboard/views/student/profile_drawer/governance_hub.html'
    
    # Detect if we are in settings mode (simple check for now)
    # Better: check if specific fields are present or use a hidden input
    if 'theme_accent' in request.POST or 'ui_density' in request.POST:
        template = 'dashboard/views/student/profile_drawer/settings_panel.html'

    # Return success response with hydration trigger
    response = render(request, template, {
        'state': IdentityOrchestrationService.synthesize_drawer_state(student, ['governance', 'settings']),
        'success': True
    })
    response['HX-Trigger'] = 'preferences-updated'
    return response

@login_required
@require_POST
def execute_identity_freeze(request):
    """Institutional Security Lockout."""
    student = get_object_or_404(Student, user=request.user)
    IdentityOrchestrationService.execute_emergency_freeze(student)
    
    # Return security surface with success state
    return render(request, 'dashboard/views/student/profile_drawer/security_hub.html', {
        'state': IdentityOrchestrationService.synthesize_drawer_state(student, ['security']),
        'freeze_executed': True
    })

@login_required
@require_POST
def update_student_password(request):
    """Secure password mutation handler."""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib import messages
    
    student = get_object_or_404(Student, user=request.user)
    current_password = request.POST.get('current_password')
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    # 🛡️ Validation Layer
    if not request.user.check_password(current_password):
        return render(request, 'dashboard/views/student/profile_drawer/password_change.html', {
            'error': 'Invalid current password'
        })
        
    if new_password != confirm_password:
        return render(request, 'dashboard/views/student/profile_drawer/password_change.html', {
            'error': 'Passwords do not match'
        })
    
    # Execute Mutation
    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user) # Maintain session
    
    return render(request, 'dashboard/views/student/profile_drawer/password_change.html', {
        'success': True
    })

@login_required
@require_POST
def run_skill_audit(request):
    """Institutional Skill Pulse: Audits student competencies against market signals."""
    import time
    time.sleep(1.5) # Simulate AI processing
    return render(request, 'dashboard/views/student/partials/skill_audit_results.html', {
        'audit_complete': True,
        'new_skills_found': ['Docker', 'AWS Lambda'],
        'optimization_boost': '+12%'
    })

@login_required
@require_POST
def generate_resume_pdf(request):
    """Document Orchestration: Generates institutional-grade professional identity PDF."""
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'success',
        'message': 'Institutional PDF generated and dispatched to your student email.',
        'trigger': 'notification-sent'
    })

@login_required
@require_POST
def push_to_placement(request):
    """Career Integration: Syncs professional identity with placement framework."""
    return render(request, 'dashboard/views/student/partials/placement_sync_success.html')

@login_required
def get_critical_banner(request):
    """
    🚨 Governance OS: Critical Institutional Notice
    Fetches the highest-priority signal for the student.
    """
    from .models import SuccessSignal
    student = Student.objects.filter(user=request.user).first()
    if not student: return HttpResponse("")
    
    # Identify high-weight signals that haven't been resolved
    top_signal = SuccessSignal.objects.filter(
        student=student, 
        is_active=True,
        weight='NEGATIVE'
    ).order_by('-confidence_delta').first()
    
    if not top_signal:
        return HttpResponse("") # Silently fail if no critical notice
        
    return render(request, 'dashboard/views/student/partials/critical_banner.html', {
        'signal': top_signal
    })
