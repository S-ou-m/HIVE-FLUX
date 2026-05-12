from django.core.cache import cache
from django.db.models import Count, Q, Exists, OuterRef, Sum
from django.utils import timezone
from datetime import timedelta
from accounts.models import Student
from finance.models import Invoice

def get_student_core_stats(college):
    """
    Returns Elite SaaS metrics for the Student Intelligence Engine.
    Uses Exists subqueries for high performance at scale.
    Cached for 60 seconds (event-invalidated in models).
    """
    cache_key = f'student_core_stats_{college.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data

    now = timezone.now()
    
    # 1. Base Queryset (Tenant Scoped + Soft-Delete Integrity)
    all_students = Student.objects.filter(college=college, is_deleted=False)
    total_students = all_students.count()

    # 2. Comparison Period Engine (Aligned Windows)
    # Current 6 months vs Immediately preceding 6 months
    # (Simplified for KPI MoM growth)
    current_month = now.month
    current_year = now.year
    
    # 3. Decision-Grade Financial Metrics (Soft-Delete Aware)
    # Total Outstanding: (total_amount - paid_amount) for active invoices
    # Collection Velocity: paid_amount within current time window
    finance_metrics = Invoice.objects.filter(college=college, is_deleted=False).aggregate(
        total_billed=Sum('total_amount'),
        total_paid=Sum('paid_amount'),
        total_outstanding=Sum('total_amount') - Sum('paid_amount') # Derived outstanding
    )
    
    total_billed = finance_metrics['total_billed'] or 0
    total_paid = finance_metrics['total_paid'] or 0
    total_outstanding = (finance_metrics['total_billed'] or 0) - (finance_metrics['total_paid'] or 0)
    collection_efficiency = round((total_paid / total_billed * 100)) if total_billed > 0 else 0

    # Avg Payment: total_paid / unique_students_who_paid
    paid_student_count = Invoice.objects.filter(college=college, is_deleted=False, paid_amount__gt=0).values('student').distinct().count()
    avg_payment_per_student = round(total_paid / paid_student_count) if paid_student_count > 0 else 0

    # 4. Existence-Based Risk Indicators
    overdue_invoices_qs = Invoice.objects.filter(student=OuterRef('pk'), status='OVERDUE', is_deleted=False)
    students_at_risk = all_students.filter(Exists(overdue_invoices_qs)).count()
    
    # 5. Smart Growth & Prediction (Bounded Guardrails)
    if current_month == 1:
        last_month, last_month_year = 12, current_year - 1
    else:
        last_month, last_month_year = current_month - 1, current_year
        
    this_month_growth = all_students.filter(created_at__year=current_year, created_at__month=current_month).count()
    last_month_growth = all_students.filter(created_at__year=last_month_year, created_at__month=last_month).count()
    
    if last_month_growth > 0:
        growth_percent = round(((this_month_growth - last_month_growth) / last_month_growth) * 100)
    else:
        growth_percent = 100 if this_month_growth > 0 else 0

    # Predictive Projection (min 5 students guardrail)
    prediction_text = None
    if total_students >= 5:
        # Simple linear projection
        days_in_month = 30 # Approx
        current_day = now.day
        projected = round((this_month_growth / current_day) * days_in_month)
        # Bounded at 2x current trend
        projected = min(projected, this_month_growth * 2)
        if projected > this_month_growth:
            prediction_text = f"Projected {projected} admissions by month-end."

    # 6. Prioritized Insight Engine (Critical > Growth > Info)
    insights = []
    if students_at_risk > 0:
        insights.append({'type': 'critical', 'text': f"⚠️ {students_at_risk} students have overdue payments."})
    if growth_percent > 20:
        insights.append({'type': 'growth', 'text': f"📈 Exceptional growth: {growth_percent}% increase this month."})
    if total_outstanding > 0:
        insights.append({'type': 'info', 'text': f"💰 Total outstanding revenue: ₹{total_outstanding:,}"})

    # Top Dept
    top_dept_qs = all_students.exclude(department__isnull=True) \
                               .values('department__name') \
                               .annotate(count=Count('id')) \
                               .order_by('-count').first()
    top_dept_name = top_dept_qs['department__name'] if top_dept_qs else "None"

    data = {
        'total_students': total_students,
        'growth': {
            'value': this_month_growth,
            'percent': growth_percent,
            'prediction': prediction_text,
            'trend': 'positive' if growth_percent >= 0 else 'negative'
        },
        'finance': {
            'total_outstanding': total_outstanding,
            'collection_efficiency': collection_efficiency,
            'avg_payment': avg_payment_per_student,
            'risk_count': students_at_risk
        },
        'academics': {
            'active_depts': all_students.values('department').distinct().exclude(department__isnull=True).count(),
            'top_dept': top_dept_name,
        },
        'insights': insights[:3],
        'meta': {
            'confidence': f"Based on {total_students} active records",
            'server_time': timezone.now().isoformat()
        }
    }
    
    cache.set(cache_key, data, timeout=60)
    return data

