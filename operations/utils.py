import hashlib
import json
import uuid
from django.utils import timezone
import datetime

class QRGenerator:
    """
    SaaS-Grade Secure QR Generator.
    Binds identity to a short-lived signed token.
    """
    SECRET_KEY = "IIT_GRADE_SECRET_2026"

    @staticmethod
    def generate_student_payload(user):
        user_id = str(user.id)
        issued_at = timezone.now().isoformat()
        nonce = str(uuid.uuid4())
        
        payload = f"{user_id}{issued_at}{nonce}"
        signature = hashlib.sha256(f"{payload}{QRGenerator.SECRET_KEY}".encode()).hexdigest()
        
        return json.dumps({
            "user_id": user_id,
            "issued_at": issued_at,
            "nonce": nonce,
            "signature": signature
        })
