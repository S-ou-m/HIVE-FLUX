import datetime
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from finance.models import Payment, Invoice, Payroll
from accounts.models import Student

def get_finance_stats(college, time_filter='this_month'):
    """
    Service layer to calculate deterministic, cached finance stats.
    """
    # 1. Define Time Ranges
    now = timezone.now()
    start_date = None
    prev_start = None
    prev_end = None

    if time_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - datetime.timedelta(days=1)
        prev_end = start_date
    elif time_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_prev_month = start_date - datetime.timedelta(days=1)
        prev_start = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_end = start_date
    elif time_filter == 'this_year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date.replace(year=start_date.year - 1)
        prev_end = start_date

    # Cache Key
    cache_key = f"finance_stats_{college.id}_{time_filter}"
    data = cache.get(cache_key)
    if data:
        return data

    # 2. Base QuerySets (Scoped to College & Active Students)
    active_student_ids = Student.objects.filter(college=college).values_list('id', flat=True)
    
    # 3. Revenue Calculation (Flow Metric)
    payments_qs = Payment.objects.filter(college=college, status='SUCCESS', student_id__in=active_student_ids)
    
    if start_date:
        curr_rev_agg = payments_qs.filter(created_at__gte=start_date).aggregate(total=Sum('amount_paid'), count=Count('id'))
        prev_rev_agg = payments_qs.filter(created_at__gte=prev_start, created_at__lt=prev_end).aggregate(total=Sum('amount_paid'))
    else:
        curr_rev_agg = payments_qs.aggregate(total=Sum('amount_paid'), count=Count('id'))
        prev_rev_agg = {'total': 0}

    revenue_val = curr_rev_agg['total'] or 0
    revenue_count = curr_rev_agg['count'] or 0
    prev_revenue_val = prev_rev_agg['total'] or 0
    
    revenue_trend = 0
    if prev_revenue_val > 0:
        revenue_trend = ((revenue_val - prev_revenue_val) / prev_revenue_val) * 100

    # 4. Pending Fees (Stock Metric - Snapshot)
    invoices_qs = Invoice.objects.filter(college=college, student_id__in=active_student_ids)
    pending_agg = invoices_qs.aggregate(total_billed=Sum('total_amount'), total_paid=Sum('paid_amount'))
    total_billed = pending_agg['total_billed'] or 0
    total_paid = pending_agg['total_paid'] or 0
    pending_val = max(total_billed - total_paid, 0)
    
    pending_invoices = invoices_qs.exclude(status='PAID')
    pending_count = pending_invoices.values('student').distinct().count()
    overdue_count = pending_invoices.filter(due_date__lt=now.date()).count()

    # 5. Advance Credits (Stock Metric - Snapshot)
    credits_val = Student.objects.filter(college=college, credit_balance__gt=0).aggregate(Sum('credit_balance'))['credit_balance__sum'] or 0
    credits_count = Student.objects.filter(college=college, credit_balance__gt=0).count()

    # 6. Payroll (Flow Metric)
    if start_date:
        payroll_agg = Payroll.objects.filter(college=college, status='PAID', created_at__gte=start_date).aggregate(total=Sum('net_salary'))
        prev_payroll_agg = Payroll.objects.filter(college=college, status='PAID', created_at__gte=prev_start, created_at__lt=prev_end).aggregate(total=Sum('net_salary'))
    else:
        payroll_agg = Payroll.objects.filter(college=college, status='PAID').aggregate(total=Sum('net_salary'))
        prev_payroll_agg = {'total': 0}

    payroll_val = payroll_agg['total'] or 0
    prev_payroll_val = prev_payroll_agg['total'] or 0
    
    payroll_trend = 0
    if prev_payroll_val > 0:
        payroll_trend = ((payroll_val - prev_payroll_val) / prev_payroll_val) * 100

    # Assemble Data Contract
    data = {
        "time_filter": time_filter,
        "revenue": {
            "value": revenue_val,
            "trend": round(revenue_trend, 1),
            "count": revenue_count
        },
        "pending": {
            "value": pending_val,
            "students": pending_count,
            "overdue": overdue_count
        },
        "credits": {
            "value": credits_val,
            "count": credits_count
        },
        "payroll": {
            "value": payroll_val,
            "trend": round(payroll_trend, 1)
        }
    }

    # Cache for 10 seconds to prevent DB hammering during active polling
    cache.set(cache_key, data, timeout=10)
    return data

def get_revenue_trend_data(college):
    """
    Returns time-series revenue data for sparkline/line chart.
    Groups by payment_date for the last 30 days.
    """
    thirty_days_ago = timezone.now().date() - datetime.timedelta(days=30)
    
    qs = Payment.objects.filter(
        college=college, 
        status='SUCCESS', 
        payment_date__gte=thirty_days_ago
    ).values('payment_date').annotate(total=Sum('amount_paid')).order_by('payment_date')
    
    # Fill in missing dates to ensure continuous sparkline
    date_map = {item['payment_date'].strftime('%b %d'): float(item['total'] or 0) for item in qs if item['payment_date']}
    
    labels = []
    data = []
    for i in range(30, -1, -1):
        d = (timezone.now().date() - datetime.timedelta(days=i)).strftime('%b %d')
        labels.append(d)
        data.append(date_map.get(d, 0.0))
        
    return {"labels": labels, "data": data}

def get_payment_mode_data(college):
    """Returns distribution of payment modes."""
    qs = Payment.objects.filter(college=college, status='SUCCESS').values('mode').annotate(total=Sum('amount_paid')).order_by('-total')
    labels = [str(item['mode']) for item in qs]
    data = [float(item['total'] or 0) for item in qs]
    return {"labels": labels, "data": data}

def get_department_revenue_data(college):
    """Returns revenue grouped by student department."""
    qs = Payment.objects.filter(college=college, status='SUCCESS', student__department__isnull=False)\
        .values('student__department__name')\
        .annotate(total=Sum('amount_paid'))\
        .order_by('-total')[:5]
    
    labels = [str(item['student__department__name']) for item in qs]
    data = [float(item['total'] or 0) for item in qs]
    return {"labels": labels, "data": data}