# --- MODULAR CHART APIs ---

def get_chart_enrollment_trend(college, time_filter='6m'):
    """ Returns trailing period of admissions with comparison to previous period """
    cache_key = f'chart_enrollment_{college.id}_{time_filter}'
    cached = cache.get(cache_key)
    if cached: return cached

    now = timezone.now()
    labels = []
    current_period = []
    previous_period = []
    
    # 6-month or 12-month window
    limit = 6 if time_filter == '6m' else 12
    
    for i in range(limit - 1, -1, -1):
        # Current Window
        target_date = now - timedelta(days=30*i)
        month_name = target_date.strftime('%b')
        labels.append(month_name)
        
        count = Student.objects.filter(
            college=college, is_deleted=False,
            created_at__year=target_date.year,
            created_at__month=target_date.month
        ).count()
        current_period.append(count)
        
        # Previous Window (Aligned)
        prev_date = target_date - timedelta(days=30*limit)
        prev_count = Student.objects.filter(
            college=college, is_deleted=False,
            created_at__year=prev_date.year,
            created_at__month=prev_date.month
        ).count()
        previous_period.append(prev_count)

    data = {
        "labels": labels,
        "data": current_period,
        "comparison_data": previous_period,
        "meta": {"title": "Enrollment Velocity"}
    }
    cache.set(cache_key, data, timeout=60)
    return data

def get_chart_department(college):
    cache_key = f'chart_dept_{college.id}'
    cached = cache.get(cache_key)
    if cached: return cached

    # Canonical order: count descending
    dept_qs = Student.objects.filter(college=college, is_deleted=False, department__isnull=False) \
                             .values('department__id', 'department__name') \
                             .annotate(count=Count('id')) \
                             .order_by('-count')[:6]
                             
    data = {
        "labels": [item['department__name'] for item in dept_qs],
        "data": [item['count'] for item in dept_qs],
        "ids": [item['department__id'] for item in dept_qs],
        "meta": {"title": "Department Yield"}
    }
    cache.set(cache_key, data, timeout=60)
    return data

def get_chart_semester(college):
    cache_key = f'chart_sem_{college.id}'
    cached = cache.get(cache_key)
    if cached: return cached

    # Group by number to prevent duplicate labels in charts
    sem_qs = Student.objects.filter(college=college, is_deleted=False, current_semester__isnull=False) \
                            .values('current_semester__number') \
                            .annotate(count=Count('id')) \
                            .order_by('current_semester__number')
                            
    data = {
        "labels": [f"Sem {item['current_semester__number']}" for item in sem_qs],
        "data": [item['count'] for item in sem_qs],
        "meta": {"title": "Academic Distribution"}
    }
    cache.set(cache_key, data, timeout=60)
    return data

def get_chart_finance(college):
    cache_key = f'chart_finance_{college.id}'
    cached = cache.get(cache_key)
    if cached: return cached

    all_students = Student.objects.filter(college=college, is_deleted=False)
    unpaid_invoices = Invoice.objects.filter(student=OuterRef('pk'), status__in=['PENDING', 'PARTIAL', 'OVERDUE'], is_deleted=False)
    
    with_dues = all_students.filter(Exists(unpaid_invoices)).count()
    with_advance = all_students.filter(credit_balance__gt=0).count()
    cleared = max(0, all_students.count() - with_dues - with_advance)

    data = {
        "labels": ["Cleared", "With Dues", "Advance Paid"],
        "data": [cleared, with_dues, with_advance],
        "meta": {"title": "Financial Recovery"}
    }
    cache.set(cache_key, data, timeout=60)
    return data
