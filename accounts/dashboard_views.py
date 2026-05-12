from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
import json
from django.contrib.auth.decorators import login_required
from academics.models import Department, Program, Semester, Subject
from academics.forms import DepartmentForm, ProgramForm, SemesterForm, SubjectForm
from accounts.services import overview_analytics, academics_analytics
from lms.models import Assignment, Submission, EvaluationEvent
from lms.services.evaluation_os.orchestrator import EvaluationOrchestrator
from lms.services.evaluation_os.fraud_engine import FraudEngine
from lms.services.evaluation_os.productivity_engine import ProductivityEngine
from operations.models import TimetableSlotInstance, AttendanceSession
from operations.services.attendance_os.session_orchestrator import AttendanceSessionOrchestrator
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction, IntegrityError
from django.db.models import Count, Q, Avg, F
from accounts.models import User, Student, Guardian, Address, Faculty, IdentitySession, ScanTerminal, IdentityScanEvent, PresencePolicy
from accounts.forms import StudentOnboardingForm, FacultyOnboardingForm
from operations.models import Timetable, TimetableSlot
from accounts.services.faculty_analytics import (
    get_faculty_core_stats, get_chart_faculty_distribution, get_chart_faculty_designation
)

@login_required
def admin_dashboard(request):
    """ Shell template that loads the full dashboard layout (Sidebar, Topbar) """
    # Permission Check: Only Staff, Superuser, or Admin role
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.userrole_set.filter(role__name='Admin').exists()
    
    if not is_admin:
        # Redirect students to their dashboard
        if Student.objects.filter(user=request.user).exists():
            return redirect('student_dashboard')
        # Faculty to theirs
        if Faculty.objects.filter(user=request.user).exists():
            return redirect('faculty_dashboard')
        return HttpResponse("Unauthorized", status=403)

    context = {
        'college': request.college,
        'user': request.user,
        'college_name': request.college.name if request.college else "System Admin",
        'user_role': "Administrator",
        'username': request.user.get_full_name() or request.user.username,
        'initial_load_url': None
    }
    
    # 🛣️ SaaS Deep-Linking Orchestration
    path = request.path
    from django.urls import reverse
    if 'academics' in path: context['initial_load_url'] = reverse('admin_academics_partial')
    elif 'students' in path: context['initial_load_url'] = reverse('admin_students_partial')
    elif 'faculty' in path: context['initial_load_url'] = reverse('admin_faculty_partial')
    elif 'finance' in path: context['initial_load_url'] = reverse('admin_finance_partial')
    elif 'timetable' in path: context['initial_load_url'] = reverse('admin_timetable_management')
    else: context['initial_load_url'] = reverse('admin_overview_partial')

    return render(request, 'dashboard/admin_master.html', context)

# [DEPRECATED] Student dashboard moved to student_dashboard_views.py

def _get_faculty_or_404(request):
    """ Helper to get faculty with tenant awareness or return 404 with context """
    if not request.college:
        # If college is missing in request, try to get it from user
        request.college = getattr(request.user, 'college', None)
        
    faculty = Faculty.objects.filter(user=request.user, college=request.college).first()
    if not faculty:
        # Last resort: find ANY faculty profile for this user
        faculty = Faculty.objects.filter(user=request.user).first()
        if faculty:
            print(f"WARNING: Faculty found but college mismatch. User college: {request.college}, Faculty college: {faculty.college}")
            return faculty
            
        # Role mismatch detection
        if Student.objects.filter(user=request.user).exists():
            raise Http404(f"PERMISSION_DENIED: Student {request.user} attempting to access Faculty intelligence layer.")
            
        raise Http404(f"Faculty profile not found for user {request.user} in college {request.college}")
    return faculty

@login_required
def faculty_dashboard(request):
    """ Shell for Faculty Dashboard """
    # 🛡️ Role-Based Redirect Engine
    faculty = Faculty.objects.filter(user=request.user).first()
    if not faculty:
        # If user is a student, redirect them to student dashboard
        if Student.objects.filter(user=request.user).exists():
            return redirect('student_dashboard')
        # If admin, stay in admin or show error
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        
        return render(request, 'dashboard/student_onboarding.html', {
            'user': request.user,
            'status': 'IDENTITY_PENDING'
        })

    context = {
        'college': request.college,
        'user': request.user,
        'user_role': "Faculty",
        'username': request.user.get_full_name() or request.user.username,
        'initial_load_url': None
    }

    # 🛣️ SaaS Deep-Linking Orchestration
    path = request.path
    from django.urls import reverse
    if 'performance' in path: context['initial_load_url'] = reverse('faculty_performance_partial')
    elif 'attendance' in path: context['initial_load_url'] = reverse('faculty_attendance_dashboard')
    elif 'timetable' in path: context['initial_load_url'] = reverse('admin_timetable_management')
    elif 'assignments' in path: context['initial_load_url'] = reverse('faculty_assignment_review_hub')
    elif 'finance' in path: context['initial_load_url'] = reverse('faculty_earnings_partial')
    else: context['initial_load_url'] = reverse('faculty_overview_partial')

    return render(request, 'dashboard/faculty_master.html', context)

@login_required
def faculty_identity_hub_partial(request):
    """ HTMX partial to load the Identity Hub (Dropdown) """
    from accounts.services.faculty_context_service import FacultyContextService
    
    # Use robust lookup helper
    faculty = _get_faculty_or_404(request)

    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/partials/faculty_identity_dropdown.html', {'hub': context_data})

@login_required
def faculty_profile_dashboard_partial(request):
    """ The Core Shell for the Faculty Intelligence Dashboard """
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/faculty_profile.html', {'hub': context_data})

@login_required
def faculty_profile_kpi_partial(request):
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/profile_partials/faculty_kpi_partial.html', {'hub': context_data})

@login_required
def faculty_profile_analytics_partial(request):
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/profile_partials/faculty_analytics_partial.html', {'hub': context_data})

@login_required
def faculty_profile_insights_partial(request):
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/profile_partials/faculty_insights_partial.html', {'hub': context_data})

@login_required
def faculty_profile_activity_partial(request):
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/profile_partials/faculty_activity_partial.html', {'hub': context_data})

@login_required
def faculty_profile_settings_partial(request):
    from accounts.services.faculty_context_service import FacultyContextService
    faculty = _get_faculty_or_404(request)
    context_data = FacultyContextService.get_context(faculty, request.college)
    return render(request, 'dashboard/views/faculty/profile_partials/faculty_settings_partial.html', {'hub': context_data})



from operations.utils import QRGenerator

@login_required
def get_attendance_qr(request):
    """ API to generate a fresh secure QR payload for the logged-in user """
    payload = QRGenerator.generate_student_payload(request.user)
    return JsonResponse({'qr_data': payload})

@login_required
def admin_overview_partial(request):
    """ Returns the Overview Command Center Shell """
    context = {
        'college_name': request.college.name if request.college else "System Admin",
        'signals': overview_analytics.get_insight_signals(request.college)
    }
    return render(request, 'dashboard/views/admin_overview.html', context)

@login_required
def admin_overview_hero_partial(request):
    """ Returns Row 1: Hero KPIs """
    college = request.college
    context = {
        'core': overview_analytics.get_core_kpis(college),
        'finance': overview_analytics.get_financial_kpis(college),
        'risk': overview_analytics.get_risk_signals(college),
        'health_score': overview_analytics.get_system_health_score(college),
    }
    return render(request, 'dashboard/partials/overview/hero_stats.html', context)

@login_required
def admin_overview_analytics_partial(request):
    """ Returns Row 2: Trends & Financial Snapshot """
    college = request.college
    context = {
        'trends': overview_analytics.get_growth_trends(college),
        'finance': overview_analytics.get_financial_kpis(college)
    }
    return render(request, 'dashboard/partials/overview/analytics_charts.html', context)

@login_required
def admin_overview_distribution_partial(request):
    """ Returns Row 3: Distributions (Dept/Sem) """
    stats = overview_analytics.get_distribution_stats(request.college)
    return render(request, 'dashboard/partials/overview/distribution_charts.html', stats)

@login_required
def admin_overview_intelligence_partial(request):
    college = request.user.college
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    # Convert to int if present
    year = int(year) if year else None
    month = int(month) if month else None
    
    context = {
        'timeline': overview_analytics.get_timeline_events(college),
        'health_score': overview_analytics.get_system_health_score(college),
        'calendar': overview_analytics.get_calendar_matrix(year=year, month=month),
    }
    return render(request, 'dashboard/partials/overview/intelligence_engine.html', context)
    
@login_required
def admin_overview_insights_partial(request):
    """ Returns Row 5: Decision Layer (Success & Skills) """
    college = request.college
    context = {
        'success': overview_analytics.get_success_intelligence(college),
        'skills': overview_analytics.get_skill_intelligence(college)
    }
    return render(request, 'dashboard/partials/overview/decision_insights.html', context)

@login_required
def admin_day_intelligence_partial(request):
    """ Returns a drawer content for a specific day's events """
    day = request.GET.get('day')
    month_name = request.GET.get('month') # e.g. "May 2026"
    
    college = request.user.college
    all_events = overview_analytics.get_timeline_events(college)
    
    # Simple filter by day (assuming current view context)
    day_events = [e for e in all_events if str(e['day']) == str(day)]
    
    return render(request, 'dashboard/partials/overview/day_intelligence_drawer.html', {
        'day': day,
        'month_name': month_name,
        'events': day_events
    })

@login_required
def admin_overview_insights_partial(request):
    college = request.user.college
    context = {
        'insights': overview_analytics.get_insight_signals(college),
    }
    return render(request, 'dashboard/partials/overview/insights_signals.html', context)

@login_required
def admin_academics_partial(request):
    """ Returns the Academics Management module view (Shell with Tabs) """
    stats = academics_analytics.get_academics_core_stats(request.college)
    return render(request, 'dashboard/views/academics/academics_base.html', {'stats': stats})

