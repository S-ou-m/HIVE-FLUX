from django.contrib import admin
from .models import (
    FeeStructure, Payment, Invoice, Account, LedgerEntry, Expense, 
    SalaryComponent, SalaryTemplate, TemplateComponent, SalaryProfile, 
    ProfileComponent, Payroll, Payslip
)

admin.site.register(FeeStructure)
admin.site.register(Payment)
admin.site.register(Invoice)
admin.site.register(Account)
admin.site.register(LedgerEntry)
admin.site.register(Expense)
admin.site.register(SalaryComponent)
admin.site.register(SalaryTemplate)
admin.site.register(TemplateComponent)
admin.site.register(SalaryProfile)
admin.site.register(ProfileComponent)
admin.site.register(Payroll)
admin.site.register(Payslip)
