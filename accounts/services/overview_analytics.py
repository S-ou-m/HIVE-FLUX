from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.cache import cache
from accounts.models import Student, Faculty, SuccessSignal
from finance.models import Invoice, Payment
from academics.models import Department, Semester, StudentSkillMastery
from operations.models import AttendanceSession, Attendance

def get_core_kpis(college):
    """Total Students + Growth Comparison"""
    cache_key = f"core_kpis_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    total_students = Student.objects.filter(college=college).count()
    
    # Growth Calculation (Current Month vs Previous Month)
    now = timezone.now()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0)
    first_of_prev_month = (first_of_this_month - timedelta(days=1)).replace(day=1)
    
    this_month_count = Student.objects.filter(college=college, created_at__gte=first_of_this_month).count()
    prev_month_count = Student.objects.filter(college=college, created_at__gte=first_of_prev_month, created_at__lt=first_of_this_month).count()
    
    growth_pct = 0
    growth_label = f"+{this_month_count} new"
    
    if prev_month_count > 0:
        growth_pct = ((this_month_count - prev_month_count) / prev_month_count) * 100
        growth_label = f"{growth_pct:+.1f}%"
    
    data = {
        'total': total_students,
        'growth_label': growth_label,
        'this_month': this_month_count,
        'is_positive': this_month_count >= prev_month_count
    }
    cache.set(cache_key, data, 60)
    return data

def get_financial_kpis(college):
    """Collection Efficiency + Total Outstanding + Snapshot Breakdown"""
    cache_key = f"financial_kpis_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    invoices = Invoice.objects.filter(student__college=college)
    total_billed = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    
    efficiency = 0
    if total_billed > 0:
        efficiency = (total_paid / total_billed) * 100
    
    outstanding = total_billed - total_paid
    
    # Financial Snapshot Breakdown
    cleared = invoices.filter(status='PAID').count()
    with_dues = invoices.filter(status__in=['PENDING', 'PARTIAL', 'OVERDUE']).count()
    advance = Student.objects.filter(college=college, credit_balance__gt=0).count()
    
    # SaaS KPIs: Collection Velocity (last 7 days)
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_payments = Payment.objects.filter(college=college, payment_date__gte=seven_days_ago).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    data = {
        'efficiency': round(efficiency, 1),
        'outstanding': outstanding,
        'total_paid': total_paid,
        'velocity': recent_payments,
        'snapshot': {
            'cleared': cleared,
            'dues': with_dues,
            'advance': advance
        }
    }
    cache.set(cache_key, data, 60)
    return data

def get_risk_signals(college):
    """Students with Overdue or Partial Invoices"""
    # Simple threshold: Outstanding > 5000 or status is Overdue
    risk_count = Student.objects.filter(
        college=college,
        invoice__status__in=['OVERDUE', 'PARTIAL']
    ).distinct().count()
    
    return {'count': risk_count}

def get_growth_trends(college):
    """Monthly Enrollment Trend for the last 6 months"""
    cache_key = f"growth_trends_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    months = []
    counts = []
    now = timezone.now()
    
    for i in range(5, -1, -1):
        month_date = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        next_month = (month_date + timedelta(days=32)).replace(day=1)
        
        count = Student.objects.filter(
            college=college, 
            created_at__gte=month_date, 
            created_at__lt=next_month
        ).count()
        
        months.append(month_date.strftime('%b'))
        counts.append(count)
        
    data = {'labels': months, 'data': counts}
    cache.set(cache_key, data, 3600) # Trend data can be cached longer
    return data

def get_distribution_stats(college):
    """Department and Semester Distributions"""
    dept_stats = Student.objects.filter(college=college)\
        .values('department__name')\
        .annotate(count=Count('id'))\
        .order_by('-count')
    
    sem_stats = Student.objects.filter(college=college)\
        .values('current_semester__number')\
        .annotate(count=Count('id'))\
        .order_by('current_semester__number')
    
    return {
        'departments': list(dept_stats),
        'semesters': list(sem_stats),
        'total_students': Student.objects.filter(college=college).count()
    }

def get_timeline_events(college):
    """Aggregates Financial and Academic deadlines for the next 14 days"""
    cache_key = f"timeline_events_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    today = timezone.now().date()
    two_weeks_later = today + timedelta(days=14)
    
    events = []
    
    # 1. Financial: Invoice Due Dates
    invoices = Invoice.objects.filter(
        college=college, 
        due_date__gte=today, 
        due_date__lte=two_weeks_later,
        status__in=['PENDING', 'PARTIAL']
    ).values('due_date').annotate(count=Count('id'))
    
    for inv in invoices:
        events.append({
            'date': inv['due_date'],
            'day': inv['due_date'].day,
            'title': f"{inv['count']} Payments Due",
            'type': 'financial',
            'severity': 'warning'
        })
        
    # 2. Academic: Student Anniversaries (Month/Day match)
    # This is tricky in Django ORM across years, so we look for students 
    # whose created_at month/day fall within the window.
    window_days = [(today + timedelta(days=i)) for i in range(15)]
    for d in window_days:
        count = Student.objects.filter(
            college=college,
            created_at__month=d.month,
            created_at__day=d.day
        ).count()
        if count > 0:
            events.append({
                'date': d,
                'day': d.day,
                'title': f"{count} Enrollment Anniv.",
                'type': 'academic',
                'severity': 'info'
            })
        
    # Sort by date
    events = sorted(events, key=lambda x: x['date'])
    
    cache.set(cache_key, events, 3600)
    return events