@login_required
def admin_academics_stats_partial(request):
    """ Returns Row 0 (Insights) and Row 1 (KPIs) """
    part = request.GET.get('part', 'kpi')
    if part == 'insights':
        insights = academics_analytics.get_academics_insights(request.college)
        return render(request, 'dashboard/partials/academics/academics_insights.html', {'insights': insights})
    
    stats = academics_analytics.get_academics_core_stats(request.college)
    return render(request, 'dashboard/partials/academics/academics_kpis.html', {'stats': stats})

@login_required
def admin_academics_charts_partial(request):
    """ Returns Row 2 (Charts Layout) or Row 1 Summary """
    stats = academics_analytics.get_academics_core_stats(request.college)
    part = request.GET.get('part')
    
    if part == 'summary':
        return render(request, 'dashboard/partials/academics/academics_summary_panel.html', {'stats': stats})
        
    return render(request, 'dashboard/partials/academics/academics_charts.html', {'stats': stats})

@login_required
def admin_profile_partial(request):
    """ Returns the SaaS Admin Profile Dashboard """
    college = request.college
    user = request.user
    
    # Mock data for activity and health score for now
    context = {
        'user': user,
        'college': college,
        'health_score': 85,
        'completion': 92,
        'last_login': user.last_login or timezone.now(),
        'activity_count': 124,
        'permissions': [
            {'name': 'Students', 'access': True},
            {'name': 'Faculty', 'access': True},
            {'name': 'Finance', 'access': True},
            {'name': 'Academics', 'access': True},
            {'name': 'System Settings', 'access': True},
        ]
    }
    return render(request, 'dashboard/views/admin_profile.html', context)

@login_required
def admin_profile_edit_partial(request):
    """ Returns the Identity Management Panel (Edit Profile) """
    if request.method == 'POST':
        # Logic to save profile changes would go here
        return HttpResponse('<script>showToast("Profile updated successfully", "success"); closeSidePanel();</script>')
    
    context = {
        'user': request.user,
        'college': request.college,
        'completion': 92,
    }
    return render(request, 'dashboard/partials/profile/edit_profile.html', context)

@login_required
def admin_password_change_partial(request):
    """ Returns the Security Workflow (Change Password) """
    if request.method == 'POST':
        # Logic to change password would go here
        return HttpResponse('<script>showToast("Password updated successfully", "success"); closeSidePanel();</script>')
    
    return render(request, 'dashboard/partials/profile/change_password.html')

@login_required
def admin_tenant_switch_partial(request):
    """ Returns the Multi-Tenant Control System """
    colleges = Department.objects.filter(college=request.college).values('name') # Mocking other tenants for now
    context = {
        'current_college': request.college,
        'tenants': [
            {'name': 'Main Campus HQ', 'id': '1', 'current': True},
            {'name': 'Engineering Campus', 'id': '2', 'current': False},
            {'name': 'Medical Campus', 'id': '3', 'current': False},
        ]
    }
    return render(request, 'dashboard/partials/profile/switch_tenant.html', context)

@login_required
def admin_sessions_partial(request):
    """ Returns the Session Intelligence Panel """
    context = {
        'sessions': [
            {'device': 'Windows PC — Chrome', 'ip': '192.168.1.1', 'loc': 'India', 'current': True, 'time': 'Now'},
            {'device': 'Android — Chrome', 'ip': '192.168.1.5', 'loc': 'India', 'current': False, 'time': '2 hours ago'},
        ]
    }
    return render(request, 'dashboard/partials/profile/active_sessions.html', context)

@login_required
def admin_academics_chart_data(request):
    """ JSON Endpoint for Chart.js """
    depts = Department.objects.filter(college=request.college).annotate(s_count=Count('student'))
    labels = [d.name for d in depts]
    counts = [d.s_count for d in depts]
    return JsonResponse({'labels': labels, 'data': counts})

@login_required
def admin_departments_partial(request):
    """ Upgraded Smart Table with sorting and filtering """
    filter_type = request.GET.get('filter')
    sort_by = request.GET.get('sort', 'name')
    
    departments = academics_analytics.get_smart_departments_list(
        request.college, 
        filter_type=filter_type, 
        sort_by=sort_by
    )
    return render(request, 'dashboard/views/academics/departments_table.html', {
        'departments': departments,
        'current_sort': sort_by,
        'current_filter': filter_type
    })

@login_required
def admin_department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.college = request.college
            department.save()
            departments = Department.objects.filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_departments.html', {'departments': departments})
    else:
        form = DepartmentForm()
    return render(request, 'dashboard/partials/modals/department_form.html', {'form': form})

@login_required
def admin_department_edit(request, dept_id):
    department = get_object_or_404(Department, id=dept_id, college=request.college)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            departments = academics_analytics.get_smart_departments_list(request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_departments.html', {'departments': departments})
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'dashboard/partials/modals/department_form.html', {'form': form, 'edit': True, 'department': department})

@login_required
def admin_department_delete(request, dept_id):
    department = get_object_or_404(Department, id=dept_id, college=request.college)
    if request.method == 'POST':
        department.hard_delete()
        departments = academics_analytics.get_smart_departments_list(request.college)
        return render(request, 'dashboard/partials/modals/close_and_update_departments.html', {'departments': departments})
    return render(request, 'dashboard/partials/modals/delete_confirmation.html', {
        'object': department,
        'delete_url': reverse('admin_department_delete', args=[dept_id]),
        'target': '#modal-container'
    })

@login_required
def admin_department_view(request, dept_id):
    department = get_object_or_404(Department, id=dept_id, college=request.college)
    programs = Program.objects.filter(department=department)
    context = {
        'department': department,
        'programs': programs,
        'stats': academics_analytics.get_smart_departments_list(request.college, dept_id=dept_id)[0]
    }
    return render(request, 'dashboard/partials/modals/department_view.html', context)

@login_required
def admin_department_export(request, dept_id):
    import csv
    from django.http import HttpResponse
    department = get_object_or_404(Department, id=dept_id, college=request.college)
    programs = Program.objects.filter(department=department)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{department.code}_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Department', department.name, 'Code', department.code])
    writer.writerow([])
    writer.writerow(['Programs'])
    writer.writerow(['Name', 'Duration (Years)'])
    for p in programs:
        writer.writerow([p.name, p.duration_years])
        
    return response

@login_required
def admin_department_health_audit(request, dept_id):
    department = get_object_or_404(Department, id=dept_id, college=request.college)
    # Mocking some audit signals for now
    signals = [
        {'title': 'Faculty Ratio', 'status': 'Healthy', 'score': 92, 'icon': 'fa-user-tie'},
        {'title': 'Student Attendance', 'status': 'Medium', 'score': 74, 'icon': 'fa-clock'},
        {'title': 'Financial Efficiency', 'status': 'Healthy', 'score': 88, 'icon': 'fa-chart-pie'},
        {'title': 'Infrastructure Compliance', 'status': 'Weak', 'score': 45, 'icon': 'fa-building'},
    ]
    return render(request, 'dashboard/partials/modals/department_health_audit.html', {
        'department': department,
        'signals': signals
    })

@login_required
def admin_programs_partial(request):
    programs = Program.objects.select_related('department').filter(college=request.college)
    return render(request, 'dashboard/views/academics/programs_table.html', {'programs': programs})

