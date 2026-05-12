from django.db import models
from django.conf import settings
from core.models import BaseModel, College

class FeeStructure(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    program = models.ForeignKey('academics.Program', on_delete=models.CASCADE, null=True, blank=True)
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE)
    amount = models.FloatField()
    breakdown = models.JSONField(default=dict, help_text="Structured breakdown: {'tuition': 40000, 'lab': 5000, ...}")
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.program} - {self.semester} (₹{self.amount})"

class Invoice(BaseModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, null=True)
    
    # Enterprise Identity Fields
    invoice_type = models.CharField(max_length=50, default='SEMESTER_FEE')
    is_auto_generated = models.BooleanField(default=False)
    
    total_amount = models.FloatField()
    paid_amount = models.FloatField(default=0.0)
    due_date = models.DateField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    issued_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'semester', 'invoice_type'], 
                name='unique_invoice_per_semester',
                condition=models.Q(is_deleted=False) # Respect soft delete
            )
        ]
        indexes = [
            models.Index(fields=['status']),
        ]

    def _invalidate_analytics_cache(self):
        from django.core.cache import cache
        cache.delete(f'student_core_stats_{self.college_id}')
        cache.delete(f'chart_finance_{self.college_id}')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._invalidate_analytics_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._invalidate_analytics_cache()

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    def __str__(self):
        return f"INV-{self.id} - {self.student.user.get_full_name()}"

class Payment(BaseModel):
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True)
    amount_paid = models.FloatField()
    payment_date = models.DateField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='CASH')
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='SUCCESS')

    def _invalidate_analytics_cache(self):
        from django.core.cache import cache
        cache.delete(f'student_core_stats_{self.college_id}')
        cache.delete(f'chart_finance_{self.college_id}')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._invalidate_analytics_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._invalidate_analytics_cache()

    def __str__(self):
        return f"PAY-{self.id} (₹{self.amount_paid})"

class Account(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50) # Asset, Liability, Income, Expense

class LedgerEntry(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = models.FloatField(default=0.0)
    credit = models.FloatField(default=0.0)
    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=50) # Invoice, Payment, Payroll
    reference_id = models.UUIDField(null=True, blank=True)

class Expense(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.FloatField()
    expense_date = models.DateField()
    department = models.ForeignKey('academics.Department', on_delete=models.CASCADE)

class SalaryComponent(BaseModel):
    TYPE_CHOICES = [('ALLOWANCE', 'Allowance'), ('DEDUCTION', 'Deduction')]
    CALC_CHOICES = [('FIXED', 'Fixed Amount'), ('PERCENTAGE', 'Percentage')]
    SCOPE_CHOICES = [('BASE', 'Base Salary'), ('GROSS', 'Gross Salary'), ('CUSTOM', 'Custom')]
    IMPACT_CHOICES = [('NET', 'Affects Net Salary'), ('CTC_ONLY', 'Employer Contribution (CTC Only)')]
    VISIBILITY_CHOICES = [('GLOBAL', 'Global (Auto-Applied)'), ('TEMPLATE', 'Template Only'), ('PROFILE', 'Profile Only')]

    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    calc_type = models.CharField(max_length=20, choices=CALC_CHOICES, default='FIXED')
    calculation_scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='BASE')
    impact_type = models.CharField(max_length=20, choices=IMPACT_CHOICES, default='NET')
    priority = models.IntegerField(default=0, help_text="Order of calculation")
    visibility_scope = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='TEMPLATE')
    default_value = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class SalaryTemplate(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class TemplateComponent(BaseModel):
    template = models.ForeignKey(SalaryTemplate, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    value = models.FloatField() # % or ₹ depending on component

class TaxRegime(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=100) # e.g., "Old Regime 2024", "New Regime"
    standard_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=50000)
    rebate_limit = models.DecimalField(max_digits=10, decimal_places=2, default=500000)
    rebate_amount = models.DecimalField(max_digits=10, decimal_places=2, default=12500)
    is_progressive = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.college.name})"

class TaxSlab(BaseModel):
    regime = models.ForeignKey(TaxRegime, on_delete=models.CASCADE, related_name='slabs')
    min_income = models.DecimalField(max_digits=12, decimal_places=2)
    max_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2) # e.g., 5.00 for 5%
    priority = models.IntegerField(default=10)

    class Meta:
        ordering = ['min_income']

    def __str__(self):
        return f"{self.regime.name}: {self.min_income} - {self.max_income} @ {self.tax_rate}%"

class SalaryProfile(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE, related_name='salary_profiles')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_template_linked = models.BooleanField(default=False)
    template = models.ForeignKey(SalaryTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    tax_regime = models.ForeignKey(TaxRegime, on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='salary_profile_updates')

    def __str__(self):
        return f"Profile: {self.faculty.user.get_full_name()}"

class ProfileComponent(BaseModel):
    profile = models.ForeignKey(SalaryProfile, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    value_override = models.FloatField() # % or ₹

class Payroll(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LOCKED', 'Locked'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]
    PAYMENT_MODES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    faculty = models.ForeignKey('accounts.Faculty', on_delete=models.CASCADE)
    month = models.IntegerField() 
    year = models.IntegerField()
    base_salary = models.FloatField(default=0.0)
    gross_salary = models.FloatField()
    deductions = models.FloatField()
    net_salary = models.FloatField()
    ctc_amount = models.FloatField(default=0.0)
    breakdown_json = models.JSONField(default=dict, help_text="Audit-frozen snapshot of all components")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='BANK_TRANSFER')
    locked_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payroll_updates')
    remarks = models.TextField(null=True, blank=True)

class Payslip(BaseModel):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    file_url = models.CharField(max_length=500)

class PayrollRunBatch(BaseModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_log = models.JSONField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    def __str__(self):
        return f'Batch {self.month}/{self.year} - {self.status}'

class RefundRequest(BaseModel):
    """Governance for financial reversals and student refunds."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='refunds')
    
    amount = models.FloatField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    eta_completion = models.DateField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Refund: {self.student.user.first_name} (₹{self.amount})"

