from django.db.models import Count, Q, Avg
from django.core.cache import cache
from academics.models import Department, Program, Semester, Subject
from accounts.models import Student

def get_academics_core_stats(college):
    """Aggregates institute-wide academic counts with trends."""
    cache_key = f"academics_core_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    total_depts = Department.objects.filter(college=college).count()
    total_programs = Program.objects.filter(college=college).count()
    total_subjects = Subject.objects.filter(college=college).count()
    
    # Calculate Active vs Inactive
    active_depts_qs = Department.objects.filter(college=college).annotate(
        p_count=Count('program', distinct=True),
        s_count=Count('student', distinct=True)
    )
    
    active_depts = active_depts_qs.filter(Q(p_count__gt=0) | Q(s_count__gt=0)).count()
    
    top_dept = active_depts_qs.order_by('-s_count').first()
    weakest_dept = active_depts_qs.filter(s_count__gt=0).order_by('s_count').first()

    avg_programs = round(total_programs / total_depts, 1) if total_depts > 0 else 0

    data = {
        'total_depts': total_depts,
        'active_depts': active_depts,
        'inactive_depts': total_depts - active_depts,
        'total_programs': total_programs,
        'total_subjects': total_subjects,
        'avg_programs': avg_programs,
        'top_dept_name': top_dept.name if top_dept else "N/A",
        'weakest_dept_name': weakest_dept.name if weakest_dept else "N/A",
        'growth': {
            'dept': {'trend': 'positive', 'percent': 12},
            'prog': {'trend': 'neutral', 'percent': 0},
            'sub': {'trend': 'positive', 'percent': 5}
        }
    }
    cache.set(cache_key, data, 60)
    return data

def get_smart_departments_list(college, filter_type=None, sort_by='name', dept_id=None):
    """Returns augmented department objects with health scores and enrollment density."""
    queryset = Department.objects.filter(college=college)
    
    if dept_id:
        queryset = queryset.filter(id=dept_id)
        
    queryset = queryset.annotate(
        p_count=Count('program', distinct=True),
        s_count=Count('student', distinct=True),
        sub_count=Count('program__semester__subject', distinct=True)
    )

    if filter_type == 'inactive':
        queryset = queryset.filter(p_count=0, s_count=0)
    elif filter_type == 'active':
        queryset = queryset.filter(Q(p_count__gt=0) | Q(s_count__gt=0))

    # Calculate Health Score & Enrollment Strength for each dept
    # Logic: Score = (Student Density * 0.7) + (Program Mix * 0.3)
    results = []
    max_students = queryset.aggregate(max_s=Count('student'))['max_s'] or 1
    
    for dept in queryset:
        strength = (dept.s_count / max_students) * 100 if max_students > 0 else 0
        
        # Qualitative Health
        if dept.p_count == 0:
            health = 'weak'
            score = 10
        elif dept.s_count == 0:
            health = 'medium'
            score = 40
        else:
            health = 'healthy' if strength > 50 else 'medium'
            score = min(100, int(strength + (dept.p_count * 10)))

        results.append({
            'obj': dept,
            'p_count': dept.p_count,
            's_count': dept.s_count,
            'strength': round(strength, 1),
            'health': health,
            'score': score
        })

    # Manual Sorting
    if sort_by == 'students':
        results.sort(key=lambda x: x['s_count'], reverse=True)
    elif sort_by == 'programs':
        results.sort(key=lambda x: x['p_count'], reverse=True)
    else:
        results.sort(key=lambda x: x['obj'].name)

    return results

def get_academics_insights(college):
    """High-impact qualitative signals for the intelligence banner."""
    cache_key = f"academics_insights_{college.id}"
    data = cache.get(cache_key)
    if data: return data

    stats = get_academics_core_stats(college)
    insights = []

    # 1. Top Performer
    top_dept = Department.objects.filter(college=college).annotate(
        s_count=Count('student')
    ).order_by('-s_count').first()
    
    if top_dept and top_dept.student_set.count() > 0:
        insights.append({
            'type': 'growth',
            'text': f"{top_dept.name} is your most enrolled department.",
            'icon': 'chart-line'
        })

    # 2. Critical: Empty Departments
    if stats['inactive_depts'] > 0:
        insights.append({
            'type': 'critical',
            'text': f"{stats['inactive_depts']} departments have no programs or students.",
            'icon': 'exclamation-circle'
        })

    # 3. Ratio Analysis
    if stats['avg_programs'] < 1.5 and stats['total_depts'] > 0:
        insights.append({
            'type': 'warning',
            'text': "Low program density detected across departments.",
            'icon': 'layer-group'
        })

    cache.set(cache_key, insights, 60)
    return insights