@login_required
def admin_program_create(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid() and getattr(form.cleaned_data['department'], 'college', None) == request.college:
            program = form.save(commit=False)
            program.college = request.college
            program.save()
            programs = Program.objects.select_related('department').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_programs.html', {'programs': programs})
    else:
        form = ProgramForm()
        # Filter dropdown to only show current college's departments
        form.fields['department'].queryset = Department.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/program_form.html', {'form': form})

@login_required
def admin_program_edit(request, program_id):
    program = get_object_or_404(Program, id=program_id, college=request.college)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            programs = Program.objects.select_related('department').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_programs.html', {'programs': programs})
    else:
        form = ProgramForm(instance=program)
        form.fields['department'].queryset = Department.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/program_form.html', {'form': form, 'edit': True, 'program': program})

@login_required
def admin_program_delete(request, program_id):
    program = get_object_or_404(Program, id=program_id, college=request.college)
    if request.method == 'POST':
        program.hard_delete()
        programs = Program.objects.select_related('department').filter(college=request.college)
        return render(request, 'dashboard/partials/modals/close_and_update_programs.html', {'programs': programs})
    return render(request, 'dashboard/partials/modals/delete_confirmation.html', {
        'object': program,
        'delete_url': reverse('admin_program_delete', args=[program_id]),
        'target': '#modal-container'
    })

@login_required
def admin_semesters_partial(request):
    semesters = Semester.objects.select_related('program').filter(college=request.college)
    return render(request, 'dashboard/views/academics/semesters_table.html', {'semesters': semesters})

@login_required
def admin_semester_create(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save(commit=False)
            semester.college = request.college
            semester.save()
            semesters = Semester.objects.select_related('program').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_semesters.html', {'semesters': semesters})
    else:
        form = SemesterForm()
        form.fields['program'].queryset = Program.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/semester_form.html', {'form': form})

@login_required
def admin_semester_edit(request, semester_id):
    semester = Semester.objects.get(id=semester_id, college=request.college)
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            form.save()
            semesters = Semester.objects.select_related('program').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_semesters.html', {'semesters': semesters})
    else:
        form = SemesterForm(instance=semester)
        form.fields['program'].queryset = Program.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/semester_form.html', {'form': form, 'edit': True, 'semester': semester})

@login_required
def admin_semester_delete(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id, college=request.college)
    if request.method == 'POST':
        semester.hard_delete()
        semesters = Semester.objects.select_related('program').filter(college=request.college)
        return render(request, 'dashboard/partials/modals/close_and_update_semesters.html', {'semesters': semesters})
    return render(request, 'dashboard/partials/modals/delete_confirmation.html', {
        'object': semester,
        'delete_url': reverse('admin_semester_delete', args=[semester_id]),
        'target': '#modal-container'
    })

@login_required
def admin_subjects_partial(request):
    subjects = Subject.objects.select_related('semester__program').filter(college=request.college)
    return render(request, 'dashboard/views/academics/subjects_table.html', {'subjects': subjects})

@login_required
def admin_subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.college = request.college
            subject.save()
            subjects = Subject.objects.select_related('semester__program').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_subjects.html', {'subjects': subjects})
    else:
        form = SubjectForm()
        form.fields['semester'].queryset = Semester.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/subject_form.html', {'form': form})

@login_required
def admin_subject_edit(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, college=request.college)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            subjects = Subject.objects.select_related('semester__program').filter(college=request.college)
            return render(request, 'dashboard/partials/modals/close_and_update_subjects.html', {'subjects': subjects})
    else:
        form = SubjectForm(instance=subject)
        form.fields['semester'].queryset = Semester.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/subject_form.html', {'form': form, 'edit': True, 'subject': subject})

@login_required
def admin_subject_delete(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, college=request.college)
    if request.method == 'POST':
        subject.hard_delete()
        subjects = Subject.objects.select_related('semester__program').filter(college=request.college)
        return render(request, 'dashboard/partials/modals/close_and_update_subjects.html', {'subjects': subjects})
    return render(request, 'dashboard/partials/modals/delete_confirmation.html', {
        'object': subject,
        'delete_url': reverse('admin_subject_delete', args=[subject_id]),
        'target': '#modal-container'
    })

from accounts.models import Student, Guardian, Address
from accounts.forms import StudentOnboardingForm
from django.contrib.auth import get_user_model

from django.db.models import Q
from django.core.paginator import Paginator

User = get_user_model()

from django.shortcuts import redirect

from accounts.services.student_analytics import (
    get_student_core_stats, get_chart_enrollment_trend, 
    get_chart_department, get_chart_semester, get_chart_finance
)
from django.http import JsonResponse
from finance.models import Invoice
from django.db.models import Exists, OuterRef

@login_required
def admin_students_stats_partial(request):
    """ Returns the Elite SaaS Student Intelligence Cards (Pollable) """
    stats = get_student_core_stats(request.college)
    return render(request, 'dashboard/partials/students/stat_cards.html', {'stats': stats})

@login_required
def admin_students_charts_partial(request):
    """ Returns the Elite SaaS Student Intelligence Charts (Load once) """
    return render(request, 'dashboard/partials/students/charts_grid.html')

@login_required
def admin_students_chart_enrollment(request):
    time_filter = request.GET.get('time_filter', '6m')
    return JsonResponse(get_chart_enrollment_trend(request.college, time_filter))

@login_required
def admin_students_chart_department(request):
    return JsonResponse(get_chart_department(request.college))

@login_required
def admin_students_chart_semester(request):
    return JsonResponse(get_chart_semester(request.college))

@login_required
def admin_students_chart_finance(request):
    return JsonResponse(get_chart_finance(request.college))

@login_required
def admin_students_partial(request):
    """ Returns the Students Management module view with advanced filtering and drill-downs """
    if not request.headers.get('HX-Request'):
        return redirect('admin_dashboard')

    try:
        # 1. Capture Query Parameters
        search = request.GET.get('search', '').strip()
        dept = request.GET.get('dept')
        sem = request.GET.get('sem')
        year = request.GET.get('year')
        sort = request.GET.get('sort', 'name')
        order = request.GET.get('order', 'asc')
        page_number = request.GET.get('page', 1)
        
        # Elite SaaS Drill-Down Filters
        financial_filter = request.GET.get('financial')

        # 2. Base Queryset with Optimization
        queryset = Student.objects.select_related('user', 'department', 'current_semester').filter(college=request.college, is_deleted=False)

        # 3. Apply Multi-Field Search
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(enrollment_no__icontains=search)
            )

        # 4. Apply Academic Filters
        if dept and dept != 'all':
            queryset = queryset.filter(department_id=dept)
        
        if sem and sem != 'all':
            try:
                queryset = queryset.filter(current_semester_id=sem)
            except: pass

        if year and year != 'all':
            try:
                queryset = queryset.filter(admission_year=int(year))
            except: pass

        # Apply Drill-Down Financial Filters via Exists (Elite Perf)
        if financial_filter == 'dues':
            unpaid = Invoice.objects.filter(student=OuterRef('pk'), status__in=['PENDING', 'PARTIAL', 'OVERDUE'], is_deleted=False)
            queryset = queryset.filter(Exists(unpaid))
        elif financial_filter == 'advance':
            queryset = queryset.filter(credit_balance__gt=0)

        # 5. Secure Dynamic Sorting
        ALLOWED_SORT_FIELDS = {
            "name": "user__first_name",
            "enrollment": "enrollment_no",
            "semester": "current_semester__number",
            "year": "admission_year",
            "dept": "department__name"
        }
        sort_field = ALLOWED_SORT_FIELDS.get(sort, "user__first_name")
        if order == 'desc':
            sort_field = f"-{sort_field}"
        
        queryset = queryset.order_by(sort_field)

        # 6. Pagination & Context
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)

        departments = Department.objects.filter(college=request.college)
        semesters = Semester.objects.filter(college=request.college).order_by('number')

        context = {
            'students': page_obj,
            'page_obj': page_obj,
            'departments': departments,
            'semesters': semesters,
            'current_filters': {
                'search': search or '',
                'dept': dept or 'all',
                'sem': sem or 'all',
                'year': year or '',
                'sort': sort or 'name',
                'order': order or 'asc',
                'financial': financial_filter or ''
            }
        }
        
        # 7. Handle HTMX Partial Updates
        if request.headers.get('HX-Request') and request.headers.get('HX-Target') == 'students-content':
            return render(request, 'dashboard/views/students_table.html', context)
        
        return render(request, 'dashboard/views/admin_students.html', context)
    except Exception as e:
        import traceback
        return HttpResponse(f"<pre>{traceback.format_exc()}</pre>")

@login_required
def admin_student_create(request):
    if request.method == 'POST':
        form = StudentOnboardingForm(request.POST, college=request.college)
        if form.is_valid():
            try:
                from django.db import transaction
                from django.db import IntegrityError
                
                # 0. Proactive Collision Check (Prevent IntegrityError 500)
                email = form.cleaned_data['email']
                enrollment_no = form.cleaned_data['enrollment_no']
                
                if User.all_objects.filter(email=email, college=request.college).exists():
                    error_msg = f"A user with email {email} already exists in this institution (including deleted records)."
                    return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'error_message': error_msg}, status=400)
                
                # Check User username uniqueness since enrollment_no becomes username
                if User.all_objects.filter(username=enrollment_no).exists():
                    error_msg = f"The generated ID {enrollment_no} conflicts with an existing system record. Please close the form and try again to regenerate."
                    return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'error_message': error_msg}, status=400)

                if Student.all_objects.filter(enrollment_no=enrollment_no).exists():
                    error_msg = f"Enrollment Number {enrollment_no} is already assigned. Please close the form and try again."
                    return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'error_message': error_msg}, status=400)

                with transaction.atomic():
                    # 1. Create User
                    username = enrollment_no # using enrollment_no as username
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password="Changeme123!"
                    )
                    user.college = request.college
                    user.save()
                    
                    # 2. Create Student profile
                    student = Student.objects.create(
                        college=request.college,
                        user=user,
                        enrollment_no=enrollment_no,
                        department=form.cleaned_data['department'],
                        current_semester=form.cleaned_data['current_semester'],
                        admission_year=form.cleaned_data['admission_year'],
                        phone_no=form.cleaned_data['phone_no']
                    )
                    
                    # 3. Create Guardian
                    Guardian.objects.create(
                        college=request.college,
                        student=student,
                        name=form.cleaned_data['guardian_name'],
                        relation=form.cleaned_data['guardian_relation'],
                        phone=form.cleaned_data['guardian_phone'],
                        email=form.cleaned_data['guardian_email']
                    )

                    # 4. Create Address
                    Address.objects.create(
                        college=request.college,
                        user=user,
                        address_line1=form.cleaned_data['address_line1'],
                        city=form.cleaned_data['city'],
                        state=form.cleaned_data['state'],
                        pincode=form.cleaned_data['pincode']
                    )
                
                students = Student.objects.select_related('user', 'department', 'current_semester').filter(college=request.college)
                return render(request, 'dashboard/partials/modals/close_and_update_students.html', {'students': students})
            except Exception as e:
                import traceback
                print(traceback.format_exc()) # Log to console for debugging
                error_msg = f"An unexpected error occurred: {str(e)}"
                return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'error_message': error_msg}, status=500)
        else:
            return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'error_message': "Please correct the invalid fields and try again."}, status=400)
    else:
        year = timezone.now().year
        # Use all_objects to count so soft-deleted students don't cause ID reuse
        count = Student.all_objects.filter(college=request.college, admission_year=year).count() + 1
        generated_enrollment = f"STU-{year}-{count:03d}"
        
        form = StudentOnboardingForm(
            college=request.college,
            initial={
                'enrollment_no': generated_enrollment,
                'admission_year': year
            }
        )
    return render(request, 'dashboard/partials/modals/student_form.html', {'form': form})

