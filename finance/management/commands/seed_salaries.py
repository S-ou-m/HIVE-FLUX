from django.core.management.base import BaseCommand
from accounts.models import Faculty
from finance.models import SalaryStructure
import random

class Command(BaseCommand):
    help = 'Seed salary structures for all faculty'

    def handle(self, *args, **kwargs):
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
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} salary structures."))
