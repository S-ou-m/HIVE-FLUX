from django import forms
from .models import FeeStructure, Invoice, Payment, SalaryProfile

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['program', 'semester', 'amount', 'effective_from']
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Amount'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount_paid', 'mode', 'reference_id']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount to Pay'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
            'reference_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID / Ref'}),
        }

class SalaryProfileForm(forms.ModelForm):
    class Meta:
        model = SalaryProfile
        fields = ['faculty', 'base_salary', 'effective_from', 'is_template_linked', 'template']
        widgets = {
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'effective_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
        }


class BatchInvoiceForm(forms.Form):
    program = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-control'}))
    semester = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-control'}))
    fee_structure = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-control'}))
    due_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    admission_year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Batch Year'}))
    skip_existing = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from academics.models import Program, Semester
            from .models import FeeStructure
            self.fields['program'].queryset = Program.objects.filter(college=college)
            self.fields['semester'].queryset = Semester.objects.filter(college=college)
            self.fields['fee_structure'].queryset = FeeStructure.objects.filter(college=college, is_active=True)