@login_required
def admin_student_edit(request, student_id):
    student = get_object_or_404(Student, id=student_id, college=request.college)
    user = student.user
    guardian = student.guardians.first() # Student has 1-to-1 or 1-to-many? Looking at create, it's 1-to-1 logic
    address = user.addresses.first()

    if request.method == 'POST':
        form = StudentOnboardingForm(request.POST, college=request.college)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update User
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.save()

                    # Update Student
                    student.department = form.cleaned_data['department']
                    student.current_semester = form.cleaned_data['current_semester']
                    student.admission_year = form.cleaned_data['admission_year']
                    student.phone_no = form.cleaned_data['phone_no']
                    student.save()

                    # Update/Create Guardian
                    if guardian:
                        guardian.name = form.cleaned_data['guardian_name']
                        guardian.relation = form.cleaned_data['guardian_relation']
                        guardian.phone = form.cleaned_data['guardian_phone']
                        guardian.email = form.cleaned_data['guardian_email']
                        guardian.save()
                    else:
                        Guardian.objects.create(
                            college=request.college,
                            student=student,
                            name=form.cleaned_data['guardian_name'],
                            relation=form.cleaned_data['guardian_relation'],
                            phone=form.cleaned_data['guardian_phone'],
                            email=form.cleaned_data['guardian_email']
                        )

                    # Update/Create Address
                    if address:
                        address.address_line1 = form.cleaned_data['address_line1']
                        address.city = form.cleaned_data['city']
                        address.state = form.cleaned_data['state']
                        address.pincode = form.cleaned_data['pincode']
                        address.save()
                    else:
                        Address.objects.create(
                            college=request.college,
                            user=user,
                            address_line1=form.cleaned_data['address_line1'],
                            city=form.cleaned_data['city'],
                            state=form.cleaned_data['state'],
                            pincode=form.cleaned_data['pincode']
                        )
                
                students = Student.objects.select_related('user', 'department', 'current_semester').filter(college=request.college)
                return render(request, 'dashboard/partials/modals/close_and_update_students.html', {'students': students})
            except Exception as e:
                import traceback
                return HttpResponse(f"<pre>{traceback.format_exc()}</pre>")
    else:
        initial_data = {
            'enrollment_no': student.enrollment_no,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_no': student.phone_no,
            'department': student.department,
            'current_semester': student.current_semester,
            'admission_year': student.admission_year,
        }
        if guardian:
            initial_data.update({
                'guardian_name': guardian.name,
                'guardian_relation': guardian.relation,
                'guardian_phone': guardian.phone,
                'guardian_email': guardian.email,
            })
        if address:
            initial_data.update({
                'address_line1': address.address_line1,
                'city': address.city,
                'state': address.state,
                'pincode': address.pincode,
            })
        
        form = StudentOnboardingForm(college=request.college, initial=initial_data)
        # Enrollment No should be read-only in edit mode
        form.fields['enrollment_no'].widget.attrs['readonly'] = True
    
    return render(request, 'dashboard/partials/modals/student_form.html', {'form': form, 'edit': True, 'student': student})

@login_required
def admin_student_delete(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(Student, id=student_id, college=request.college)
        user = student.user
        # All-or-nothing delete
        try:
            from finance.models import LedgerEntry
            with transaction.atomic():
                # 1. Explicitly clear financial footprints that might be floating (like LedgerEntries with UUID references)
                # LedgerEntries for this student's invoices/payments should be purged to keep institutional totals clean
                LedgerEntry.objects.filter(college=request.college, reference_id__in=student.invoice_set.values_list('id', flat=True)).delete()
                LedgerEntry.objects.filter(college=request.college, reference_id__in=student.payment_set.values_list('id', flat=True)).delete()
                
                # 2. Delete main profiles (Cascades to Invoices, Payments via models.py)
                student.delete()
                user.delete() 
        except Exception as e:
            pass
            
        students = Student.objects.select_related('user', 'department', 'current_semester').filter(college=request.college)
        return render(request, 'dashboard/views/students_table.html', {'students': students})

from academics.models import Semester
@login_required
def get_semesters_for_program(request):
    dept_id = request.GET.get('department')
    semesters = Semester.objects.filter(program__department_id=dept_id) if dept_id else Semester.objects.none()
    return render(request, 'dashboard/partials/modals/semester_options.html', {'semesters': semesters})



@login_required
def admin_faculty_partial(request):
    """ Returns the Elite SaaS Faculty Intelligence module view """
    if not request.headers.get('HX-Request'):
        return redirect('admin_dashboard')
    return render(request, 'dashboard/views/admin_faculty.html')

@login_required
def admin_faculty_stats_partial(request):
    """ Elite Faculty Intelligence Cards (Polling every 30s) """
    stats = get_faculty_core_stats(request.college)
    part = request.GET.get('part')
    return render(request, 'dashboard/partials/faculty/stat_cards.html', {
        'stats': stats, 
        'part': part
    })

@login_required
def admin_faculty_charts_partial(request):
    """ Elite Faculty Intelligence Charts (Loaded Once) """
    return render(request, 'dashboard/partials/faculty/charts_grid.html')

@login_required
def admin_faculty_chart_dept(request):
    from .services.faculty_analytics import get_chart_faculty_distribution
    return JsonResponse(get_chart_faculty_distribution(request.college))

@login_required
def admin_faculty_chart_desig(request):
    from .services.faculty_analytics import get_chart_faculty_designation
    return JsonResponse(get_chart_faculty_designation(request.college))

from django.urls import reverse

@login_required
def admin_faculty_directory_partial(request):
    """ Returns the Faculty Directory table with advanced filtering and drill-downs """
    if not request.headers.get('HX-Request'):
        return redirect('admin_dashboard')

    try:
        # 1. Capture Query Parameters
        search = request.GET.get('search', '').strip()
        dept = request.GET.get('dept')
        sort = request.GET.get('sort', 'name')
        order = request.GET.get('order', 'asc')
        page_number = request.GET.get('page', 1)
        smart_filter = request.GET.get('filter') # For drill-downs

        # 2. Base Queryset
        queryset = Faculty.objects.select_related('user', 'department').filter(college=request.college)

        # 3. Apply Multi-Field Search
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(phone_no__icontains=search)
            )

        # 4. Apply Department Filter
        if dept and dept != 'all':
            queryset = queryset.filter(department_id=dept)

        # 5. Apply Smart Drill-Down Filters (from Stat Cards)
        if smart_filter:
            now = timezone.now()
            seven_days_ago = now - timedelta(days=7)
            
            if smart_filter == 'new_joiner':
                queryset = queryset.filter(created_at__gte=seven_days_ago)
            
            elif smart_filter == 'idle':
                # No timetable entries + created > 7 days ago
                assigned_faculty_ids = TimetableSlot.objects.filter(timetable__college=request.college).values_list('assignment__faculty_id', flat=True).distinct()
                queryset = queryset.filter(created_at__lt=seven_days_ago).exclude(id__in=assigned_faculty_ids)
                
            elif smart_filter == 'overloaded':
                # Compute hours for all faculty, then filter ORM by ID
                # This is an intensive operation but ensures perfect accuracy for SQLite
                timetable_entries = TimetableSlot.objects.filter(timetable__college=request.college).values('assignment__faculty_id', 'start_time', 'end_time')
                faculty_hours = {}
                dummy_date = datetime.today()
                
                for entry in timetable_entries:
                    fac_id = entry['assignment__faculty_id']
                    start = datetime.combine(dummy_date, entry['start_time'])
                    end = datetime.combine(dummy_date, entry['end_time'])
                    if end < start: end += timedelta(days=1)
                    duration = (end - start).total_seconds() / 3600.0
                    faculty_hours[fac_id] = faculty_hours.get(fac_id, 0) + duration
                    
                overloaded_ids = [fac_id for fac_id, hours in faculty_hours.items() if hours > 24]
                queryset = queryset.filter(id__in=overloaded_ids)

        # 6. Secure Dynamic Sorting
        ALLOWED_SORT_FIELDS = {
            "name": "user__first_name",
            "dept": "department__name",
            "designation": "designation",
            "status": "is_active"
        }
        sort_field = ALLOWED_SORT_FIELDS.get(sort, "user__first_name")
        if order == 'desc':
            sort_field = f"-{sort_field}"
        
        queryset = queryset.order_by(sort_field)

        # 7. Pagination & Context
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page_number)
        departments = Department.objects.filter(college=request.college)

        context = {
            'faculty': page_obj,
            'page_obj': page_obj,
            'departments': departments,
            'current_filters': {
                'search': search or '',
                'dept': dept or 'all',
                'sort': sort or 'name',
                'order': order or 'asc',
                'smart_filter': smart_filter or ''
            }
        }

        # 8. Handle HTMX Partial Updates
        # 8. Handle HTMX Partial Updates (Inject button into module header via OOB)
        if request.headers.get('HX-Target') == 'faculty-tab-content':
            create_url = reverse('admin_faculty_create')
            button_oob = f"""
            <div id="faculty-actions" hx-swap-oob="true">
                <button class="add-btn-elite" hx-get="{create_url}" hx-target="#modal-container">
                    <span class="plus-icon">+</span> Add Faculty
                </button>
            </div>
            """
            table_response = render(request, 'dashboard/views/faculty_table.html', context)
            
            # We NO LONGER OOB-swap the insights strip because the Intelligence Engine is global
            full_response = table_response.content.decode() + button_oob
            return HttpResponse(full_response)

        return render(request, 'dashboard/views/faculty_table.html', context)
    except Exception as e:
        import traceback
        return HttpResponse(f"<pre>{traceback.format_exc()}</pre>")



@login_required
def admin_workload_partial(request):
    """ Returns the Faculty Workload table grouped by Faculty (Accordion Style) """
    from accounts.models import Faculty
    from django.db.models import Prefetch
    from operations.models import TimetableSlot
    from datetime import datetime, date

    # 1. Fetch all faculty who have active timetable assignments
    faculties = Faculty.objects.filter(
        college=request.college,
        subjectassignment__timetableslot__timetable__college=request.college,
        subjectassignment__timetableslot__is_active=True
    ).select_related('user', 'department').distinct().order_by('user__first_name')

    workload_data = []
    for f in faculties:
        slots = TimetableSlot.objects.select_related(
            'assignment__subject',
            'room'
        ).filter(
            assignment__faculty=f,
            timetable__college=request.college,
            is_active=True
        ).order_by('day_of_week', 'start_time')

        # Calculate Total Weekly Hours
        total_minutes = 0
        for s in slots:
            start_dt = datetime.combine(date.min, s.start_time)
            end_dt = datetime.combine(date.min, s.end_time)
            total_minutes += (end_dt - start_dt).total_seconds() / 60
        
        hours = total_minutes // 60
        mins = int(total_minutes % 60)

        workload_data.append({
            'faculty': f,
            'slots': slots,
            'weekly_hours': f"{int(hours)}h {mins}m" if mins > 0 else f"{int(hours)}h",
            'slot_count': slots.count()
        })
    
    # Sort workload_data by department name for the template regroup to work correctly
    workload_data.sort(key=lambda x: x['faculty'].department.name)

    response = render(request, 'dashboard/views/faculty/workload_table.html', {
        'workload_data': workload_data
    })
    
    assign_url = reverse('admin_workload_create')
    button_oob = f"""
    <div class="module-actions" id="faculty-actions" hx-swap-oob="true">
        <button class="btn btn-primary" hx-get="{assign_url}" hx-target="#modal-container">
            <span class="icon">+</span> Assign Workload
        </button>
    </div>
    """
    return HttpResponse(response.content.decode() + button_oob)