def get_calendar_matrix(year=None, month=None):
    """Generates a matrix for the specified month's calendar with navigation meta"""
    import calendar
    now = timezone.now()
    
    if year is None: year = now.year
    if month is None: month = now.month
    
    # Boundary logic for navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    cal = calendar.monthcalendar(year, month)
    
    # Check if we are viewing the actual current month
    is_current_month = (year == now.year and month == now.month)
    
    target_date = datetime(year, month, 1)
    
    return {
        'month_name': target_date.strftime('%B %Y'),
        'matrix': cal,
        'today': now.day,
        'is_current_month': is_current_month,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year
    }

def get_insight_signals(college):
    """Priority-sorted Intelligence Signals with Action Links"""
    signals = []
    
    # 1. Critical: Unpaid Dues
    financials = get_financial_kpis(college)
    risk = get_risk_signals(college)
    if financials['outstanding'] > 50000:
        signals.append({
            'type': 'critical',
            'label': f"₹{financials['outstanding']:,} Overdue Revenue",
            'sub_text': f"{risk['count']} students with payment risk",
            'icon': 'exclamation-triangle',
            'action_url': '/dashboard/admin/partial/finance/payments/?status=OVERDUE'
        })
        
    # 2. Warning: Collection Velocity
    if financials['velocity'] < 10000:
        signals.append({
            'type': 'warning',
            'label': "Low Weekly Collection",
            'sub_text': f"₹{financials['velocity']:,} collected in last 7 days",
            'icon': 'trending-down',
            'action_url': '/dashboard/admin/partial/finance/stats/'
        })
        
    # 3. Growth: Admissions
    core = get_core_kpis(college)
    if core['this_month'] > 0:
        signals.append({
            'type': 'growth',
            'label': f"New Admissions: {core['this_month']}",
            'sub_text': f"Trend: {core['growth_label']}",
            'icon': 'user-plus',
            'action_url': '/dashboard/admin/partial/students/?filter=this_month'
        })
    
    # 4. Real-time: Operational Hotspots (Low Attendance Today)
    today = timezone.now().date()
    today_sessions = AttendanceSession.objects.filter(college=college, started_at__date=today, status__in=['COMPLETED', 'LOCKED'])
    if today_sessions.exists():
        for session in today_sessions:
            if session.expected_count > 0:
                att_pct = (session.present_count / session.expected_count) * 100
                if att_pct < 60:
                    signals.append({
                        'type': 'critical',
                        'label': f"Low Attendance: {session.subject_snapshot_name}",
                        'sub_text': f"{att_pct:.1f}% attendance in today's session",
                        'icon': 'clock',
                        'action_url': f'/dashboard/admin/partial/attendance/session/{session.id}/'
                    })
    
    return signals[:3]

def get_system_health_score(college):
    """Weighted health score based on operational metrics"""
    financials = get_financial_kpis(college)
    core = get_core_kpis(college)
    
    # Logic: 
    # Efficiency (40%) + Enrollment Growth (30%) + Collection Velocity (30%)
    f_score = financials['efficiency'] * 0.4
    g_score = min(100, core['this_month'] * 5) * 0.3 # Cap growth score
    v_score = min(100, (financials['velocity'] / 50000) * 100) * 0.3
    
    total = int(f_score + g_score + v_score)
    return max(0, min(100, total))

def get_success_intelligence(college):
    """Aggregates high-weight success signals for the executive overview"""
    signals = SuccessSignal.objects.filter(college=college)
    distribution = signals.values('signal_type').annotate(count=Count('id')).order_by('-count')
    
    # Severity breakdown
    severity = signals.values('weight').annotate(count=Count('id'))
    
    return {
        'total': signals.count(),
        'distribution': list(distribution),
        'severity': list(severity)
    }

def get_skill_intelligence(college):
    """Institutional-wide skill mastery benchmarks"""
    top_skills = StudentSkillMastery.objects.filter(student__college=college)\
        .values('skill__name')\
        .annotate(avg_mastery=Avg('mastery_level'))\
        .order_by('-avg_mastery')[:5]
    
    return list(top_skills)
