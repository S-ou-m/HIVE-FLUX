from django import forms
from .models import Department, Program, Semester, Subject

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science Engineering'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CSE'})
        }

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'duration_years', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B.Tech Computer Science'}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 4'}),
            'department': forms.Select(attrs={'class': 'form-control'})
        }

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['number', 'program'] # Changed from course to program
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1'}),
            'program': forms.Select(attrs={'class': 'form-control'})
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'credits', 'semester']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Data Structures'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 4'}),
            'semester': forms.Select(attrs={'class': 'form-control'})
        }
