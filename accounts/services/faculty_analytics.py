from django.core.cache import cache
from django.db.models import Count, Q, OuterRef, Exists, Avg, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from accounts.models import Faculty
from academics.models import Department
from operations.models import Timetable, TimetableSlot

def get_faculty_core_stats(college):
    """
    Elite SaaS: Returns workload intelligence and recruitment trends.
    """
    cache_key = f'faculty_core_stats_{college.id}'
    cached_data = cache.get(cache_key)
    if cached_data: return cached_data

    now = timezone.now()
    
    # 1. Base Queryset (Soft Delete & College Isolation)
    all_faculty = Faculty.objects.filter(college=college, is_deleted=False)
    total_faculty = all_faculty.count()
    
    # 2. Recruitment Velocity (This Month vs Last Month)
    this_month_growth = all_faculty.filter(created_at__year=now.year, created_at__month=now.month).count()
    prev_month_date = now - timedelta(days=30)
    last_month_growth = all_faculty.filter(created_at__year=prev_month_date.year, created_at__month=prev_month_date.month).count()
    
    growth_percent = 0
    if last_month_growth > 0:
        growth_percent = round(((this_month_growth - last_month_growth) / last_month_growth) * 100)
    elif this_month_growth > 0:
        growth_percent = 100

    # 3. Workload Analytics (Session Tracking)
    # Corrected: Query TimetableSlot as it contains the SubjectAssignment -> Faculty link
    slot_qs = TimetableSlot.objects.filter(timetable__college=college, is_active=True)
    total_sessions = slot_qs.count()
    
    # Classification: Overloaded vs Balanced vs Idle
    # Group by faculty to find session counts
    faculty_session_counts = slot_qs.values('assignment__faculty_id').annotate(count=Count('id'))
    
    overloaded_count = sum(1 for f in faculty_session_counts if f['count'] > 25) # > 5 sessions/day avg
    assigned_faculty_ids = set(f['assignment__faculty_id'] for f in faculty_session_counts if f['assignment__faculty_id'])
    idle_count = all_faculty.exclude(id__in=assigned_faculty_ids).count()

    # 4. Academic Density
    active_depts = all_faculty.values('department').distinct().exclude(department__isnull=True).count()
    top_dept_qs = all_faculty.exclude(department__isnull=True) \
                             .values('department__name') \
                             .annotate(count=Count('id')) \
                             .order_by('-count').first()
    top_dept_name = top_dept_qs['department__name'] if top_dept_qs else "None"

    # 5. Prioritized Insight Layer
    insights = []
    if overloaded_count > 0:
        insights.append({'type': 'critical', 'text': f"⚠️ {overloaded_count} Faculty members exceed session capacity limits."})
    if idle_count > (total_faculty * 0.2):
        insights.append({'type': 'info', 'text': f"💡 {idle_count} Faculty members are currently unassigned to sessions."})
    if this_month_growth > 5:
        insights.append({'type': 'growth', 'text': f"📈 Exceptional recruitment: {this_month_growth} new joiners this month."})

    data = {
        'total_faculty': total_faculty,
        'growth': {
            'value': this_month_growth,
            'percent': growth_percent,
            'trend': 'positive' if growth_percent >= 0 else 'negative'
        },
        'workload': {
            'total_sessions': total_sessions,
            'overloaded': overloaded_count,
            'idle': idle_count,
            'avg_sessions': round(total_sessions / total_faculty, 1) if total_faculty > 0 else 0
        },
        'academics': {
            'active_depts': active_depts,
            'top_dept': top_dept_name
        },
        'insights': insights[:3],
        'meta': {
            'confidence': f"Analyzed {total_sessions} timetable sessions",
            'server_time': timezone.now().isoformat()
        }
    }
    
    cache.set(cache_key, data, timeout=300)
    return data

def get_chart_faculty_distribution(college):
    """ Department Distribution (Horizontal Bar with Percentages) """
    cache_key = f'chart_faculty_dept_{college.id}'
    cached = cache.get(cache_key)
    if cached: return cached

    total_fac = Faculty.objects.filter(college=college, is_deleted=False).count()
    dept_qs = Faculty.objects.filter(college=college, is_deleted=False, department__isnull=False) \
                             .values('department__id', 'department__name') \
                             .annotate(count=Count('id')) \
                             .order_by('-count')[:6]
                             
    labels = []
    data_points = []
    ids = []
    for item in dept_qs:
        pct = round((item['count'] / total_fac) * 100) if total_fac > 0 else 0
        labels.append(f"{item['department__name']} ({pct}%)")
        data_points.append(item['count'])
        ids.append(item['department__id'])

    data = {
        "labels": labels,
        "data": data_points,
        "ids": ids,
        "meta": {"title": "Institutional Density"}
    }
    cache.set(cache_key, data, timeout=300)
    return data

def get_chart_faculty_designation(college):
    """ Designation Breakdown (KPI Donut Logic) """
    cache_key = f'chart_faculty_desig_{college.id}'
    cached = cache.get(cache_key)
    if cached: return cached

    desig_qs = Faculty.objects.filter(college=college, is_deleted=False, designation__isnull=False) \
                               .values('designation') \
                               .annotate(count=Count('id')) \
                               .order_by('-count')
    
    labels = [item['designation'] for item in desig_qs]
    data_points = [item['count'] for item in desig_qs]
    
    data = {
        "labels": labels,
        "data": data_points,
        "meta": {
            "title": "Designation Breakdown",
            "is_single": len(labels) == 1,
            "total": sum(data_points)
        }
    }
    cache.set(cache_key, data, timeout=300)
    return data