from operations.forms import WorkloadForm

@login_required
def admin_workload_create(request):
    if request.method == 'POST':
        form = WorkloadForm(request.POST, college=request.college)
        if form.is_valid():
            form.save()
            
            workload_list = TimetableSlot.objects.select_related(
                'assignment__faculty__user', 
                'assignment__subject',
                'timetable__program',
                'timetable__semester'
            ).filter(timetable__college=request.college, is_active=True)
            return render(request, 'dashboard/partials/modals/close_and_update_workload.html', {'workload': workload_list})
    else:
        form = WorkloadForm(college=request.college)
    return render(request, 'dashboard/partials/modals/workload_form.html', {'form': form})

@login_required
def admin_faculty_create(request):
    if request.method == 'POST':
        form = FacultyOnboardingForm(request.POST, college=request.college)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Create User
                    email = form.cleaned_data['email']
                    username = email # using email as username
                    
                    # Hard-delete any existing user with this username (even soft-deleted ones)
                    # to prevent IntegrityError on the UNIQUE constraint.
                    User.all_objects.filter(username=username).delete()

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password="Faculty123!"
                    )
                    user.college = request.college
                    user.save()
                    
                    # 2. Create Faculty profile
                    faculty = Faculty.objects.create(
                        college=request.college,
                        user=user,
                        department=form.cleaned_data['department'],
                        designation=form.cleaned_data['designation'],
                        phone_no=form.cleaned_data['phone_no']
                    )

                    # 3. Create Address
                    Address.objects.create(
                        college=request.college,
                        user=user,
                        address_line1=form.cleaned_data['address_line1'],
                        city=form.cleaned_data['city'],
                        state=form.cleaned_data['state'],
                        pincode=form.cleaned_data['pincode']
                    )
                    
                faculty_list = Faculty.objects.select_related('user', 'department').filter(college=request.college)
                return render(request, 'dashboard/partials/modals/close_and_update_faculty.html', {'faculty': faculty_list})
            except Exception as e:
                import traceback
                return HttpResponse(f"<pre>{traceback.format_exc()}</pre>")
    else:
        form = FacultyOnboardingForm(college=request.college)
    return render(request, 'dashboard/partials/modals/faculty_form.html', {'form': form})

from django.shortcuts import get_object_or_404

@login_required
def admin_faculty_edit(request, faculty_id):
    faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
    user = faculty.user
    address = user.addresses.first()

    if request.method == 'POST':
        form = FacultyOnboardingForm(request.POST, college=request.college)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update User
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.username = form.cleaned_data['email']
                    user.save()

                    # Update Faculty
                    faculty.department = form.cleaned_data['department']
                    faculty.designation = form.cleaned_data['designation']
                    faculty.phone_no = form.cleaned_data['phone_no']
                    faculty.save()

                    # Update Address
                    if address:
                        address.address_line1 = form.cleaned_data['address_line1']
                        address.city = form.cleaned_data['city']
                        address.state = form.cleaned_data['state']
                        address.pincode = form.cleaned_data['pincode']
                        address.save()
                    else:
                        Address.objects.create(
                            college=request.college,
                            user=user,
                            address_line1=form.cleaned_data['address_line1'],
                            city=form.cleaned_data['city'],
                            state=form.cleaned_data['state'],
                            pincode=form.cleaned_data['pincode']
                        )
                
                faculty_list = Faculty.objects.select_related('user', 'department').filter(college=request.college)
                return render(request, 'dashboard/partials/modals/close_and_update_faculty.html', {'faculty': faculty_list})
            except Exception as e:
                import traceback
                return HttpResponse(f"<pre>{traceback.format_exc()}</pre>")
    else:
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_no': faculty.phone_no,
            'department': faculty.department,
            'designation': faculty.designation,
        }
        if address:
            initial_data.update({
                'address_line1': address.address_line1,
                'city': address.city,
                'state': address.state,
                'pincode': address.pincode,
            })
        form = FacultyOnboardingForm(college=request.college, initial=initial_data)
    
    return render(request, 'dashboard/partials/modals/edit_faculty_form.html', {'form': form, 'faculty': faculty})

@login_required
def admin_faculty_delete(request, faculty_id):
    if request.method == 'POST':
        faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
        # Delete user and faculty from DB
        user = faculty.user
        faculty.delete()
        user.delete() # Soft delete user to keep history if needed, but faculty is hard deleted.
        
        faculty_list = Faculty.objects.select_related('user', 'department').filter(college=request.college)
        return render(request, 'dashboard/views/faculty_table.html', {'faculty': faculty_list})

@login_required
def admin_workload_edit(request, workload_id):
    from operations.models import TimetableSlot
    from operations.forms import WorkloadForm
    workload_entry = TimetableSlot.objects.get(id=workload_id, timetable__college=request.college)
    if request.method == 'POST':
        form = WorkloadForm(request.POST, instance=workload_entry, college=request.college)
        if form.is_valid():
            form.save()
            workload = TimetableSlot.objects.select_related(
                'assignment__faculty__user', 
                'assignment__subject',
                'timetable__program',
                'timetable__semester'
            ).filter(timetable__college=request.college, is_active=True)
            return render(request, 'dashboard/partials/modals/close_and_update_workload.html', {'workload': workload, 'edit': True})
    else:
        initial_data = {
            'faculty': workload_entry.assignment.faculty.id if workload_entry.assignment else None,
            'subject': workload_entry.assignment.subject.id if workload_entry.assignment else None,
            'semester': workload_entry.assignment.semester.id if workload_entry.assignment and workload_entry.assignment.semester else None,
        }
        form = WorkloadForm(instance=workload_entry, initial=initial_data, college=request.college)
    return render(request, 'dashboard/partials/modals/workload_form.html', {'form': form, 'edit': True, 'workload_entry': workload_entry})

@login_required
def admin_workload_delete(request, workload_id):
    from operations.models import TimetableSlot
    workload_entry = TimetableSlot.objects.get(id=workload_id, timetable__college=request.college)
    workload_entry.hard_delete()
    workload = TimetableSlot.objects.select_related(
        'assignment__faculty__user', 
        'assignment__subject',
        'timetable__program',
        'timetable__semester'
    ).filter(timetable__college=request.college, is_active=True)
    return render(request, 'dashboard/views/faculty/workload_table.html', {'workload': workload})

@login_required
def faculty_workload_detail_partial(request, workload_id):
    """ Read-only Intelligence Report for a Workload Assignment """
    from operations.models import TimetableSlot, TimetableSlotInstance
    slot = get_object_or_404(TimetableSlot, id=workload_id, timetable__college=request.college)
    
    # Fetch last known instance telemetry
    last_instance = TimetableSlotInstance.objects.filter(timetable_slot=slot).order_by('-date').first()
    
    # Calculate attendance percentage
    attendance_pct = 0
    if last_instance and last_instance.expected_students > 0:
        attendance_pct = int((last_instance.actual_students / last_instance.expected_students) * 100)
    
    return render(request, 'dashboard/views/faculty/workload_detail.html', {
        'slot': slot,
        'last_instance': last_instance,
        'attendance_pct': attendance_pct
    })

def faculty_overview_partial(request):
    """ Command Center: Living SaaS Dashboard Overview """
    from django.utils import timezone
    from datetime import timedelta
    from operations.models import ExecutionControl, TimetableSlotInstance, AttendanceSession, SubjectAssignment
    
    # 1. Fetch Faculty & College context
    faculty = _get_faculty_or_404(request)
    today = timezone.now().date()
    
    # 2. Get Today's Execution Control (Hero Session)
    execution = ExecutionControl.objects.filter(
        slot_instance__timetable_slot__assignment__faculty=faculty,
        scheduled_start__date=today
    ).select_related(
        'slot_instance__timetable_slot__assignment__subject',
        'slot_instance__timetable_slot__timetable__program',
        'slot_instance__timetable_slot__room'
    ).order_by('scheduled_start').first()
    
    # 3. Get Today's Full Schedule (Timeline)
    today_schedule = ExecutionControl.objects.filter(
        slot_instance__timetable_slot__assignment__faculty=faculty,
        scheduled_start__date=today
    ).select_related(
        'slot_instance__timetable_slot__assignment__subject',
        'slot_instance__timetable_slot__room'
    ).order_by('scheduled_start')
    
    # 4. Operational Metrics (Smart Insights)
    today_sessions_count = today_schedule.count()
    completed_sessions = today_schedule.filter(status='COMPLETED').count()
    
    # Completion Rate
    completion_rate = int((completed_sessions / today_sessions_count * 100)) if today_sessions_count > 0 else 0
    
    # Attendance Averages (Last 7 Days)
    seven_days_ago = today - timedelta(days=7)
    recent_sessions = AttendanceSession.objects.filter(
        session_owner=faculty,
        started_at__date__range=[seven_days_ago, today],
        status='COMPLETED'
    )
    
    avg_attendance = 0
    if recent_sessions.exists():
        total_p = sum(s.present_count for s in recent_sessions)
        total_e = sum(s.expected_count for s in recent_sessions)
        avg_attendance = int((total_p / total_e * 100)) if total_e > 0 else 0
        
    # Estimated Earnings
    est_earnings = completed_sessions * 800
    
    context = {
        'execution': execution,
        'today_schedule': today_schedule,
        'today_sessions_count': today_sessions_count,
        'completion_rate': completion_rate,
        'avg_attendance': avg_attendance,
        'est_earnings': f"{est_earnings:,}",
        'faculty': faculty
    }
    return render(request, 'dashboard/views/faculty/faculty_overview.html', context)

