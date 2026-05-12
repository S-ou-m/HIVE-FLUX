from django.contrib import admin
from .models import Application, DocumentType, Document, StudentDocument, VerificationWorkflow, VerificationStep, VerificationLog

admin.site.register(Application)
admin.site.register(DocumentType)
admin.site.register(Document)
admin.site.register(StudentDocument)
admin.site.register(VerificationWorkflow)
admin.site.register(VerificationStep)
admin.site.register(VerificationLog)
