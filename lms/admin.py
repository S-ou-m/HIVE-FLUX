from django.contrib import admin
from .models import Assignment, Submission, Exam, Marks, Grade

admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Exam)
admin.site.register(Marks)
admin.site.register(Grade)
