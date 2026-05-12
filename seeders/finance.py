import random
from datetime import timedelta
from django.utils import timezone
from faker import Faker
from core.models import College
from accounts.models import Student, Faculty
from finance.models import FeeStructure, Invoice, Payment, SalaryProfile, SalaryComponent, Payroll, PayrollRunBatch

fake = Faker()

def seed_finance():
    print("Seeding Financial Ecosystem (Fees, Payments & Payroll)...")
    colleges = College.objects.all()
    
    for college in colleges:
        print(f"  Processing {college.name}...")
        
        # 1. Fee Structures
        depts = college.department_set.all()
        for dept in depts:
            programs = dept.program_set.all()
            for prog in programs:
                for sem_num in range(1, 9):
                    FeeStructure.objects.get_or_create(
                        college=college,
                        program=prog,
                        semester_number=sem_num,
                        defaults={
                            'tuition_fee': random.randint(40000, 60000),
                            'exam_fee': 2500,
                            'library_fee': 1500,
                            'other_fees': 5000
                        }
                    )

        # 2. Student Invoices & Payments
        students = Student.objects.filter(college=college)
        print(f"    Generating Invoices for {students.count()} students...")
        
        for student in students:
            fee = FeeStructure.objects.filter(
                program=student.department.program_set.first(), # Simplified
                semester_number=student.current_semester.number
            ).first()
            
            if not fee: continue
            
            total = fee.tuition_fee + fee.exam_fee + fee.library_fee + fee.other_fees
            
            # Use deterministic hash for consistent financial behavior
            s_seed = hash(str(student.id)) % 100
            
            status = 'PAID'
            if s_seed < 10: status = 'OVERDUE'
            elif s_seed < 25: status = 'PARTIAL'
            
            invoice, _ = Invoice.objects.get_or_create(
                college=college,
                student=student,
                semester=student.current_semester,
                defaults={
                    'total_amount': total,
                    'paid_amount': 0,
                    'status': status,
                    'due_date': timezone.now().date() - timedelta(days=random.randint(-10, 20))
                }
            )
            
            if status == 'PAID':
                paid = total
            elif status == 'PARTIAL':
                paid = random.randint(10000, total - 5000)
            else:
                paid = 0
            
            if paid > 0:
                Payment.objects.create(
                    college=college,
                    invoice=invoice,
                    amount_paid=paid,
                    payment_mode=random.choice(['UPI', 'CASH', 'NEFT', 'CARD']),
                    transaction_id=f"TXN{random.randint(100000, 999999)}",
                    status='SUCCESS',
                    payment_date=invoice.created_at + timedelta(days=random.randint(1, 5))
                )
                invoice.paid_amount = paid
                invoice.save()

        # 3. Faculty Payroll
        faculties = Faculty.objects.filter(college=college)
        # Setup Salary Profiles
        components = [
            ('Basic Pay', 'EARNING'), ('HRA', 'EARNING'), ('Special Allowance', 'EARNING'),
            ('Provident Fund', 'DEDUCTION'), ('Professional Tax', 'DEDUCTION'), ('TDS', 'DEDUCTION')
        ]
        comp_objs = {}
        for name, c_type in components:
            obj, _ = SalaryComponent.objects.get_or_create(
                college=college, name=name, defaults={'component_type': c_type, 'is_statutory': True}
            )
            comp_objs[name] = obj

        for faculty in faculties:
            profile, _ = SalaryProfile.objects.get_or_create(
                faculty=faculty,
                defaults={
                    'college': college,
                    'base_salary': random.randint(50000, 150000),
                    'account_number': fake.bban(),
                    'bank_name': 'Hiveflux Institutional Bank'
                }
            )
            # Add components if not present
            if not profile.components.exists():
                profile.components.add(comp_objs['Basic Pay'], through_defaults={'amount': profile.base_salary * 0.5})
                profile.components.add(comp_objs['HRA'], through_defaults={'amount': profile.base_salary * 0.2})
                profile.components.add(comp_objs['Provident Fund'], through_defaults={'amount': 1800})

        # Generate Payroll for last 3 months
        for m_offset in range(3, 0, -1):
            run_date = timezone.now().replace(day=28) - timedelta(days=m_offset*30)
            batch = PayrollRunBatch.objects.create(
                college=college,
                month=run_date.month,
                year=run_date.year,
                status='COMPLETED',
                processed_by=None # System
            )
            for faculty in faculties:
                Payroll.objects.create(
                    college=college,
                    faculty=faculty,
                    batch=batch,
                    month=run_date.month,
                    year=run_date.year,
                    gross_salary=faculty.salaryprofile.base_salary * 0.7,
                    net_salary=faculty.salaryprofile.base_salary * 0.6,
                    status='PAID'
                )

    print("[OK] Financial Ecosystem Seeded.")

if __name__ == "__main__":
    import django
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
    django.setup()
    seed_finance()
