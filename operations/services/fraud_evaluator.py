import logging
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from operations.models import ScanLog
from operations.events import EventDispatcher, FRAUD_DETECTED

logger = logging.getLogger(__name__)

class FraudEvaluator:
    """
    Analyzes ScanLogs to detect proxy attendance and anomalous behavior.
    """

    @classmethod
    def evaluate_scan(cls, scan_id):
        """
        Main entry point for evaluating a new scan.
        """
        scan = ScanLog.objects.select_related('session', 'user').get(id=scan_id)
        
        reasons = []
        score_penalty = 0.0

        # 1. Device Sharing Check (Multi-user per device)
        # Check if this device has scanned for different users in the last 1 hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        unique_users = ScanLog.objects.filter(
            device_id=scan.device_id,
            scanned_at__gte=one_hour_ago
        ).exclude(user=scan.user).values('user').distinct().count()

        if unique_users > 0:
            reasons.append(f"Device shared by {unique_users + 1} users")
            score_penalty += 0.4 * unique_users # High penalty for device sharing

        # 2. Impossible Velocity (Future: Check location drift)
        
        # 3. Proxy/VPN Check (Simplified)
        # If the same IP is used by many users simultaneously
        unique_ips = ScanLog.objects.filter(
            ip_address=scan.ip_address,
            scanned_at__gte=one_hour_ago
        ).exclude(user=scan.user).values('user').distinct().count()
        
        if unique_ips > 5:
            reasons.append(f"IP address shared by {unique_ips + 1} users (Possible Proxy)")
            score_penalty += 0.2

        # 4. Final Score Calculation
        scan.confidence_score = max(0.0, 1.0 - score_penalty)
        
        if scan.confidence_score < 0.5:
            scan.proxy_flag = True
            logger.warning(f"[FRAUD_ALERT] User {scan.user} | Session {scan.session.id} | Score: {scan.confidence_score} | Reasons: {reasons}")
            
            EventDispatcher.dispatch(FRAUD_DETECTED, scan.college.id, {
                'scan_id': str(scan.id),
                'user_id': str(scan.user.id),
                'session_id': str(scan.session.id),
                'reasons': reasons
            })
        
        scan.save()
        return scan.confidence_score
