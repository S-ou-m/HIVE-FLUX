from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Notification, Notice, NoticeReadStatus
from .services import NotificationService, NoticeService
from academics.models import Department, Semester
from .utils import get_targeted_notices

@login_required
def get_notifications_dropdown_partial(request):
    """
    Returns the notification dropdown partial content.
    Optionally generates insights before returning.
    """
    # For now, we generate insights on every dropdown open for demo purposes.
    # In production, this should be event-driven or cached.
    NotificationService.generate_system_insights(request.user, request.college)
    
    notifications = Notification.objects.filter(
        user=request.user, 
        college=request.college,
        is_read=False
    )[:10] # Limit to latest 10
    
    # Group by priority for the UI
    critical = [n for n in notifications if n.priority == 'CRITICAL']
    warning = [n for n in notifications if n.priority == 'WARNING']
    info = [n for n in notifications if n.priority == 'INFO']
    
    context = {
        'critical': critical,
        'warning': warning,
        'info': info,
        'total_new': notifications.count()
    }
    return render(request, 'dashboard/partials/notifications/dropdown.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Marks a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('HX-Target') == 'dashboard-content':
        return notification_center_view(request)
    return get_notifications_dropdown_partial(request)

@login_required
def delete_notification(request, notification_id):
    """Deletes a specific notification."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    if request.headers.get('HX-Target') == 'dashboard-content':
        return notification_center_view(request)
    return get_notifications_dropdown_partial(request)

from django.urls import reverse
from django.shortcuts import redirect

@login_required
def mark_all_notifications_read(request):
    """Marks all unread notifications for the user/tenant as read."""
    Notification.objects.filter(user=request.user, college=request.college, is_read=False).update(is_read=True)
    if request.headers.get('HX-Request'):
        return notification_center_view(request)
    return redirect('notification_center')

@login_required
def notification_settings_view(request):
    """Returns the notification settings partial or updates preferences."""
    from .models import NotificationPreference
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        prefs.email_notifications = request.POST.get('email_notifications') == 'on'
        prefs.in_app_notifications = request.POST.get('in_app_notifications') == 'on'
        prefs.finance_alerts = request.POST.get('finance_alerts') == 'on'
        prefs.academic_alerts = request.POST.get('academic_alerts') == 'on'
        prefs.student_alerts = request.POST.get('student_alerts') == 'on'
        prefs.system_alerts = request.POST.get('system_alerts') == 'on'
        prefs.save()
        return render(request, 'dashboard/partials/notifications/settings.html', {
            'prefs': prefs, 
            'success': True
        })

    return render(request, 'dashboard/partials/notifications/settings.html', {'prefs': prefs})

@login_required
def notification_center_view(request):
    """
    Returns the full Notification Center with support for filtering.
    """
    if not request.headers.get('HX-Request'):
        context = {
            'college': request.college,
            'user': request.user,
            'college_name': request.college.name if request.college else "System Admin",
            'user_role': "Administrator",
            'username': request.user.get_full_name() or request.user.username,
            'initial_load_url': reverse('notification_center')
        }
        return render(request, 'dashboard/admin_master.html', context)

    notifications = Notification.objects.filter(user=request.user, college=request.college)
    
    # Apply Filters from GET parameters
    f_type = request.GET.get('type')
    f_priority = request.GET.get('priority')
    f_unread = request.GET.get('unread')

    if f_type:
        notifications = notifications.filter(type=f_type.upper())
    if f_priority:
        notifications = notifications.filter(priority=f_priority.upper())
    if f_unread == 'true':
        notifications = notifications.filter(is_read=False)

    notifications = notifications.order_by('-created_at')
    
    # Determine active filter label for UI
    active_filter = 'all'
    if f_unread: active_filter = 'unread'
    elif f_priority: active_filter = f_priority.lower()
    elif f_type: active_filter = f_type.lower()

    return render(request, 'dashboard/views/notifications/center.html', {
        'notifications': notifications,
        'active_filter': active_filter
    })

# --- Notice Center Views ---

@login_required
def notice_center_view(request):
    """
    Main entry point for the Notice Center.
    """
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.userrole_set.filter(role__name='Admin').exists()
    user_role = "Administrator" if is_admin else "User"
    
    if not request.headers.get('HX-Request'):
        context = {
            'college': request.college,
            'user': request.user,
            'username': request.user.get_full_name() or request.user.username,
            'user_role': user_role,
            'initial_load_url': reverse('notice_center')
        }
        return render(request, 'dashboard/admin_master.html', context)
    
    # Pre-fetch notices for initial render
    notices = get_targeted_notices(request.user, request.college).order_by('-published_at')
    return render(request, 'dashboard/views/communication/notice_center.html', {
        'user_role': user_role,
        'notices': notices
    })

@login_required
def notice_list_partial(request):
    """
    Returns the filtered list of notices for the user.
    """
    notices = get_targeted_notices(request.user, request.college)
    
    # Apply UI Filters (Type, Priority, Unread)
    f_type = request.GET.get('type')
    f_priority = request.GET.get('priority')
    f_unread = request.GET.get('unread')

    if f_type:
        notices = notices.filter(notice_type=f_type.upper())
    if f_priority:
        notices = notices.filter(priority=f_priority.upper())
    if f_unread == 'true':
        read_ids = NoticeReadStatus.objects.filter(user=request.user).values_list('notice_id', flat=True)
        notices = notices.exclude(id__in=read_ids)

    notices = notices.order_by('-published_at')
    
    # Add 'is_read' attribute to each notice for the template
    read_notice_ids = set(NoticeReadStatus.objects.filter(user=request.user).values_list('notice_id', flat=True))
    for n in notices:
        n.is_read = n.id in read_notice_ids

    # Determine user role for template permissions
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.userrole_set.filter(role__name='Admin').exists()
    user_role = "Administrator" if is_admin else "User"

    return render(request, 'dashboard/partials/communication/notice_list.html', {
        'notices': notices,
        'active_filter': request.GET.get('filter', 'all'),
        'user_role': user_role
    })

@login_required
def create_notice_view(request):
    """
    Handles notice creation by administrators.
    """
    # Permission Check: Admin, Staff, or Superuser
    if not (request.user.is_staff or request.user.is_superuser or request.user.userrole_set.filter(role__name='Admin').exists()):
        return render(request, 'dashboard/partials/common/error_toast.html', {'message': 'Unauthorized'})

    if request.method == 'POST':
        # Extract data from the high-fidelity drawer form
        title = request.POST.get('title')
        content = request.POST.get('content')
        n_type = request.POST.get('notice_type', 'ANNOUNCEMENT')
        priority = request.POST.get('priority', 'IMPORTANT')
        target_role = request.POST.get('target_role', 'ALL')
        dept_ids = request.POST.getlist('departments')
        
        # Create Notice
        notice = Notice.objects.create(
            college=request.college,
            title=title,
            content=content,
            notice_type=n_type,
            priority=priority,
            target_roles=[target_role] if target_role != 'ALL' else [],
            created_by=request.user,
            status='PUBLISHED',
            published_at=timezone.now()
        )
        
        if dept_ids:
            notice.target_departments.add(*dept_ids)
            
        # Trigger Push Notifications via Service
        NoticeService.publish_notice(notice)
        
        # Return the updated list partial with professional feedback
        import json
        response = notice_list_partial(request)
        response['HX-Trigger'] = json.dumps({
            "showToast": {
                "message": "Broadcast Payload Deployed Successfully",
                "type": "success"
            },
            "noticeRead": {} # Refresh sidebar counts
        })
        return response

    # GET returns the premium drawer content
    context = {
        'departments': Department.objects.filter(college=request.college),
        'semesters': Semester.objects.filter(college=request.college),
    }
    return render(request, 'dashboard/partials/communication/create_notice_modal.html', context)

@login_required
def mark_notice_read(request, notice_id):
    """
    Marks a notice as read by the user.
    """
    notice = get_object_or_404(Notice, id=notice_id)
    NoticeReadStatus.objects.get_or_create(user=request.user, notice=notice)
    
    is_admin = request.user.is_staff or request.user.is_superuser or request.user.userrole_set.filter(role__name='Admin').exists()
    user_role = "Administrator" if is_admin else "User"

    response = HttpResponse()
    if request.headers.get('HX-Request'):
        # Return the updated card partial for direct DOM replacement
        response = render(request, 'dashboard/partials/communication/notice_card.html', {
            'notice': notice,
            'is_read': True,
            'user_role': user_role
        })
    else:
        response = notice_list_partial(request)

    # Add a trigger to refresh UI and show feedback
    import json
    response['HX-Trigger'] = json.dumps({
        "noticeRead": {},
        "showToast": {
            "message": "Notice Acknowledged",
            "type": "success"
        }
    })
    return response

@login_required
def get_critical_banner(request):
    """
    Returns a sticky top banner if there's an unread critical notice.
    """
    read_ids = NoticeReadStatus.objects.filter(user=request.user).values_list('notice_id', flat=True)
    
    # Re-use targeting logic or simplify for banner
    critical_notice = Notice.objects.filter(
        college=request.college,
        priority='CRITICAL',
        status='PUBLISHED'
    ).exclude(id__in=read_ids).first()
    
    if not critical_notice:
        return HttpResponse("") # Empty response if no critical notice

    return render(request, 'dashboard/partials/communication/critical_banner.html', {
        'notice': critical_notice
    })
@login_required
def get_notice_sidebar_counts(request):
    """
    Returns a partial containing only the count badges for the sidebar.
    """
    notices = get_targeted_notices(request.user, request.college)
    read_ids = NoticeReadStatus.objects.filter(user=request.user).values_list('notice_id', flat=True)
    
    unread_count = notices.exclude(id__in=read_ids).count()
    critical_count = notices.filter(priority='CRITICAL').exclude(id__in=read_ids).count()
    total_count = notices.count()
    
    return render(request, 'dashboard/partials/communication/sidebar_counts.html', {
        'unread_count': unread_count,
        'critical_count': critical_count,
        'total_count': total_count
    })

@login_required
def notice_read_receipts(request, notice_id):
    """
    Returns a modal showing who has read the notice.
    """
    if not request.user.userrole_set.filter(role__name='Admin').exists():
        return HttpResponse("Unauthorized", status=403)
        
    notice = get_object_or_404(Notice, id=notice_id)
    read_statuses = NoticeReadStatus.objects.filter(notice=notice).select_related('user').order_by('-read_at')
    
    return render(request, 'dashboard/partials/communication/read_receipts_modal.html', {
        'notice': notice,
        'read_statuses': read_statuses,
        'total_read': read_statuses.count()
    })
