import random
from django.db.models import Avg

class FraudEngine:
    """
    Isolated engine for academic integrity signals.
    Future-ready for Plagiarism and LLM detection API integration.
    """

    @staticmethod
    def analyze_submission(submission):
        """
        Mock-Intelligent analysis for 'Unicorn' UI demonstration.
        In a real system, this would call external APIs.
        """
        # Simulated signals
        similarity = random.uniform(2, 45)
        ai_probability = random.uniform(0, 80)
        
        risk_level = 'LOW'
        needs_attention = False
        ai_state = 'ANALYZED'
        
        if similarity > 30 or ai_probability > 60:
            risk_level = 'HIGH'
            needs_attention = True
            ai_state = 'FLAGGED'
        elif similarity > 15:
            risk_level = 'MEDIUM'
            
        # Update submission signals
        submission.risk_level = risk_level
        submission.needs_attention = needs_attention
        submission.ai_state = ai_state
        submission.ai_confidence = random.uniform(0.7, 0.99)
        
        submission.fraud_signals = {
            "content_similarity": f"{similarity:.1f}%",
            "ai_pattern_match": f"{ai_probability:.1f}%",
            "time_anomaly": "None Detected",
            "metadata_status": "Verified"
        }
        
        submission.save()
        return submission

    @staticmethod
    def get_radar_summary(faculty, college):
        """Aggregates risk data for the Fraud Radar UI."""
        from lms.models import Submission
        from lms.services.evaluation_os.adapter import SubmissionIntelAdapter
        
        submissions = Submission.objects.filter(
            assignment__faculty=faculty,
            college=college
        )
        
        # Python-based aggregation for JSON compatibility (SQLite)
        similarity_scores = [
            SubmissionIntelAdapter.get_similarity_score(s) 
            for s in submissions 
            if s.fraud_signals
        ]
        
        avg_similarity = (sum(similarity_scores) / len(similarity_scores)) if similarity_scores else 0
        
        return {
            "critical_flags": submissions.filter(risk_level='CRITICAL').count(),
            "high_risk_avg": submissions.filter(risk_level='HIGH').count(),
            "avg_similarity": round(avg_similarity, 1)
        }
