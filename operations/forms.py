from django import forms
from .models import Timetable, Room, SubjectAssignment, TimetableSlot
from accounts.models import Faculty
from academics.models import Subject, Semester

class WorkloadForm(forms.ModelForm):
    # Assignment Fields
    faculty = forms.ModelChoiceField(queryset=Faculty.objects.none())
    subject = forms.ModelChoiceField(queryset=Subject.objects.none())
    semester = forms.ModelChoiceField(queryset=Semester.objects.none(), required=False)
    
    # Timetable Context
    timetable = forms.ModelChoiceField(queryset=Timetable.objects.none(), label="Target Batch/Timetable")

    class Meta:
        model = TimetableSlot
        fields = ['timetable', 'day_of_week', 'start_time', 'end_time', 'room', 'slot_type']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['faculty'].queryset = Faculty.objects.filter(college=college)
            self.fields['subject'].queryset = Subject.objects.filter(college=college)
            self.fields['semester'].queryset = Semester.objects.filter(college=college)
            self.fields['timetable'].queryset = Timetable.objects.filter(college=college)
            self.fields['room'].queryset = Room.objects.filter(college=college)

    def save(self, commit=True):
        # 1. Get or Create the SubjectAssignment
        assignment, created = SubjectAssignment.objects.get_or_create(
            college=self.instance.timetable.college if self.instance.pk else self.fields['faculty'].queryset.first().college,
            faculty=self.cleaned_data['faculty'],
            subject=self.cleaned_data['subject'],
            semester=self.cleaned_data['semester'],
        )
        
        # 2. Attach assignment to the slot
        instance = super().save(commit=False)
        instance.assignment = assignment
        
        if commit:
            instance.save()
        return instance

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['department', 'program', 'semester', 'section', 'academic_year', 'effective_from']
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            from academics.models import Department, Program, Semester
            self.fields['department'].queryset = Department.objects.filter(college=college)
            self.fields['program'].queryset = Program.objects.filter(college=college)
            self.fields['semester'].queryset = Semester.objects.filter(college=college)
