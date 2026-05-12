from django.db import models
from core.models import BaseModel, College

class AuditLog(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    record_id = models.UUIDField()
    timestamp = models.DateTimeField(auto_now_add=True)
