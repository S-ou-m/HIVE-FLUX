from django import forms
from accounts.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

class StudentOnboardingForm(forms.Form):
    # Step 1: Personal Info
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': 'required'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': 'required'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'required': 'required'}))
    phone_no = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900', 'required': 'required'}))

    # Step 2: Academic Info
    enrollment_no = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'style': 'background-color: rgba(255,255,255,0.05); cursor: not-allowed; color: var(--color-orange);'}))
    admission_year = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}))
    department = forms.ModelChoiceField(queryset=None, empty_label="Select Department", widget=forms.Select(attrs={
        'class': 'form-control', 
        'required': 'required',
        'hx-get': '/dashboard/admin/partial/academics/semesters/load/',
        'hx-target': '#id_current_semester'
    }))
    current_semester = forms.ModelChoiceField(queryset=None, empty_label="Select Semester", widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}))

    # Step 3: Guardian Info
    guardian_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Name', 'required': 'required'}))
    guardian_relation = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Father', 'required': 'required'}))
    guardian_phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Phone', 'required': 'required'}))
    guardian_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Email (Optional)'}))

    # Step 4: Address
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address', 'required': 'required'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'required': 'required'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'required': 'required'}))
    pincode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP / Pincode', 'required': 'required'}))

    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from academics.models import Department, Semester
            self.fields['department'].queryset = Department.objects.filter(college=college)
            
            # Default to empty, then try to fill based on POST data OR Initial data (for Edit mode)
            self.fields['current_semester'].queryset = Semester.objects.none()
            
            # 1. Check POST data (for dynamic HTMX or Submission)
            dept_id = self.data.get('department')
            
            # 2. If no POST data, check Initial data (for Edit mode)
            if not dept_id and self.initial.get('department'):
                dept_id = self.initial.get('department')
                # If it's a model instance, get the ID
                if hasattr(dept_id, 'id'):
                    dept_id = dept_id.id

            if dept_id:
                try:
                    self.fields['current_semester'].queryset = Semester.objects.filter(program__department_id=dept_id)
                except (ValueError, TypeError):
                    pass

class FacultyOnboardingForm(forms.Form):
    # Step 1: Personal Info
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': 'required'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': 'required'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'required': 'required'}))
    phone_no = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900', 'required': 'required'}))

    # Step 2: Professional Details
    department = forms.ModelChoiceField(queryset=None, empty_label="Select Department", widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}))
    designation = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Professor', 'required': 'required'}))

    # Step 3: Address
    address_line1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address', 'required': 'required'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'required': 'required'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'required': 'required'}))
    pincode = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP / Pincode', 'required': 'required'}))

    # Step 4: Account Status
    is_active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from academics.models import Department
            self.fields['department'].queryset = Department.objects.filter(college=college)