@login_required
def faculty_performance_partial(request):
    """ Intelligence: Faculty Performance & Metrics """
    from django.db.models import Avg, Count, F, Sum
    from django.db.models.functions import TruncDate
    from operations.models import FacultyWorklog, AttendanceSession, SubjectAssignment
    faculty = _get_faculty_or_404(request)
    
    import json

    # 1. Fetch Performance Metrics (Last 30 days)
    worklogs = FacultyWorklog.objects.filter(
        faculty=faculty,
        college=request.college
    ).order_by('-date')[:30]
    
    # 2. Subject-wise Analysis & KPIs
    subject_stats = AttendanceSession.objects.filter(
        session_owner=faculty,
        college=request.college,
        status='COMPLETED'
    ).values('subject_snapshot_name').annotate(
        avg_attendance=Avg(F('present_count') * 100.0 / F('expected_count')),
        session_count=Count('id')
    ).order_by('-avg_attendance')

    # Calculate Global KPIs
    avg_att_val = subject_stats.aggregate(global_avg=Avg('avg_attendance'))['global_avg'] or 0.0
    
    # Execution Rating: Ratio of completed sessions in last 30 days
    total_sessions_30d = FacultyWorklog.objects.filter(faculty=faculty, date__gte=timezone.now() - timezone.timedelta(days=30)).aggregate(Sum('total_sessions'))['total_sessions__sum'] or 0
    completed_sessions_30d = FacultyWorklog.objects.filter(faculty=faculty, date__gte=timezone.now() - timezone.timedelta(days=30)).aggregate(Sum('completed_sessions'))['completed_sessions__sum'] or 0
    execution_precision = (completed_sessions_30d / total_sessions_30d * 5.0) if total_sessions_30d > 0 else 5.0
    
    # Syllabus Progress: Mocked aggregate
    total_assignments = SubjectAssignment.objects.filter(faculty=faculty, is_active=True).count()
    total_delivered = AttendanceSession.objects.filter(session_owner=faculty, status='COMPLETED').count()
    syllabus_progress = min(round((total_delivered / (max(total_assignments, 1) * 40.0)) * 100, 1), 100.0)

    # 3. Chart 1: Daily Attendance Trend (Last 14 days)
    daily_attendance_data = AttendanceSession.objects.filter(
        session_owner=faculty,
        college=request.college,
        status='COMPLETED'
    ).annotate(
        session_date=TruncDate('started_at')
    ).values('session_date').annotate(
        avg_att=Avg(F('present_count') * 100.0 / F('expected_count'))
    ).order_by('session_date')[:14]
    
    chart_dates = [d['session_date'].strftime('%b %d') if d['session_date'] else '' for d in daily_attendance_data]
    chart_attendance = [round(float(d['avg_att'] or 0), 1) for d in daily_attendance_data]

    # 4. Chart 2: Subject Distribution
    donut_labels = [s['subject_snapshot_name'] for s in subject_stats]
    donut_data = [s['session_count'] for s in subject_stats]

    context = {
        'worklogs': worklogs,
        'subject_stats': subject_stats,
        'faculty': faculty,
        'chart_dates_json': json.dumps(chart_dates),
        'chart_attendance_json': json.dumps(chart_attendance),
        'donut_labels_json': json.dumps(donut_labels),
        'donut_data_json': json.dumps(donut_data),
        'kpi': {
            'attendance': round(avg_att_val, 1),
            'execution': round(execution_precision, 1),
            'syllabus': syllabus_progress,
            'engagement': round(avg_att_val * 1.05, 1) # Placeholder for complex engagement index
        }
    }
    return render(request, 'dashboard/views/faculty/performance_partial.html', context)

@login_required
def admin_timetable_management(request):
    """ Intelligence: Timetable Management Dashboard (High-Fidelity) """
    from operations.models import Timetable, TimetableSlot, Room, SubjectAssignment, TimetableSlotInstance
    from academics.models import Department, Semester, Program, Subject
    from accounts.models import Faculty
    from django.db.models import Count, Q
    
    college = request.college

    if request.method == 'POST':
        # 🛡️ Atomic Session Orchestration
        subject_id = request.POST.get('subject')
        faculty_id = request.POST.get('faculty')
        room_id = request.POST.get('room')
        day = request.POST.get('day')
        time_slot = request.POST.get('time')
        
        selected_timetable = Timetable.objects.filter(college=college, is_active=True).first()
        if not selected_timetable:
             return HttpResponse("Active Timetable Blueprint Not Found", status=404)
        
        with transaction.atomic():
            # 1. Resolve or Create SubjectAssignment
            subject = get_object_or_404(Subject, id=subject_id, college=college)
            faculty = get_object_or_404(Faculty, id=faculty_id, college=college)
            room = get_object_or_404(Room, id=room_id, college=college)
            
            assignment, created = SubjectAssignment.objects.get_or_create(
                subject=subject,
                faculty=faculty,
                college=college,
                defaults={'is_active': True}
            )
            
            # 2. Extract start/end time from slot string (e.g., "09:00 - 10:00")
            try:
                start_str, end_str = time_slot.split(' - ')
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
            except Exception as e:
                return HttpResponse(f"Invalid time slot format: {str(e)}", status=400)
            
            # 3. Create or Update TimetableSlot
            slot, _ = TimetableSlot.objects.update_or_create(
                timetable=selected_timetable,
                day_of_week=int(day),
                start_time=start_time,
                end_time=end_time,
                defaults={
                    'assignment': assignment,
                    'room': room,
                    'is_active': True,
                    'slot_type': 'LECTURE'
                }
            )
        
        # Inject Success Toast via OOB Swap
        toast_html = f"""
        <div id="toast-container" hx-swap-oob="beforeend">
            <div class="toast animate-fade-in">
                <div class="icon text-emerald-500"><i class="fas fa-check-circle"></i></div>
                <p>Slot Allocated: {subject.name} in {room.name}</p>
            </div>
        </div>
        """
        
        # Recursively call GET logic to get the refreshed partial
        request.method = 'GET'
        response = admin_timetable_management(request)
        if isinstance(response, HttpResponse):
            response.content = response.content + toast_html.encode()
        return response
    
    # 1. KPIs & Telemetry
    total_classes = TimetableSlot.objects.filter(timetable__college=college, is_active=True).count()
    active_periods = TimetableSlot.objects.filter(timetable__college=college, is_active=True).count() # Simplified
    total_faculty = Faculty.objects.filter(college=college).count()
    total_rooms = Room.objects.filter(college=college).count()
    live_classes = TimetableSlotInstance.objects.filter(timetable_slot__timetable__college=college, status='LIVE').count()
    
    # 2. Filter Data
    departments = Department.objects.filter(college=college)
    semesters = Semester.objects.filter(college=college)
    programs = Program.objects.filter(college=college)
    
    # 3. Weekly Grid Logic (Structure for a standard week 9 AM - 5 PM)
    time_slots = [
        "09:00 - 10:00", "10:00 - 11:00", "11:00 - 12:00",
        "12:00 - 01:00", "01:00 - 02:00", "02:00 - 03:00",
        "03:00 - 04:00", "04:00 - 05:00"
    ]
    days = [
        (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'),
        (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')
    ]
    
    # Fetch slots for a default/first timetable if none selected (simplified for now)
    selected_timetable = Timetable.objects.filter(college=college, is_active=True).first()
    slots_data = {}
    if selected_timetable:
        grid_slots = TimetableSlot.objects.filter(timetable=selected_timetable, is_active=True).select_related(
            'assignment__subject', 'assignment__faculty__user', 'room'
        )
        for slot in grid_slots:
            # Map hours to the format used in time_slots ("09:00 - 10:00")
            h_start = slot.start_time.hour
            h_end = slot.end_time.hour
            
            # Standardize to 12h format for the key to match time_slots list
            fs_h = h_start if h_start <= 12 else h_start - 12
            fe_h = h_end if h_end <= 12 else h_end - 12
            
            time_key = f"{fs_h:02d}:{slot.start_time.minute:02d} - {fe_h:02d}:{slot.end_time.minute:02d}"
            key = f"{slot.day_of_week}-{time_key}"
            slots_data[key] = slot

    context = {
        'kpi': {
            'total_classes': total_classes,
            'active_periods': active_periods,
            'total_faculty': total_faculty,
            'total_rooms': total_rooms,
            'live_classes': live_classes,
            'free_slots': 12 # Mocked
        },
        'departments': departments,
        'semesters': semesters,
        'programs': programs,
        'selected_timetable': selected_timetable,
        'time_slots': time_slots,
        'days': days,
        'slots_data': slots_data,
    }
    return render(request, 'dashboard/views/admin/timetable_management_partial.html', context)

@login_required
def admin_timetable_create(request):
    """ Action: Create a new Timetable Blueprint """
    from operations.forms import TimetableForm
    if request.method == 'POST':
        form = TimetableForm(request.POST, college=request.college)
        if form.is_valid():
            timetable = form.save(commit=False)
            timetable.college = request.college
            timetable.save()
            return admin_timetable_management(request) # Refresh dashboard
    else:
        form = TimetableForm(college=request.college)
    
    return render(request, 'dashboard/partials/modals/timetable_form.html', {'form': form})

@login_required
def admin_timetable_generate(request):
    """ Orchestration Workspace: High-Fidelity Timetable Generation """
    # Aggregate context for the workspace
    from academics.models import Department, Subject
    from accounts.models import Faculty
    from operations.models import Room
    
    context = {
        'departments': Department.objects.filter(college=request.college),
        'total_faculty': Faculty.objects.filter(college=request.college).count(),
        'total_rooms': Room.objects.filter(college=request.college).count(),
        'total_subjects': Subject.objects.filter(college=request.college).count(),
        'generation_strategies': [
            {'id': 'balanced', 'name': 'Balanced Distribution', 'icon': 'fa-scale-balanced', 'desc': 'Uniform load across faculty and rooms.'},
            {'id': 'faculty', 'name': 'Faculty Optimization', 'icon': 'fa-user-tie', 'desc': 'Prioritize faculty work-life balance.'},
            {'id': 'student', 'name': 'Student Centric', 'icon': 'fa-graduation-cap', 'desc': 'Minimize gaps and maximize engagement.'},
            {'id': 'infrastructure', 'name': 'Resource Efficient', 'icon': 'fa-building', 'desc': 'Maximum utilization of specialized labs.'}
        ]
    }
    return render(request, 'dashboard/views/admin/timetable_orchestration_drawer.html', context)

@login_required
def admin_timetable_export(request):
    """ Action: Export Timetable (PDF/Excel) """
    # Placeholder for export logic
    from django.http import HttpResponse
    return HttpResponse("Timetable Export Engine Initialized. Processing document...")

@login_required
def admin_timetable_import(request):
    """ Action: Import Timetable from Template """
    # Placeholder for import modal
    return render(request, 'dashboard/partials/modals/timetable_import_modal.html')

# 📊 [ INTELLIGENCE DRILL-DOWN VIEWS ]

@login_required
def admin_timetable_class_directory(request):
    """ Drill-down: Comprehensive Class Directory """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Class Directory Matrix',
        'subtitle': 'Detailed distribution of academic sessions across departments.',
        'icon': 'fa-book-open',
        'color': 'purple'
    })

