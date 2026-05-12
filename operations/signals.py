from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import ScanLog, AttendanceSession, Attendance

from django.template.loader import render_to_string

@receiver(post_save, sender=ScanLog)
def broadcast_scan_log(sender, instance, created, **kwargs):
    if created and instance.result == 'SUCCESS':
        channel_layer = get_channel_layer()
        faculty_id = instance.session.session_owner.user.id
        
        html = render_to_string('dashboard/partials/realtime_updates.html', {
            'event': 'scan_success',
            'student_name': instance.user.get_full_name(),
            'timestamp': instance.scanned_at.strftime('%H:%M:%S'),
            'message': f"Successful scan by {instance.user.get_full_name()}"
        })
        
        async_to_sync(channel_layer.group_send)(
            f"faculty_{faculty_id}",
            {
                "type": "broadcast_update",
                "payload": html
            }
        )

@receiver(post_save, sender=AttendanceSession)
def broadcast_session_status(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    faculty_id = instance.session_owner.user.id
    
    html = render_to_string('dashboard/partials/realtime_updates.html', {
        'event': 'session_status_change',
        'status': instance.status,
        'initials': instance.session_owner.user.get_full_name()[:2].upper() # Fallback initials
    })
    
    async_to_sync(channel_layer.group_send)(
        f"faculty_{faculty_id}",
        {
            "type": "broadcast_update",
            "payload": html
        }
    )
