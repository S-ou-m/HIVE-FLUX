from django.contrib import admin
from .models import (
    Room, SubjectAssignment, Timetable, TimetableSlot, 
    TimetableSlotInstance, AttendanceSession, EnrollmentMapping, 
    SessionEnrollmentSnapshot, ScanLog, Attendance, OperationsActivityLog
)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'capacity', 'floor')

@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'subject', 'semester', 'is_active')

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('program', 'semester', 'section', 'academic_year', 'version', 'is_active')

@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('timetable', 'day_of_week', 'start_time', 'end_time', 'assignment', 'room')

@admin.register(TimetableSlotInstance)
class TimetableSlotInstanceAdmin(admin.ModelAdmin):
    list_display = ('timetable_slot', 'date', 'status', 'expected_students', 'actual_students')

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('subject_snapshot_name', 'started_at', 'status', 'present_count')

@admin.register(EnrollmentMapping)
class EnrollmentMappingAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'semester', 'section', 'is_active')

admin.site.register(SessionEnrollmentSnapshot)
admin.site.register(ScanLog)
admin.site.register(Attendance)
admin.site.register(OperationsActivityLog)
