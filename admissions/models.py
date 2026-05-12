from django.db import models
from core.models import BaseModel, College

class Application(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    applied_program = models.ForeignKey('academics.Program', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.student_name} - {self.applied_program.name if self.applied_program else 'No Program'}"

class DocumentType(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Document(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    file_url = models.CharField(max_length=500)
    verified = models.BooleanField(default=False)
    status = models.CharField(max_length=50)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

class StudentDocument(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    file_url = models.CharField(max_length=500)
    status = models.CharField(max_length=50)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

class VerificationWorkflow(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class VerificationStep(BaseModel):
    workflow = models.ForeignKey(VerificationWorkflow, on_delete=models.CASCADE)
    step_order = models.IntegerField()
    role = models.ForeignKey('accounts.Role', on_delete=models.CASCADE)

class VerificationLog(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    step = models.ForeignKey(VerificationStep, on_delete=models.CASCADE)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50)
    remarks = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
