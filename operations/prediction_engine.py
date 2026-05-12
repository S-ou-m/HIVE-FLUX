from django.db.models import Q
from .models import Attendance, AttendanceSession

class PredictionEngine:
    @staticmethod
    def analyze_student_risk(student, upcoming_sessions_window=7):
        """
        Analyzes a student's attendance to forecast risk level.
        Returns a dictionary with current, projected, trend, and severity.
        """
        base_query = Attendance.objects.filter(student=student)
        total_sessions_held = base_query.count()
        
        if total_sessions_held == 0:
            return {
                "current_attendance": 100,
                "projected_attendance": 100,
                "severity": "NONE",
                "trend": "STABLE"
            }
            
        present_count = base_query.filter(
            Q(status='PRESENT') | Q(status='LATE') | Q(status='ON_DUTY')
        ).count()
        
        current_attendance = round((present_count / total_sessions_held) * 100, 2)
        
        # Projected Attendance: If they miss the next `upcoming_sessions_window` sessions
        projected_attendance = round((present_count / (total_sessions_held + upcoming_sessions_window)) * 100, 2)
        
        # Determine Severity based on Projected Attendance
        if projected_attendance < 60:
            severity = "HIGH"
        elif 60 <= projected_attendance < 70:
            severity = "MEDIUM"
        elif 70 <= projected_attendance < 75:
            severity = "LOW"
        else:
            severity = "NONE"
            
        # Determine Trend (In a real system, compare to last week's rolling average)
        # For prototype, if projected is significantly lower, it's DOWN
        trend = "DOWN" if (current_attendance - projected_attendance) > 2 else "STABLE"
        
        return {
            "current_attendance": current_attendance,
            "projected_attendance": projected_attendance,
            "severity": severity,
            "trend": trend,
            "total_attended": present_count,
            "total_held": total_sessions_held
        }