@login_required
def admin_timetable_utilization(request):
    """ Drill-down: Infrastructure Utilization Intelligence """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Utilization Intelligence',
        'subtitle': 'Real-time analysis of period allocation and peak usage.',
        'icon': 'fa-clock',
        'color': 'blue'
    })

@login_required
def admin_timetable_faculty_availability(request):
    """ Drill-down: Faculty Synchronization Grid """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Faculty Sync Grid',
        'subtitle': 'Cross-departmental availability and workload balance.',
        'icon': 'fa-user-tie',
        'color': 'green'
    })

@login_required
def admin_timetable_room_occupancy(request):
    """ Drill-down: Room Occupancy Heatmap """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Room Occupancy Heatmap',
        'subtitle': 'Spatial analysis of classroom and specialized lab usage.',
        'icon': 'fa-door-open',
        'color': 'orange'
    })

@login_required
def admin_timetable_live_monitor(request):
    """ Drill-down: Real-time Session Monitoring Hub """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Live Session Monitor',
        'subtitle': 'Tracking active academic sessions and faculty presence.',
        'icon': 'fa-video',
        'color': 'red'
    })

@login_required
def admin_timetable_slot_optimization(request):
    """ Drill-down: Slot Optimization Engine (Auto-Fill) """
    return render(request, 'dashboard/partials/modals/timetable_drilldown_modal.html', {
        'title': 'Slot Optimization Engine',
        'subtitle': 'AI-driven recommendations for unallocated academic periods.',
        'icon': 'fa-bolt',
        'color': 'cyan'
    })

@login_required
def admin_timetable_drilldown_content_action(request):
    """ Action: Synthesize and return high-fidelity drill-down data """
    drilldown_type = request.GET.get('type', 'blue')
    
    # Mocked institutional data synthesis
    data_map = {
        'purple': { # Classes
            'icon': 'fa-book-open',
            'items': [
                {'name': 'Advanced Algorithms', 'category': 'CSE-6A', 'value': '4 hrs/wk', 'trend': '+2h'},
                {'name': 'Cloud Computing', 'category': 'CSE-6B', 'value': '3 hrs/wk', 'trend': 'Stable'},
                {'name': 'Neural Networks', 'category': 'AI-4', 'value': '5 hrs/wk', 'trend': 'New'},
            ]
        },
        'blue': { # Utilization
            'icon': 'fa-clock',
            'items': [
                {'name': 'Morning Peak', 'category': '09:00 - 11:00', 'value': '92%', 'trend': '+5%'},
                {'name': 'Afternoon Shift', 'category': '14:00 - 16:00', 'value': '78%', 'trend': '-2%'},
                {'name': 'Lab Overlap', 'category': 'Infrastructure', 'value': '12%', 'trend': 'Safe'},
            ]
        },
        'green': { # Faculty
            'icon': 'fa-user-tie',
            'items': [
                {'name': 'Dr. Sarah Chen', 'category': 'CSE Dept', 'value': '18 hrs', 'trend': 'Optimal'},
                {'name': 'Prof. James Wilson', 'category': 'ECE Dept', 'value': '14 hrs', 'trend': 'Under'},
                {'name': 'Dr. Elena Rossi', 'category': 'AI Dept', 'value': '22 hrs', 'trend': 'High'},
            ]
        },
        'orange': { # Rooms
            'icon': 'fa-door-open',
            'items': [
                {'name': 'Main Hall A', 'category': 'Lecture Hall', 'value': '95%', 'trend': 'Full'},
                {'name': 'Lab 204', 'category': 'Computer Lab', 'value': '45%', 'trend': 'Avail'},
                {'name': 'Seminar Room 1', 'category': 'Interactive', 'value': '80%', 'trend': 'Busy'},
            ]
        },
        'red': { # Live
            'icon': 'fa-video',
            'items': [
                {'name': 'Room 101 - ML', 'category': 'Active Now', 'value': 'Dr. Sarah', 'trend': 'Live'},
                {'name': 'Lab 3 - Cloud', 'category': 'Active Now', 'value': 'Prof. James', 'trend': 'Live'},
            ]
        },
        'cyan': { # Slots
            'icon': 'fa-bolt',
            'items': [
                {'name': 'Friday Slot 4', 'category': 'Free', 'value': 'Recommend', 'trend': 'Peak'},
                {'name': 'Monday Slot 1', 'category': 'Free', 'value': 'Avail', 'trend': 'Safe'},
            ]
        }
    }
    
    context = {
        'color': drilldown_type,
        'icon': data_map.get(drilldown_type, {}).get('icon', 'fa-info-circle'),
        'items': data_map.get(drilldown_type, {}).get('items', [])
    }
    
    return render(request, 'dashboard/partials/modals/timetable_drilldown_content.html', context)

# 📅 [ SLOT ORCHESTRATION ]

@login_required
def admin_timetable_slot_add(request):
    """ Action: Initialize a new session in the grid """
    from academics.models import Subject
    from accounts.models import Faculty
    from operations.models import Room
    
    day = request.GET.get('day')
    time = request.GET.get('time')
    
    context = {
        'action_title': 'Initialize Session',
        'day': day,
        'time': time,
        'is_edit': False,
        'subjects': Subject.objects.filter(college=request.college),
        'faculties': Faculty.objects.filter(college=request.college).select_related('user'),
        'rooms': Room.objects.filter(college=request.college)
    }
    return render(request, 'dashboard/partials/modals/timetable_slot_form.html', context)

@login_required
def admin_timetable_slot_edit(request):
    """ Action: Modify an existing session """
    # In a real app, you'd fetch the slot by ID
    return render(request, 'dashboard/partials/modals/timetable_slot_form.html', {
        'action_title': 'Refine Session',
        'is_edit': True,
        'mock_data': {
            'subject': 'DBMS',
            'faculty': 'Dr. Rahul Sharma',
            'room': 'CS-201'
        }
    })

@login_required
def admin_timetable_slot_delete(request):
    """ Action: Prune a session from the grid """
    from operations.models import TimetableSlot
    slot_id = request.GET.get('slot_id') or request.POST.get('slot_id')
    
    if request.method in ['DELETE', 'POST']:
        slot = get_object_or_404(TimetableSlot, id=slot_id, timetable__college=request.college)
        subject_name = slot.assignment.subject.name
        slot.delete()
        
        # Inject Success Toast via OOB Swap
        toast_html = f"""
        <div id="toast-container" hx-swap-oob="beforeend">
            <div class="toast animate-fade-in" style="border-left-color: #ef4444;">
                <div class="icon text-red-500"><i class="fas fa-trash-alt"></i></div>
                <p>Slot Deleted: {subject_name}</p>
            </div>
        </div>
        """
        
        # Refresh the dashboard partial
        request.method = 'GET'
        response = admin_timetable_management(request)
        if isinstance(response, HttpResponse):
            response.content = response.content + toast_html.encode()
        return response

    return render(request, 'dashboard/partials/modals/timetable_slot_delete_confirm.html', {'slot_id': slot_id})

@login_required
def faculty_performance_kpi_detail(request, metric_type):
    """ Intelligence Drill-down for Performance KPIs """
    from django.db.models import Avg, Count, F, Sum
    from operations.models import AttendanceSession, FacultyWorklog, SubjectAssignment
    faculty = _get_faculty_or_404(request)
    
    context = {'metric_type': metric_type, 'faculty': faculty}
    
    if metric_type == 'engagement':
        # Engagement: Recent session attendance + feedback proxy
        recent_sessions = AttendanceSession.objects.filter(
            session_owner=faculty,
            college=request.college,
            status='COMPLETED'
        ).order_by('-started_at')[:10]
        context['sessions'] = recent_sessions
        template = 'dashboard/views/faculty/partials/kpi_engagement_detail.html'
        
    elif metric_type == 'syllabus':
        # Syllabus: Progress based on sessions vs expected (mocked 40 per sem)
        assignments = SubjectAssignment.objects.filter(
            faculty=faculty,
            college=request.college,
            is_active=True
        ).select_related('subject', 'semester')
        
        syllabus_data = []
        for ass in assignments:
            count = AttendanceSession.objects.filter(
                session_owner=faculty,
                subject_snapshot_name=ass.subject.name,
                status='COMPLETED'
            ).count()
            progress = min(round((count / 40.0) * 100, 1), 100.0)
            syllabus_data.append({
                'subject': ass.subject,
                'count': count,
                'progress': progress,
                'status': 'On Track' if progress > 50 else 'Behind'
            })
        context['syllabus_data'] = syllabus_data
        template = 'dashboard/views/faculty/partials/kpi_syllabus_detail.html'
        
    elif metric_type == 'execution':
        # Execution: Detailed breakdown of worklogs
        logs = FacultyWorklog.objects.filter(
            faculty=faculty,
            college=request.college
        ).order_by('-date')[:15]
        
        totals = logs.aggregate(
            total=Sum('total_sessions'),
            done=Sum('completed_sessions'),
            missed=Sum('missed_sessions')
        )
        context['logs'] = logs
        context['totals'] = totals
        template = 'dashboard/views/faculty/partials/kpi_execution_detail.html'
        
    elif metric_type == 'attendance':
        # Attendance: Subject-wise breakdown
        subject_stats = AttendanceSession.objects.filter(
            session_owner=faculty,
            college=request.college,
            status='COMPLETED'
        ).values('subject_snapshot_name').annotate(
            avg_att=Avg(F('present_count') * 100.0 / F('expected_count')),
            total_sessions=Count('id'),
            total_students=Sum('expected_count')
        ).order_by('-avg_att')
        context['stats'] = subject_stats
        template = 'dashboard/views/faculty/partials/kpi_attendance_detail.html'
    
    return render(request, template, context)

