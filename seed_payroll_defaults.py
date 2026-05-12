import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from finance.models import TaxRegime, TaxSlab, SalaryComponent, College

def seed_defaults():
    college = College.objects.first() # Seed for the first college found
    if not college:
        print("No college found. Create a college first.")
        return

    # 1. TAX REGIMES
    if not TaxRegime.objects.filter(college=college).exists():
        old_regime = TaxRegime.objects.create(
            college=college, name="Old Regime (FY 24-25)", 
            standard_deduction=50000, is_progressive=True
        )
        # Slabs for Old Regime (simplified)
        TaxSlab.objects.create(regime=old_regime, min_income=0, max_income=250000, tax_rate=0)
        TaxSlab.objects.create(regime=old_regime, min_income=250000, max_income=500000, tax_rate=5)
        TaxSlab.objects.create(regime=old_regime, min_income=500000, max_income=1000000, tax_rate=20)
        TaxSlab.objects.create(regime=old_regime, min_income=1000000, tax_rate=30)

        new_regime = TaxRegime.objects.create(
            college=college, name="New Regime (Default)", 
            standard_deduction=75000, is_progressive=True
        )
        # Slabs for New Regime
        TaxSlab.objects.create(regime=new_regime, min_income=0, max_income=300000, tax_rate=0)
        TaxSlab.objects.create(regime=new_regime, min_income=300000, max_income=700000, tax_rate=5)
        TaxSlab.objects.create(regime=new_regime, min_income=700000, max_income=1000000, tax_rate=10)
        TaxSlab.objects.create(regime=new_regime, min_income=1000000, tax_rate=15)
        print("Tax Regimes Seeded.")

    # 2. SALARY COMPONENTS
    components = [
        ('House Rent Allowance (HRA)', 'ALLOWANCE', 'PERCENTAGE', 40),
        ('Dearness Allowance (DA)', 'ALLOWANCE', 'PERCENTAGE', 50),
        ('Conveyance Allowance', 'ALLOWANCE', 'FIXED', 1600),
        ('Medical Allowance', 'ALLOWANCE', 'FIXED', 1250),
        ('Provident Fund (Employee)', 'DEDUCTION', 'PERCENTAGE', 12),
        ('Professional Tax', 'DEDUCTION', 'FIXED', 200),
    ]

    for name, type, calc, val in components:
        if not SalaryComponent.objects.filter(college=college, name=name).exists():
            SalaryComponent.objects.create(
                college=college, name=name, type=type, 
                calc_type=calc, default_value=val,
                visibility_scope='GLOBAL'
            )
    print("Salary Components Seeded.")

if __name__ == "__main__":
    seed_defaults()
