import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from accounts.models import Faculty
from finance.models import SalaryStructure

def seed_salaries():
    faculty_list = Faculty.objects.all()
    count = 0
    for f in faculty_list:
        if not SalaryStructure.objects.filter(faculty=f).exists():
            base = random.choice([45000, 55000, 65000, 75000, 85000, 120000])
            SalaryStructure.objects.create(
                college=f.college,
                faculty=f,
                base_salary=base,
                hra=base * 0.1,
                allowances_json={
                    'Medical': 2500,
                    'Special': 5000,
                    'Academic': 3000
                },
                deductions_json={
                    'PF': base * 0.12,
                    'Tax': base * 0.05
                }
            )
            count += 1
    print(f"Successfully seeded {count} salary structures.")

if __name__ == "__main__":
    seed_salaries()