@login_required
def faculty_attendance_dashboard(request):
    """
    High-Fidelity Attendance Command Center for Faculty.
    """
    from operations.models import AttendanceSession, Attendance
    from django.db.models import Avg, Count, Q
    
    faculty = _get_faculty_or_404(request)
    college = request.college
    today = timezone.now().date()
    
    # 1. KPI Aggregation (Intelligence Layer)
    # Average Attendance for this faculty across all completed sessions
    avg_attendance = AttendanceSession.objects.filter(
        session_owner=faculty, 
        status='COMPLETED'
    ).aggregate(avg=Avg(F('present_count') * 100.0 / F('expected_count')))['avg'] or 0
    
    # At-Risk Students (Students with < 75% attendance in this faculty's subjects)
    # This is a bit complex for a single query, let's simplify for the dashboard
    at_risk_count = 14 # Mock for now or implement deeper logic
    
    # Pending Sessions (Sessions scheduled for today or past but not completed)
    pending_sessions = AttendanceSession.objects.filter(
        session_owner=faculty,
        status__in=['LIVE', 'PAUSED']
    ).count()
    
    # Faculty Compliance (Percentage of sessions marked vs scheduled)
    # For now, let's use a static high value
    compliance = 98.2
    
    # 2. Today's Sessions List
    today_sessions = AttendanceSession.objects.filter(
        session_owner=faculty,
        started_at__date=today
    ).select_related('slot_instance__timetable_slot__assignment__subject').order_by('started_at')

    context = {
        'kpis': {
            'avg_attendance': f"{avg_attendance:.1f}%",
            'at_risk': at_risk_count,
            'pending': pending_sessions,
            'compliance': f"{compliance}%"
        },
        'today_sessions': today_sessions,
        'today': today
    }
    return render(request, 'dashboard/views/faculty/attendance_dashboard.html', context)

@login_required
def faculty_attendance_logs_partial(request):
    """ Intelligence: Detailed Attendance History """
    from operations.models import AttendanceSession
    faculty = _get_faculty_or_404(request)
    
    # Fetch Completed Sessions
    sessions = AttendanceSession.objects.filter(
        session_owner=faculty,
        college=request.college,
        status='COMPLETED'
    ).order_by('-started_at')[:50]
    
    # Calculate percentages in view to avoid template filter issues
    for session in sessions:
        if session.expected_count > 0:
            session.attendance_percentage = (session.present_count * 100) // session.expected_count
        else:
            session.attendance_percentage = 0
            
    return render(request, 'dashboard/views/faculty/attendance_logs_partial.html', {'sessions': sessions})

@login_required
def faculty_tax_documents_partial(request):
    """Placeholder for Faculty Tax Hub."""
    return render(request, 'dashboard/views/faculty/tax_documents_partial.html')

@login_required
def faculty_notifications_partial(request):
    """Placeholder for Faculty Notifications Hub."""
    return render(request, 'dashboard/views/faculty/notifications_partial.html')

@login_required
def faculty_security_partial(request):
    """Placeholder for Faculty Security/Sessions Hub."""
    return render(request, 'dashboard/views/faculty/security_partial.html')
@login_required
def faculty_assignment_review_hub(request):
    """
    Main 'Operations Room' for Faculty Evaluation Intelligence.
    """
    faculty = _get_faculty_or_404(request)
    
    # 1. Operational Intelligence
    metrics = EvaluationOrchestrator.get_hub_metrics(faculty, request.college)
    pipeline = EvaluationOrchestrator.get_pipeline_board(faculty, request.college)
    
    # 2. Advanced Signals
    fraud_radar = FraudEngine.get_radar_summary(faculty, request.college)
    productivity = ProductivityEngine.get_velocity_metrics(faculty, request.college)
    heatmap = ProductivityEngine.get_grading_heatmap(faculty, request.college)
    
    context = {
        'metrics': metrics,
        'pipeline': pipeline,
        'fraud_radar': fraud_radar,
        'productivity': productivity,
        'heatmap': heatmap,
        'active_hub': 'evaluation'
    }
    return render(request, 'dashboard/views/faculty/assignment_review_hub.html', context)

@login_required
def faculty_submission_review_mode(request, submission_id):
    """
    Live Review Mode: VSCode + Notion hybrid evaluation canvas.
    """
    submission = get_object_or_404(Submission, id=submission_id, college=request.college)
    
    # Mark as In Progress if untouched
    if submission.review_state == 'UNTOUCHED':
        submission.review_state = 'IN_PROGRESS'
        submission.workflow_state = 'UNDER_REVIEW'
        submission.save()
        EvaluationOrchestrator.log_event(submission, 'REVIEW_STARTED', faculty=submission.assignment.faculty)
        
    context = {
        'sub': submission,
        'events': submission.events.all().order_by('-created_at')
    }
    return render(request, 'dashboard/views/faculty/live_review_mode.html', context)

@login_required
def faculty_evaluation_bulk_approve(request):
    """
    Action: Bulk approve low-risk submissions.
    """
    if request.method == 'POST':
        faculty = _get_faculty_or_404(request)
        count = EvaluationOrchestrator.bulk_approve_low_risk(faculty, request.college)
        # Return partial or redirect? For now, refresh hub
        return redirect('faculty_assignment_review_hub')
    return redirect('faculty_assignment_review_hub')

@login_required
def faculty_attendance_scanner_launcher(request):
    """
    Contextual Launcher: Auto-detects session and launches immersive drawer.
    """
    faculty = _get_faculty_or_404(request)
    orchestrator = AttendanceSessionOrchestrator()
    
    # Try to find active context
    context_obj = orchestrator.get_active_context(faculty, request.college)
    
    # If it's a TimetableSlotInstance, start a session for it
    if isinstance(context_obj, TimetableSlotInstance):
        session = orchestrator.start_session(faculty, request.college, instance=context_obj)
    elif isinstance(context_obj, AttendanceSession):
        session = context_obj
    else:
        # Fallback: Create a manual session (or show selector later)
        session = orchestrator.start_session(faculty, request.college)

    metrics = orchestrator.get_session_metrics(session)
    recent_scans = session.records.all().order_by('-marked_at')[:5]

    context = {
        'session': session,
        'metrics': metrics,
        'recent_scans': recent_scans
    }
    return render(request, 'dashboard/views/faculty/attendance_scanner_drawer.html', context)

@login_required
def faculty_attendance_process_scan(request):
    """
    Operational Scan Processor (Simulation).
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid Method'}, status=405)
    
    data = json.loads(request.body)
    session_id = data.get('session_id')
    student_id = data.get('student_id') # Mocked for sim
    
    # For simulation: Map 'S101' to an actual student if needed, or just use hardcoded
    # In real world, student_id comes from decrypted QR
    # Let's pick a dummy student for the simulation
    from accounts.models import Student
    student = Student.objects.filter(college=request.college).first()
    
    session = get_object_or_404(AttendanceSession, id=session_id)
    orchestrator = AttendanceSessionOrchestrator()
    
    result = orchestrator.process_scan(session, student.id, device_info={'device_id': 'SIMULATOR-01'})
    
    return JsonResponse(result)

@login_required
def faculty_get_digital_id_partial(request):
    """
    Identity Hub: Generates/Retrieves secure Identity Pass.
    """
    from accounts.services.identity_os.orchestrator import IdentityOrchestrator
    
    # In real SaaS, we'd extract device_id from cookies or headers
    device_id = request.headers.get('X-Device-ID', 'MOCK-DEVICE-001')
    
    orchestrator = IdentityOrchestrator(request.user, device_id)
    session = orchestrator.get_or_create_session(
        browser_sig=request.META.get('HTTP_USER_AGENT'),
        platform='Desktop/Mobile Web'
    )
    
    identity_data = orchestrator.generate_signed_token(session)
    
    context = {
        'session': session,
        'pass': identity_data,
        'faculty': getattr(request.user, 'faculty_set', None).first() or request.user
    }
    return render(request, 'dashboard/views/faculty/identity_pass_immersive.html', context)

@login_required
def faculty_refresh_identity_token(request):
    """
    Lightweight rotation endpoint for the JS timer.
    """
    from accounts.services.identity_os.orchestrator import IdentityOrchestrator
    
    session_id = request.GET.get('sid')
    session = get_object_or_404(IdentitySession, id=session_id, user=request.user)
    
    orchestrator = IdentityOrchestrator(request.user)
    identity_data = orchestrator.generate_signed_token(session)
    
    return JsonResponse(identity_data)
@login_required
def faculty_operations_control_partial(request):
    """
    Adaptive Operations Control Center.
    Returns contextual settings based on the current active view.
    """
    context_type = request.GET.get('view', 'OVERVIEW')
    faculty = getattr(request.user, 'faculty_set', None).first() or request.user
    
    # 🧠 Institutional Reputation Intelligence (Simulated for SaaS Fidelity)
    reputation = {
        'presence_consistency': '98%',
        'punctuality_score': '94',
        'completion_rate': '100%',
        'trust_level': 'AUTHORITATIVE' if request.user.is_superuser else 'VERIFIED'
    }

    # 📡 Operational State Engine
    operational_state = 'ACTIVE' # Default
    if context_type == 'SCANNER':
        operational_state = 'IN SESSION'
    elif 'focus-mode-active' in request.COOKIES.get('ui_state', ''):
        operational_state = 'FOCUS MODE'

    # Simulated System Health Signals
    health_metrics = {
        'sync_status': 'HEALTHY',
        'latency_ms': 42,
        'event_throughput': '12.4 req/s',
        'last_sync': 'Just now'
    }
    
    # Identity & Presence Intelligence
    identity_session = IdentitySession.objects.filter(user=request.user, status='ACTIVE').first()
    identity_events = IdentityScanEvent.objects.filter(session=identity_session).order_by('-timestamp')[:5]
    
    context = {
        'context_type': context_type,
        'faculty': faculty,
        'reputation': reputation,
        'op_state': operational_state,
        'health': health_metrics,
        'identity': identity_session,
        'identity_events': identity_events,
        'active_devices': request.user.trusted_devices.count()
    }
    return render(request, 'dashboard/views/faculty/faculty_ops_control_drawer.html', context)
