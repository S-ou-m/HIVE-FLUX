from django.db.models import Avg, Count
from django.utils import timezone

class ProductivityEngine:
    """
    Analytics engine for faculty evaluation performance.
    """

    @staticmethod
    def get_velocity_metrics(faculty, college):
        """Calculates throughput and speed signals."""
        from lms.models import Submission
        
        # Recent activity (Last 7 days)
        last_week = timezone.now() - timezone.timedelta(days=7)
        recent_subs = Submission.objects.filter(
            assignment__faculty=faculty,
            college=college,
            reviewed_at__gte=last_week
        )
        
        total_reviewed = recent_subs.count()
        avg_duration = recent_subs.aggregate(Avg('review_duration_seconds'))['review_duration_seconds__avg'] or 0
        
        # Convert seconds to human readable (e.g., 4.5m / paper)
        velocity_label = f"{avg_duration / 60:.1f}m / paper" if avg_duration > 0 else "N/A"
        
        return {
            "weekly_throughput": total_reviewed,
            "avg_review_speed": velocity_label,
            "consistency_score": "High" if total_reviewed > 10 else "Developing"
        }

    @staticmethod
    def get_grading_heatmap(faculty, college):
        """Simulated heatmap data for the UI."""
        # In a real app, this would be a daily count aggregation
        return [
            {"day": "Mon", "count": 12},
            {"day": "Tue", "count": 28},
            {"day": "Wed", "count": 8},
            {"day": "Thu", "count": 15},
            {"day": "Fri", "count": 22},
            {"day": "Sat", "count": 5},
            {"day": "Sun", "count": 2},
        ]
