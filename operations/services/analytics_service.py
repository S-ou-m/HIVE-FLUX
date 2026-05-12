import logging
from django.db import transaction
from operations.models import FacultyWorklog, AttendanceSession

logger = logging.getLogger(__name__)

def sync_faculty_worklog(event):
    """
    Consumer for SESSION_COMPLETED event.
    Updates the FacultyWorklog snapshot atomically.
    """
    try:
        session_id = event.data.get('session_id')
        faculty_id = event.data.get('faculty_id')
        college_id = event.college_id
        date = event.timestamp.date()

        with transaction.atomic():
            worklog, created = FacultyWorklog.objects.select_for_update().get_or_create(
                college_id=college_id,
                faculty_id=faculty_id,
                date=date
            )
            
            # Atomic Increments
            worklog.completed_sessions += 1
            
            # Track source session for audit
            if session_id not in worklog.source_sessions:
                worklog.source_sessions.append(session_id)
                
            worklog.save()
            logger.info(f"Updated Worklog for Faculty {faculty_id} | Date: {date}")
            
    except Exception as e:
        logger.error(f"Failed to sync FacultyWorklog: {str(e)}")
