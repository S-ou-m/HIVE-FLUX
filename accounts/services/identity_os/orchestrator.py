import hmac
import hashlib
import time
import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from accounts.models import IdentitySession, TrustedDevice, IdentityScanEvent

class IdentityOrchestrator:
    """
    Central authority for institutional identity sessions and token security.
    """
    
    ROTATION_INTERVAL = 60 # Seconds
    OVERLAP_WINDOW = 15    # Seconds for transition safety
    
    def __init__(self, user, device_id=None):
        self.user = user
        self.device_id = device_id
        
    def get_or_create_session(self, browser_sig=None, platform=None):
        """
        Retrieves or initializes a secure IdentitySession pinned to a device.
        """
        device = None
        if self.device_id:
            device, _ = TrustedDevice.objects.get_or_create(
                device_id=self.device_id,
                user=self.user,
                defaults={
                    'browser_signature': browser_sig or "Unknown",
                    'platform': platform or "Unknown"
                }
            )
            
        # Check for existing active session
        session = IdentitySession.objects.filter(
            user=self.user, 
            device=device,
            status='ACTIVE',
            expires_at__gt=timezone.now()
        ).first()
        
        if not session:
            # Create fresh session with a new rotation seed
            session = IdentitySession.objects.create(
                user=self.user,
                device=device,
                expires_at=timezone.now() + timedelta(hours=12), # Operational shift length
                trust_score=self.calculate_initial_trust(device)
            )
            
        return session

    def calculate_initial_trust(self, device):
        """Calculates trust score based on device history."""
        if not device: return 30 # Low trust for anonymous/new devices
        if device.trust_state == 'TRUSTED': return 90
        if device.trust_state == 'BANNED': return 0
        return 50 # Provisional

    def generate_signed_token(self, session):
        """
        Generates an HMAC-SHA256 signed payload for the rotating QR.
        """
        timestamp = int(time.time())
        # Use rotation seed + timestamp rounded to interval to ensure stability
        # We round down to the nearest interval for the 'current' token
        current_interval = timestamp - (timestamp % self.ROTATION_INTERVAL)
        
        payload = f"{session.id}:{session.rotation_seed}:{current_interval}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'token': f"{payload}:{signature[:16]}", # Truncated sig for QR density
            'expires_in': self.ROTATION_INTERVAL - (timestamp % self.ROTATION_INTERVAL),
            'trust_score': session.trust_score
        }

    def verify_token(self, raw_token, terminal):
        """
        Verifies a scanned token against active sessions and overlap windows.
        """
        try:
            sid, seed, interval, sig = raw_token.split(':')
            session = IdentitySession.objects.get(id=sid, status='ACTIVE')
            
            # Verify Signature
            expected_payload = f"{sid}:{seed}:{interval}"
            expected_sig = hmac.new(
                settings.SECRET_KEY.encode(),
                expected_payload.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(sig, expected_sig):
                return self.log_failure(session, terminal, "INVALID_SIGNATURE")

            # Verify Time Window (Allow for rotation interval + overlap)
            token_time = int(interval)
            current_time = int(time.time())
            if current_time - token_time > (self.ROTATION_INTERVAL + self.OVERLAP_WINDOW):
                return self.log_failure(session, terminal, "EXPIRED_TOKEN")

            # Log Success
            IdentityScanEvent.objects.create(
                session=session,
                terminal=terminal,
                event_type='IDENTITY_REFRESH' if terminal.terminal_type == 'INTERNAL' else 'CHECK_IN',
                verification_state='SUCCESS'
            )
            
            return True, session
            
        except Exception as e:
            return False, str(e)

    def log_failure(self, session, terminal, reason):
        IdentityScanEvent.objects.create(
            session=session,
            terminal=terminal,
            event_type='FAILED_ATTEMPT',
            verification_state=reason
        )
        # Decay trust score on failure
        session.trust_score = max(0, session.trust_score - 10)
        session.save()
        return False, reason
