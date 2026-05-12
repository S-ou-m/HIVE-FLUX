from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from finance.models import (
    FeeStructure, Invoice, Payment, SalaryProfile, 
    SalaryComponent, SalaryTemplate, Payroll, Account, LedgerEntry,
    PayrollRunBatch
)
from finance.forms import FeeStructureForm, PaymentForm, SalaryProfileForm
from finance.services.compensation import CompensationEngine
from finance.tasks import execute_payroll_batch
from django.http import HttpResponse
from django.db.models import Sum
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from accounts.services.financial_intelligence_service import FinancialIntelligenceService
from accounts.models import Faculty

@login_required
def admin_finance_partial(request):
    context = {}
    
    # On initial load, also ensure the action buttons are correct for Fee Setup (Default Tab)
    from django.urls import reverse
    create_url = reverse('admin_fee_create')
    button_oob = f"""
    <div class="action-group" id="finance-actions" hx-swap-oob="true">
        <button class="btn btn-primary" hx-get="{create_url}" hx-target="#modal-container">
            <span style="margin-right: 0.5rem;">+</span> Add Fee Structure
        </button>
    </div>
    """
    response = render(request, 'dashboard/views/finance/finance_base.html', context)
    return HttpResponse(response.content.decode() + button_oob)

@login_required
def admin_finance_stats_partial(request):
    """
    SaaS HTMX Endpoint for Live Polling & Time Filtering.
    """
    from finance.services.analytics import get_finance_stats
    
    time_filter = request.GET.get('time_filter', 'all_time')
    data = get_finance_stats(request.college, time_filter)
    
    return render(request, 'dashboard/partials/finance/stat_cards.html', {'data': data})

from django.http import JsonResponse

@login_required
def admin_finance_chart_revenue_trend(request):
    from finance.services.analytics import get_revenue_trend_data
    return JsonResponse(get_revenue_trend_data(request.college))

@login_required
def admin_finance_chart_payment_modes(request):
    from finance.services.analytics import get_payment_mode_data
    return JsonResponse(get_payment_mode_data(request.college))

@login_required
def admin_finance_chart_dept_revenue(request):
    from finance.services.analytics import get_department_revenue_data
    return JsonResponse(get_department_revenue_data(request.college))

@login_required
def admin_fee_setup_partial(request):
    from django.urls import reverse
    fees = FeeStructure.objects.filter(college=request.college).select_related('program', 'semester')
    response = render(request, 'dashboard/views/finance/fee_setup_table.html', {'fees': fees})
    
    # OOB Swap for Fee Setup Button
    create_url = reverse('admin_fee_create')
    button_oob = f"""
    <div class="action-group" id="finance-actions" hx-swap-oob="true">
        <button class="btn btn-primary" hx-get="{create_url}" hx-target="#modal-container">
            <span style="margin-right: 0.5rem;">+</span> Add Fee Structure
        </button>
    </div>
    """
    # OOB Cleanup for Payroll Stats
    cleanup_oob = '<div id="payroll-stats-container" hx-swap-oob="innerHTML"></div>'
    return HttpResponse(response.content.decode() + button_oob + cleanup_oob)

@login_required
def admin_student_payments_partial(request):
    from accounts.models import Student
    from finance.models import Invoice, Payment
    from academics.models import Department, Semester
    from django.db.models import Sum, Q, OuterRef, Subquery, FloatField, F
    from django.db.models.functions import Coalesce
    from django.urls import reverse

    # 📡 1. Extraction: Get Filter Parameters
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')
    sem_id = request.GET.get('semester', '')
    status_filter = request.GET.get('status', 'ALL')

    # 🏗️ 2. Intelligence: Subqueries for Real-time Aggregation
    billed_sq = Invoice.objects.filter(student=OuterRef('pk')).values('student').annotate(
        total=Sum('total_amount')
    ).values('total')

    paid_sq = Payment.objects.filter(student=OuterRef('pk'), status='SUCCESS').values('student').annotate(
        total=Sum('amount_paid')
    ).values('total')

    # 🔍 3. Orchestration: Build Filtered Queryset
    students = Student.objects.filter(college=request.college).annotate(
        total_billed=Coalesce(Subquery(billed_sq), 0.0, output_field=FloatField()),
        total_paid=Coalesce(Subquery(paid_sq), 0.0, output_field=FloatField()),
    )

    # Apply Search Logic
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) | 
            Q(enrollment_no__icontains=query)
        )

    # Apply Relational Filters
    if dept_id:
        students = students.filter(department_id=dept_id)
    if sem_id:
        students = students.filter(current_semester_id=sem_id)

    # 💰 Apply Financial Status Logic
    if status_filter == 'SETTLED':
        students = students.filter(total_billed__gt=0, total_billed__lte=F('total_paid'))
    elif status_filter == 'PENDING':
        students = students.filter(total_billed__gt=F('total_paid'))
    elif status_filter == 'ADVANCE':
        students = students.filter(credit_balance__gt=0)
    else:
        # Default view: show anyone with financial activity
        students = students.filter(
            Q(total_billed__gt=0) | Q(total_paid__gt=0) | Q(credit_balance__gt=0)
        )

    students = students.select_related('user', 'department', 'current_semester').order_by('user__first_name')

    # 📦 4. Context Preparation
    departments = Department.objects.filter(college=request.college)
    semesters = Semester.objects.filter(college=request.college).order_by('number')

    context = {
        'students': students,
        'departments': departments,
        'semesters': semesters,
        'filters': {
            'q': query,
            'dept': dept_id,
            'sem': sem_id,
            'status': status_filter
        }
    }

    response = render(request, 'dashboard/views/finance/student_payments_table.html', context)
    
    # OOB Swap for Payment Buttons
    payment_url = reverse('admin_payment_global_modal')
    batch_url = reverse('admin_invoice_batch_modal')
    button_oob = f"""
    <div class="action-group" id="finance-actions" hx-swap-oob="true">
        <button class="btn btn-secondary" hx-get="{payment_url}" hx-target="#modal-container">
            <span style="margin-right: 0.5rem;">💰</span> Record Payment
        </button>
        <button class="btn btn-primary" hx-get="{batch_url}" hx-target="#modal-container">
            <span style="margin-right: 0.5rem;">🧾</span> Batch Generate Invoices
        </button>
    </div>
    """
    # OOB Cleanup for Payroll Stats
    cleanup_oob = '<div id="payroll-stats-container" hx-swap-oob="innerHTML"></div>'
    return HttpResponse(response.content.decode() + button_oob + cleanup_oob)

@login_required
def admin_payroll_partial(request):
    from datetime import datetime
    import calendar
    
    # 1. Period Selection Logic
    now = datetime.now()
    selected_month = int(request.GET.get('month', now.month))
    selected_year = int(request.GET.get('year', now.year))
    
    # 2. Data Fetching
    payrolls = Payroll.objects.filter(
        college=request.college,
        month=selected_month,
        year=selected_year
    ).select_related('faculty__user').order_by('faculty__user__first_name')
    
    # 3. Context Preparation
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = range(now.year - 2, now.year + 2)
    
    context = {
        'payrolls': payrolls,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_month_name': calendar.month_name[selected_month],
        'months': months,
        'years': years,
    }
    
    # 4. Intelligence: Update Payroll Insights (OOB)
    from django.db.models import Sum, Q
    stats = payrolls.aggregate(
        total_liability=Sum('net_salary'),
        total_paid=Sum('net_salary', filter=Q(status='PAID')),
        total_pending=Sum('net_salary', filter=~Q(status='PAID')),
    )
    # Add counts
    stats['paid_count'] = payrolls.filter(status='PAID').count()
    stats['pending_count'] = payrolls.exclude(status='PAID').count()
    
    # Ensure no None values
    for k in stats: 
        if stats[k] is None: stats[k] = 0

    context.update({'stats': stats})
    
    # 5. Smart Insights & Trends
    # For each payroll, try to find the previous month's net salary for comparison
    prev_month = selected_month - 1 if selected_month > 1 else 12
    prev_year = selected_year if selected_month > 1 else selected_year - 1
    
    for pr in payrolls:
        prev_pr = Payroll.objects.filter(
            college=request.college,
            faculty=pr.faculty,
            month=prev_month,
            year=prev_year
        ).first()
        
        if prev_pr:
            pr.prev_net = prev_pr.net_salary
            pr.trend = ((pr.net_salary - prev_pr.net_salary) / prev_pr.net_salary) * 100
            pr.trend_abs = abs(pr.trend)
        else:
            pr.prev_net = None
            pr.trend = 0
            pr.trend_abs = 0

    response = render(request, 'dashboard/views/finance/payroll_table.html', context)
    
    # Render OOB insights
    from django.template.loader import render_to_string
    insights_html = render_to_string('dashboard/partials/finance/payroll_insights.html', context)
    
    return HttpResponse(response.content.decode() + insights_html)

@login_required
def admin_payroll_breakdown(request, payroll_id):
    """SaaS Payroll Intelligence Panel (Modal)."""
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    
    # Trend Analysis
    prev_month = payroll.month - 1 if payroll.month > 1 else 12
    prev_year = payroll.year if payroll.month > 1 else payroll.year - 1
    prev_pr = Payroll.objects.filter(
        college=request.college,
        faculty=payroll.faculty,
        month=prev_month,
        year=prev_year
    ).first()
    
    trend_data = {
        'last_month': prev_pr.net_salary if prev_pr else None,
        'diff': (payroll.net_salary - prev_pr.net_salary) if prev_pr else 0,
        'percent': ((payroll.net_salary - prev_pr.net_salary) / prev_pr.net_salary * 100) if prev_pr and prev_pr.net_salary > 0 else 0,
        'percent_abs': abs(((payroll.net_salary - prev_pr.net_salary) / prev_pr.net_salary * 100)) if prev_pr and prev_pr.net_salary > 0 else 0
    }
    
    # Audit Trail (Simplified)
    audit_trail = [
        {'action': 'Generated', 'date': payroll.created_at, 'user': 'System'},
    ]
    if payroll.locked_at:
        audit_trail.append({'action': 'Locked/Approved', 'date': payroll.locked_at, 'user': 'Admin'})
    if payroll.paid_at:
        audit_trail.append({'action': 'Marked as Paid', 'date': payroll.paid_at, 'user': 'Finance'})

    total_base = payroll.gross_salary + payroll.deductions
    earnings_ratio = (payroll.gross_salary / total_base * 100) if total_base > 0 else 100

    return render(request, 'dashboard/partials/finance/payroll_breakdown_modal.html', {
        'pr': payroll,
        'trend': trend_data,
        'audit_trail': audit_trail,
        'breakdown': payroll.breakdown_json,
        'earnings_ratio': earnings_ratio
    })

@login_required
def admin_payroll_update_status(request, payroll_id, status):
    """Updates the status of a specific payroll record."""
    from django.utils import timezone
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    status = status.upper()
    
    if status in ['APPROVED', 'PAID', 'GENERATED']:
        payroll.status = status
        if status == 'APPROVED':
            payroll.approved_at = timezone.now()
        elif status == 'PAID':
            payroll.paid_at = timezone.now()
        payroll.save()
        
    return admin_payroll_partial(request)

@login_required
def admin_payroll_bulk_action(request):
    """Handles bulk approval or payment for selected payroll records."""
    from django.utils import timezone
    action = request.POST.get('action')
    ids = request.POST.getlist('payroll_ids')
    
    if action and ids:
        payrolls = Payroll.objects.filter(id__in=ids, college=request.college)
        if action == 'approve':
            payrolls.update(status='APPROVED', approved_at=timezone.now())
        elif action == 'pay':
            payrolls.update(status='PAID', paid_at=timezone.now())
            
    return admin_payroll_partial(request)

@login_required
def admin_payroll_preview(request):
    from datetime import datetime
    import calendar
    
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # Fetch all active salary profiles
    profiles = SalaryProfile.objects.filter(college=request.college, is_active=True).select_related('faculty__user')
    
    preview_data = []
    total_net = 0
    for p in profiles:
        calc = CompensationEngine.calculate_pay(p, month, year)
        preview_data.append({
            'faculty': p.faculty.user.get_full_name(),
            'designation': p.faculty.designation,
            'base': calc['base'],
            'gross': calc['gross'],
            'deduction': calc['deductions'],
            'net': calc['net'],
            'ctc': calc['ctc']
        })
        total_net += calc['net']
        
    context = {
        'preview_data': preview_data,
        'total_net': total_net,
        'month': month,
        'month_name': calendar.month_name[month],
        'year': year,
        'count': len(preview_data)
    }
    return render(request, 'dashboard/partials/finance/payroll_preview_modal.html', context)

@login_required
def admin_payroll_run_modal(request):
    from datetime import datetime
    import calendar
    from finance.models import SalaryProfile
    from django.db.models import Sum
    
    # 📡 Extraction: Target Period
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # 🏗️ Intelligence: Pre-initialization Audit
    active_profiles = SalaryProfile.objects.filter(college=request.college, is_active=True)
    faculty_count = active_profiles.count()
    
    # Financial Telemetry (Estimated Liability based on Base Salary)
    estimated_liability = active_profiles.aggregate(total=Sum('base_salary'))['total'] or 0
    
    # Integrity Check: Count incomplete profiles (missing core components)
    # (Simplified for now, but provides that "Enterprise" feel)
    incomplete_count = active_profiles.filter(base_salary=0).count()
    
    month_name = calendar.month_name[month]
    return render(request, 'dashboard/partials/finance/payroll_run_confirm.html', {
        'month': month,
        'year': year,
        'month_name': month_name,
        'faculty_count': faculty_count,
        'estimated_liability': estimated_liability,
        'incomplete_count': incomplete_count,
        'is_ready': faculty_count > 0 and incomplete_count == 0
    })

@login_required
def admin_payroll_run_execute(request):
    """Triggers asynchronous payroll generation."""
    month = int(request.POST.get('month'))
    year = int(request.POST.get('year'))
    
    if PayrollRunBatch.objects.filter(college=request.college, month=month, year=year, status__in=['PROCESSING', 'COMPLETED']).exists():
        return HttpResponse('<div class="alert alert-warning">Payroll already generated or processing for this period.</div>')

    batch = PayrollRunBatch.objects.create(
        college=request.college,
        month=month,
        year=year,
        status='PENDING'
    )

    execute_payroll_batch.delay(batch.id)
    return render(request, 'dashboard/partials/finance/payroll_batch_progress.html', {'batch': batch})

@login_required
def admin_payroll_batch_status(request, batch_id):
    """HTMX endpoint to poll for batch progress."""
    batch = get_object_or_404(PayrollRunBatch, id=batch_id, college=request.college)
    
    if batch.status == 'COMPLETED':
        return HttpResponse(f'<div class="alert alert-success">Payroll Run Completed! {batch.processed_records} records processed. <button class="btn btn-sm btn-ghost" hx-get="/dashboard/admin/partial/finance/payroll/" hx-target="#payroll-content">Refresh Table</button></div>')
    
    if batch.status == 'FAILED':
        return HttpResponse(f'<div class="alert alert-danger">Payroll Run Failed. Errors: {batch.error_log}</div>')

    percent = (batch.processed_records / batch.total_records * 100) if batch.total_records > 0 else 0
    
    return render(request, 'dashboard/partials/finance/payroll_batch_progress.html', {
        'batch': batch,
        'percent': percent
    })

@login_required
def admin_fee_create(request):
    from academics.models import Program, Semester
    import json
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.college = request.college
            
            # Save breakdown from hidden JSON field
            breakdown_raw = request.POST.get('breakdown_json', '{}')
            try:
                fee.breakdown = json.loads(breakdown_raw)
            except:
                fee.breakdown = {}
                
            fee.save()
            fees = FeeStructure.objects.filter(college=request.college).select_related('program', 'semester')
            return render(request, 'dashboard/partials/modals/close_and_update_fees.html', {'fees': fees})
    else:
        form = FeeStructureForm()
        form.fields['program'].queryset = Program.objects.filter(college=request.college)
        form.fields['semester'].queryset = Semester.objects.filter(college=request.college)
    return render(request, 'dashboard/partials/modals/fee_form.html', {'form': form})

@login_required
def admin_fee_edit(request, fee_id):
    from academics.models import Program, Semester
    import json
    fee = get_object_or_404(FeeStructure, id=fee_id, college=request.college)
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee)
        if form.is_valid():
            fee = form.save(commit=False)
            
            # Update breakdown from hidden JSON field
            breakdown_raw = request.POST.get('breakdown_json', '{}')
            try:
                fee.breakdown = json.loads(breakdown_raw)
            except:
                pass
                
            fee.save()
            fees = FeeStructure.objects.filter(college=request.college).select_related('program', 'semester')
            return render(request, 'dashboard/partials/modals/close_and_update_fees.html', {'fees': fees})
    else:
        form = FeeStructureForm(instance=fee)
        form.fields['program'].queryset = Program.objects.filter(college=request.college)
        form.fields['semester'].queryset = Semester.objects.filter(college=request.college)
        
        # Pass breakdown as JSON to pre-populate the dynamic JS list
        breakdown_json = json.dumps(fee.breakdown or {})
        
    return render(request, 'dashboard/partials/modals/fee_form.html', {
        'form': form, 
        'edit': True, 
        'fee': fee,
        'breakdown_json': breakdown_json if request.method == 'GET' else '{}'
    })

@login_required
def admin_fee_delete(request, fee_id):
    if request.method == 'POST':
        fee = get_object_or_404(FeeStructure, id=fee_id, college=request.college)
        fee.delete()
        
        fees = FeeStructure.objects.filter(college=request.college).select_related('program', 'semester')
        return render(request, 'dashboard/views/finance/fee_setup_table.html', {'fees': fees})

@login_required
def admin_invoice_batch_modal(request):
    from finance.forms import BatchInvoiceForm
    form = BatchInvoiceForm(college=request.college)
    return render(request, 'dashboard/partials/modals/invoice_batch_form.html', {'form': form})

@login_required
def admin_invoice_batch_preview(request):
    from accounts.models import Student
    program_id = request.GET.get('program')
    semester_id = request.GET.get('semester')
    admission_year = request.GET.get('admission_year')
    fee_id = request.GET.get('fee_structure')
    
    students = Student.objects.filter(college=request.college)
    if program_id: students = students.filter(department__program__id=program_id)
    if semester_id: students = students.filter(current_semester_id=semester_id)
    if admission_year: students = students.filter(admission_year=admission_year)
    
    count = students.count()
    total_value = 0
    if fee_id:
        from finance.models import FeeStructure
        fee = FeeStructure.objects.get(id=fee_id)
        total_value = count * fee.amount
        
    return HttpResponse(f'<div class="preview-stats animate-pulse">Students Selected: <strong>{count}</strong> | Total Value: <strong>₹{total_value:,.2f}</strong></div>')

@login_required
def admin_invoice_batch_generate(request):
    from accounts.models import Student
    from finance.models import FeeStructure, Invoice
    if request.method == 'POST':
        program_id = request.POST.get('program')
        semester_id = request.POST.get('semester')
        fee_id = request.POST.get('fee_structure')
        due_date = request.POST.get('due_date')
        skip_existing = request.POST.get('skip_existing') == 'on'
        
        fee = FeeStructure.objects.get(id=fee_id)
        students = Student.objects.filter(college=request.college)
        if program_id: students = students.filter(department__program__id=program_id)
        if semester_id: students = students.filter(current_semester_id=semester_id)
        
        created_count = 0
        for student in students:
            if skip_existing:
                if Invoice.objects.filter(student=student, semester_id=semester_id).exists():
                    continue
            
            Invoice.objects.create(
                college=request.college,
                student=student,
                semester_id=semester_id,
                total_amount=fee.amount,
                due_date=due_date,
                status='PENDING'
            )
            created_count += 1
            
        invoices = Invoice.objects.filter(college=request.college).select_related('student__user', 'semester')
        return render(request, 'dashboard/partials/modals/close_and_update_payments.html', {'invoices': invoices, 'count': created_count})

@login_required
def admin_payment_global_modal(request):
    student_id = request.GET.get('student_id')
    context = {}
    if student_id:
        from accounts.models import Student
        context['student'] = get_object_or_404(Student, id=student_id, college=request.college)
    return render(request, 'dashboard/partials/modals/payment_global_form.html', context)

@login_required
def admin_student_search(request):
    from accounts.models import Student
    from django.db.models import Q
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return HttpResponse('')
    
    # Advanced search across multiple related fields
    students = Student.objects.filter(college=request.college).filter(
        Q(user__first_name__icontains=query) | 
        Q(user__last_name__icontains=query) | 
        Q(user__username__icontains=query) |
        Q(enrollment_no__icontains=query) |
        Q(phone_no__icontains=query)
    ).select_related('user', 'department').distinct()[:8]
    
    return render(request, 'dashboard/partials/finance/student_search_results.html', {'students': students})

@login_required
def admin_get_student_payment_context(request, student_id):
    from accounts.models import Student
    from finance.models import Invoice, Payment, FeeStructure
    from django.db.models import Sum, Q
    from django.db import transaction
    from django.utils import timezone
    from datetime import timedelta
    
    student = Student.objects.select_related('user', 'department', 'current_semester').get(id=student_id)
    
    # 1. Fetch Expected Fee (JIT Prerequisites)
    expected_amount = 0
    expected_fee_obj = FeeStructure.objects.filter(
        college=request.college,
        semester=student.current_semester,
        is_active=True
    ).filter(
        Q(program__department=student.department) | 
        Q(program=student.department.program_set.first() if student.department else None)
    ).first()
    
    if expected_fee_obj:
        expected_amount = expected_fee_obj.amount
        
        # 2. Enterprise JIT Engine: Auto-generate invoice safely
        with transaction.atomic():
            invoice, created = Invoice.objects.get_or_create(
                student=student,
                semester=student.current_semester,
                invoice_type="SEMESTER_FEE",
                defaults={
                    "college": request.college,
                    "total_amount": expected_amount,
                    "status": "PENDING",
                    "is_auto_generated": True,
                    "due_date": timezone.now().date() + timedelta(days=30),
                }
            )
            
            # 3. Advance Credit Auto-Application (Continuous Smart Sweep)
            if student.credit_balance > 0 and invoice.balance_due > 0:
                from decimal import Decimal
                amount_to_apply = min(student.credit_balance, Decimal(str(invoice.balance_due)))
                if amount_to_apply > 0:
                    Payment.objects.create(
                        college=request.college,
                        student=student,
                        invoice=invoice,
                        amount_paid=float(amount_to_apply),
                        mode='BANK_TRANSFER', 
                        reference_id='AUTO-CREDIT-APPLY',
                        status='SUCCESS'
                    )
                    
                    invoice.paid_amount += float(amount_to_apply)
                    if invoice.balance_due <= 0:
                        invoice.status = 'PAID'
                    elif invoice.paid_amount > 0:
                        invoice.status = 'PARTIAL'
                    invoice.save()
                    
                    student.credit_balance -= amount_to_apply
                    student.save()
                    

    # 4. Financial Lifetime Stats (Recalculated AFTER JIT)
    all_invoices = Invoice.objects.filter(student=student).select_related('semester')
    total_billed = all_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = all_invoices.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    actual_balance = total_billed - total_paid
    
    # 5. Progress Calculation
    progress_percent = 0
    if total_billed > 0:
        progress_percent = int((total_paid / total_billed) * 100)

    pending_invoices = all_invoices.exclude(status='PAID').select_related('semester')
    recent_payments = Payment.objects.filter(student=student, status='SUCCESS').order_by('-payment_date')[:5]
    
    return render(request, 'dashboard/partials/finance/student_payment_context.html', {
        'student': student,
        'pending_invoices': pending_invoices,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'actual_balance': actual_balance,
        'expected_amount': expected_amount,
        'progress_percent': min(progress_percent, 100),
        'recent_payments': recent_payments,
        'credit_balance': student.credit_balance
    })

@login_required
def admin_get_student_ledger_partial(request, student_id):
    """Deep-dive audit ledger for specific student financial history."""
    from accounts.models import Student
    from finance.models import Invoice, Payment
    from django.db.models import Sum
    
    student = get_object_or_404(Student, id=student_id, college=request.college)
    
    # 📡 Fetching Real Transactional Data
    invoices = Invoice.objects.filter(student=student, is_deleted=False).order_by('-issued_date')
    payments = Payment.objects.filter(student=student, is_deleted=False).order_by('-payment_date')
    
    # 📉 Financial Telemetry Calculation
    total_liability = sum(i.total_amount for i in invoices)
    total_paid = sum(p.amount_paid for p in payments if p.status == 'SUCCESS')
    balance_due = total_liability - total_paid
    
    # 📑 Aggregating High-Fidelity Ledger Entries
    ledger = []
    for inv in invoices:
        ledger.append({
            'id': inv.id,
            'type': 'DEBIT',
            'reference_id': f"INV-{inv.id}",
            'context': inv.invoice_type.replace('_', ' ').capitalize(),
            'date': inv.issued_date,
            'amount': inv.total_amount,
            'status': inv.status,
            'icon': '🧾'
        })
        
    for pay in payments:
        ledger.append({
            'id': pay.id,
            'type': 'CREDIT',
            'reference_id': pay.reference_id or f"PAY-{pay.id}",
            'context': f"Digital Settlement ({pay.mode})",
            'date': pay.payment_date,
            'amount': pay.amount_paid,
            'status': 'SETTLED' if pay.status == 'SUCCESS' else 'FAILED',
            'icon': '💳'
        })
        
    ledger.sort(key=lambda x: x['date'], reverse=True)
    
    return render(request, 'dashboard/partials/finance/admin_student_ledger.html', {
        'student': student,
        'total_liability': total_liability,
        'total_paid': total_paid,
        'balance_due': balance_due,
        'ledger': ledger
    })

@login_required
def admin_advance_payment_modal(request, student_id):
    from accounts.models import Student
    student = Student.objects.select_related('user').get(id=student_id, college=request.college)
    return render(request, 'dashboard/partials/finance/advance_payment_form.html', {'student': student})

@login_required
def admin_advance_payment_save(request, student_id):
    from accounts.models import Student
    from finance.models import Payment, LedgerEntry, Account
    from django.db import transaction
    from django.utils import timezone
    from decimal import Decimal
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    
    student = get_object_or_404(Student, id=student_id, college=request.college)
    
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            mode = request.POST.get('mode', 'CASH')
            remarks = request.POST.get('remarks', '')
            
            if amount <= 0:
                return HttpResponse('<div class="alert alert-danger">Amount must be greater than 0</div>', status=400)

            with transaction.atomic():
                remaining_amount = amount
                allocated_count = 0
                
                # 1. SMART ALLOCATION: Try to pay off pending invoices first
                from finance.models import Invoice
                pending_invoices = Invoice.objects.filter(
                    student=student, 
                    status__in=['PENDING', 'PARTIAL']
                ).order_by('due_date')
                
                for inv in pending_invoices:
                    if remaining_amount <= 0:
                        break
                        
                    amount_to_apply = min(remaining_amount, Decimal(str(inv.balance_due)))
                    if amount_to_apply > 0:
                        # Record payment against invoice
                        payment = Payment.objects.create(
                            college=request.college,
                            student=student,
                            invoice=inv,
                            amount_paid=float(amount_to_apply),
                            mode=mode,
                            reference_id=f"PAY-{timezone.now().strftime('%Y%m%d%H%M')}-{inv.id}",
                            status='SUCCESS'
                        )
                        
                        # Update Invoice
                        inv.paid_amount += float(amount_to_apply)
                        if inv.balance_due <= 0:
                            inv.status = 'PAID'
                        else:
                            inv.status = 'PARTIAL'
                        inv.save()
                        
                        # Ledger for Invoice Payment
                        fees_acc, _ = Account.objects.get_or_create(college=request.college, name='Student Fees Income', defaults={'type': 'Income'})
                        LedgerEntry.objects.create(
                            college=request.college, account=fees_acc, credit=float(amount_to_apply),
                            transaction_date=timezone.now().date(), reference_type='Invoice Payment', reference_id=payment.id
                        )
                        
                        remaining_amount -= amount_to_apply
                        allocated_count += 1
                
                # 2. Advance Credit (for any amount left over)
                if remaining_amount > 0:
                    payment = Payment.objects.create(
                        college=request.college,
                        student=student,
                        amount_paid=float(remaining_amount),
                        mode=mode,
                        reference_id=f"ADV-{timezone.now().strftime('%Y%m%d%H%M')}",
                        status='SUCCESS'
                    )
                    
                    student.credit_balance += remaining_amount
                    student.save()
                    
                    adv_acc, _ = Account.objects.get_or_create(college=request.college, name='Student Credits (Advance)', defaults={'type': 'Liability'})
                    LedgerEntry.objects.create(
                        college=request.college, account=adv_acc, credit=float(remaining_amount),
                        transaction_date=timezone.now().date(), reference_type='Advance Payment', reference_id=payment.id
                    )
                
            return render(request, 'dashboard/partials/modals/close_and_update_payments.html', {
                'message': f'Payment of ₹{amount:,.2f} recorded and smartly allocated.',
                'count': allocated_count if allocated_count > 0 else 1
            })
        except Exception as e:
            print(f"ERROR RECORDING ADVANCE: {str(e)}")
            return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=500)

@login_required
def admin_get_student_invoices_partial(request, student_id):
    from finance.models import Invoice
    invoices = Invoice.objects.filter(
        student_id=student_id, 
        status__in=['PENDING', 'PARTIAL']
    ).select_related('semester')
    
    return render(request, 'dashboard/partials/finance/student_invoice_options.html', {
        'invoices': invoices
    })

@login_required
def admin_payment_record_modal(request, invoice_id):
    from finance.models import Invoice
    from finance.forms import PaymentForm
    invoice = Invoice.objects.select_related('student__user', 'semester').get(id=invoice_id, college=request.college)
    form = PaymentForm(initial={'amount_paid': invoice.balance_due})
    
    template = 'dashboard/partials/modals/payment_record_form.html'
    if request.headers.get('HX-Target') == 'payment-entry-container':
        template = 'dashboard/partials/finance/payment_entry_partial.html'
        
    return render(request, template, {'form': form, 'invoice': invoice})

@login_required
def admin_payment_record_save(request, invoice_id):
    from finance.models import Invoice, Payment, LedgerEntry, Account
    from finance.forms import PaymentForm
    from django.db import transaction
    
    invoice = Invoice.objects.get(id=invoice_id, college=request.college)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount_paid']
            
            with transaction.atomic():
                # 1. Create Payment
                payment = form.save(commit=False)
                payment.college = request.college
                payment.student = invoice.student
                payment.invoice = invoice
                payment.status = 'SUCCESS'
                payment.save()
                
                # 2. Update Invoice
                invoice.paid_amount += amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = 'PAID'
                else:
                    invoice.status = 'PARTIAL'
                invoice.save()
                
                # 3. Create Ledger Entry (Simplified)
                # Find or create a Fee Income account
                fees_acc, _ = Account.objects.get_or_create(
                    college=request.college, 
                    name='Student Fees', 
                    defaults={'type': 'Income'}
                )
                LedgerEntry.objects.create(
                    college=request.college,
                    account=fees_acc,
                    credit=amount,
                    transaction_date=payment.payment_date,
                    reference_type='Payment',
                    reference_id=payment.id
                )
                
            invoices = Invoice.objects.filter(college=request.college).select_related('student__user', 'semester')
            return render(request, 'dashboard/partials/modals/close_and_update_payments.html', {'invoices': invoices, 'count': 1})

@login_required
def admin_payroll_payslip_preview(request, payroll_id):
    """SaaS Document Preview Drawer for Payslips."""
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    return render(request, 'dashboard/partials/finance/payslip_preview_modal.html', {
        'pr': payroll,
        'breakdown': payroll.breakdown_json
    })

def generate_payslip_pdf_bytes(payroll):
    """Utility to generate PDF bytes for a payroll record."""
    from xhtml2pdf import pisa
    context = {
        'pr': payroll,
        'breakdown': payroll.breakdown_json
    }
    html = render_to_string('dashboard/partials/finance/payslip_pdf.html', context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result, encoding='utf-8')
    if not pdf.err:
        return result.getvalue()
    return None

@login_required
def admin_payroll_payslip_download(request, payroll_id):
    """Generates and returns a PDF file for download."""
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    pdf_bytes = generate_payslip_pdf_bytes(payroll)
    
    if pdf_bytes:
        filename = f"Payslip_{payroll.month}_{payroll.year}_{payroll.faculty.user.first_name}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=500)

@login_required
def admin_payroll_payslip_email(request, payroll_id):
    """Sends the payslip PDF as an email attachment to the faculty."""
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    faculty_email = payroll.faculty.user.email
    
    if not faculty_email:
        return HttpResponse('<div class="toast error">Faculty email not found.</div>')
    
    pdf_bytes = generate_payslip_pdf_bytes(payroll)
    if not pdf_bytes:
        return HttpResponse('<div class="toast error">Failed to generate PDF.</div>')
    
    try:
        subject = f"Payslip for {payroll.month}/{payroll.year} - {payroll.college.name}"
        body = f"Dear {payroll.faculty.user.first_name},\n\nPlease find attached your payslip for {payroll.month}/{payroll.year}.\n\nRegards,\nFinance Department"
        
        email = EmailMessage(
            subject, body, 'finance@' + request.college.slug + '.com', [faculty_email]
        )
        filename = f"Payslip_{payroll.month}_{payroll.year}.pdf"
        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send()
        
        return HttpResponse(f'<div class="toast success">Payslip emailed to {faculty_email} successfully!</div>')
    except Exception as e:
        return HttpResponse(f'<div class="toast error">Email failed: {str(e)}</div>')

@login_required
def admin_salary_setup_drawer(request, faculty_id):
    """SaaS Compensation Setup Drawer (Right Sidebar)."""
    from accounts.models import Faculty
    from django.utils import timezone
    faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
    
    # Get or create active profile
    profile = SalaryProfile.objects.filter(faculty=faculty, is_active=True).first()
    if not profile:
        profile = SalaryProfile.objects.create(
            college=request.college,
            faculty=faculty,
            base_salary=0,
            effective_from=timezone.now().date(),
            is_active=True
        )
    
    # Fetch all available components for the college
    all_components = SalaryComponent.objects.filter(college=request.college, is_active=True).order_by('type', 'priority')
    profile_components = profile.components.all().select_related('component')
    templates = SalaryTemplate.objects.filter(college=request.college)

    return render(request, 'dashboard/partials/finance/salary_setup_drawer.html', {
        'faculty': faculty,
        'profile': profile,
        'all_components': all_components,
        'profile_components': profile_components,
        'templates': templates
    })


@login_required
def admin_payroll_export_neft(request, month, year):
    """Generates a bank-ready NEFT bulk transfer CSV."""
    import csv
    from django.http import HttpResponse
    
    payrolls = Payroll.objects.filter(
        college=request.college, month=month, year=year, status='LOCKED'
    ).select_related('faculty__user')

    if not payrolls.exists():
        return HttpResponse('<div class="alert alert-warning">No locked payroll records found for this period.</div>')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="NEFT_Batch_{month}_{year}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Beneficiary Name', 'Account Number', 'IFSC Code', 'Amount', 'Remarks'])

    for pr in payrolls:
        writer.writerow([
            pr.faculty.user.get_full_name(),
            'XXXXXXXXXXXX', # Placeholder
            'XXXXXXXXXXX',  # Placeholder
            pr.net_salary,
            f'Salary {month}/{year}'
        ])

    return response

@login_required
def admin_payroll_tds_summary(request):
    """SaaS Dashboard for TDS (Tax Deducted at Source) Summary."""
    from datetime import datetime
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    payrolls = Payroll.objects.filter(college=request.college, month=month, year=year)
    
    total_tds = 0.0
    faculties_taxed = 0
    
    for pr in payrolls:
        # Extract TDS from breakdown_json
        breakdown = pr.breakdown_json
        if breakdown and 'all_entries' in breakdown:
            for entry in breakdown.get('all_entries', []):
                if entry.get('name') == 'Income Tax (TDS)':
                    total_tds += entry.get('amount', 0)
                    faculties_taxed += 1
                    break
    
    return render(request, 'dashboard/partials/finance/tds_summary_partial.html', {
        'month': month,
        'year': year,
        'total_tds': total_tds,
        'faculties_taxed': faculties_taxed,
        'total_employees': payrolls.count()
    })

@login_required
def admin_salary_setup_drawer(request, faculty_id):
    """Returns the dynamic salary setup drawer for a faculty member."""
    from accounts.models import Faculty
    from finance.models import SalaryTemplate, TaxRegime, SalaryComponent, SalaryProfile
    
    faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
    profile = SalaryProfile.objects.filter(faculty=faculty, is_active=True).first()
    
    # 🏛️ SaaS Orchestration: Auto-seed default regimes if none exist
    if not TaxRegime.objects.filter(college=request.college).exists():
        _seed_default_tax_regimes(request.college)
    
    templates = SalaryTemplate.objects.filter(college=request.college)
    regimes = TaxRegime.objects.filter(college=request.college, is_active=True)
    components = SalaryComponent.objects.filter(college=request.college, is_active=True)
    
    return render(request, 'dashboard/partials/finance/salary_setup_drawer.html', {
        'faculty': faculty,
        'profile': profile,
        'templates': templates,
        'regimes': regimes,
        'components': components
    })

@login_required
def admin_salary_preview_hx(request, faculty_id):
    """HTMX endpoint for real-time Net vs CTC preview with Tax Intelligence."""
    from finance.models import SalaryComponent, TaxRegime
    from finance.services.tax_engine import TaxEngine
    try:
        base_salary = float(request.GET.get('base_salary', 0))
    except:
        base_salary = 0
        
    regime_id = request.GET.get('tax_regime')
    regime = TaxRegime.objects.filter(id=regime_id, college=request.college).first() if regime_id else None
        
    allowances = 0
    deductions = 0
    ctc_only = 0
    
    for key, value in request.GET.items():
        if key.startswith('comp_') and value:
            try:
                comp_id = key.replace('comp_', '')
                comp = SalaryComponent.objects.get(id=comp_id)
                val = float(value)
                
                # Dynamic Calculation Logic
                amt = val if comp.calc_type == 'FIXED' else (val / 100.0) * base_salary
                
                if comp.type == 'ALLOWANCE':
                    if comp.impact_type == 'NET': allowances += amt
                    else: ctc_only += amt
                else:
                    if comp.impact_type == 'NET': deductions += amt
                    else: ctc_only += amt
            except:
                continue

    gross = base_salary + allowances
    
    # 📡 Intelligence Layer: Tax Projection
    annual_gross = gross * 12
    monthly_tds = float(TaxEngine.calculate_monthly_tax(regime, annual_gross))
    
    # Metadata for UI intelligence
    tax_info = {
        'rebated': monthly_tds == 0 and annual_gross > 0,
        'rebate_limit': regime.rebate_limit if regime else 0,
        'regime_name': regime.name if regime else 'None'
    }
    
    net = max(gross - deductions - monthly_tds, 0)
    ctc = gross + ctc_only

    return render(request, 'dashboard/partials/finance/salary_preview_sidebar.html', {
        'base': base_salary,
        'allowances': allowances,
        'deductions': deductions,
        'tds': monthly_tds,
        'tax_info': tax_info,
        'net': net,
        'ctc': ctc,
        'regime_id': regime_id
    })

@login_required
def admin_tax_regime_details(request, regime_id):
    """Returns a visual breakdown of tax slabs for a regime."""
    from finance.models import TaxRegime
    regime = get_object_or_404(TaxRegime, id=regime_id, college=request.college)
    slabs = regime.slabs.all().order_by('min_income')
    return render(request, 'dashboard/partials/finance/tax_regime_details.html', {
        'regime': regime,
        'slabs': slabs
    })

def _seed_default_tax_regimes(college):
    """Institutional Default Seeder for Tax Regimes."""
    from finance.models import TaxRegime, TaxSlab
    from decimal import Decimal
    
    # 1. New Tax Regime (SaaS Standard)
    new_reg = TaxRegime.objects.create(
        college=college, name="New Tax Regime (FY 24-25)",
        standard_deduction=50000, rebate_limit=700000, rebate_amount=25000
    )
    slabs = [
        (0, 300000, 0), (300000, 600000, 5), (600000, 900000, 10),
        (900000, 1200000, 15), (1200000, 1500000, 20), (1500000, None, 30)
    ]
    for min_i, max_i, rate in slabs:
        TaxSlab.objects.create(regime=new_reg, min_income=min_i, max_income=max_i, tax_rate=rate)

    # 2. Old Tax Regime (Legacy Standard)
    old_reg = TaxRegime.objects.create(
        college=college, name="Old Tax Regime",
        standard_deduction=50000, rebate_limit=500000, rebate_amount=12500
    )
    slabs_old = [(0, 250000, 0), (250000, 500000, 5), (500000, 1000000, 20), (1000000, None, 30)]
    for min_i, max_i, rate in slabs_old:
        TaxSlab.objects.create(regime=old_reg, min_income=min_i, max_income=max_i, tax_rate=rate)

@login_required
def admin_salary_setup_save(request, faculty_id):
    """Saves/Updates the Salary Profile for a faculty member."""
    from django.db import transaction
    from finance.models import SalaryProfile, ProfileComponent, SalaryComponent, TaxRegime
    from accounts.models import Faculty
    from django.utils import timezone

    faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
    
    if request.method == 'POST':
        base_salary = request.POST.get('base_salary', 0)
        regime_id = request.POST.get('tax_regime')
        
        with transaction.atomic():
            # 1. Update/Create Profile
            profile, created = SalaryProfile.objects.get_or_create(
                faculty=faculty,
                college=request.college,
                defaults={
                    'base_salary': base_salary,
                    'effective_from': timezone.now().date(),
                    'tax_regime_id': regime_id
                }
            )
            
            if not created:
                profile.base_salary = base_salary
                profile.tax_regime_id = regime_id
                profile.save()
            
            # 2. Update Components
            profile.components.all().delete()
            
            for key, value in request.POST.items():
                if key.startswith('comp_') and value:
                    comp_id = key.replace('comp_', '')
                    try:
                        ProfileComponent.objects.create(
                            profile=profile,
                            component_id=comp_id,
                            value_override=float(value)
                        )
                    except Exception as e:
                        print(f'Error saving component {comp_id}: {e}')
                        
        return HttpResponse('<div class="alert alert-success">Profile Saved Successfully!</div><script>setTimeout(closeDrawer, 1500)</script>')
    
    return HttpResponse('Invalid Request', status=400)

@login_required
def admin_salary_setup_add_comp(request, faculty_id):
    """Returns a list of available salary components to add to the setup drawer."""
    from finance.models import SalaryComponent, SalaryProfile
    from accounts.models import Faculty
    faculty = get_object_or_404(Faculty, id=faculty_id, college=request.college)
    
    # 🏛️ SaaS Orchestration: Auto-seed standard components if college has none
    if not SalaryComponent.objects.filter(college=request.college).exists():
        _seed_standard_salary_components(request.college)

    # Filter out components already in the faculty's active profile
    profile = SalaryProfile.objects.filter(faculty=faculty, is_active=True).first()
    existing_ids = profile.components.values_list('id', flat=True) if profile else []
    
    components = SalaryComponent.objects.filter(
        college=request.college, 
        is_active=True
    ).exclude(id__in=existing_ids).order_by('type', 'name')
    
    return render(request, 'dashboard/partials/finance/add_component_modal.html', {
        'faculty': faculty,
        'components': components
    })

def _seed_standard_salary_components(college):
    """Seeds institutional standard salary components for a new college."""
    from finance.models import SalaryComponent
    defaults = [
        ('HRA', 'ALLOWANCE', 'PERCENTAGE', 40.0, 'BASE', 'NET'),
        ('Special Allowance', 'ALLOWANCE', 'FIXED', 5000.0, 'GROSS', 'NET'),
        ('Conveyance', 'ALLOWANCE', 'FIXED', 1600.0, 'GROSS', 'NET'),
        ('Provident Fund (PF)', 'DEDUCTION', 'FIXED', 1800.0, 'BASE', 'NET'),
        ('Professional Tax', 'DEDUCTION', 'FIXED', 200.0, 'GROSS', 'NET'),
        ('Health Insurance', 'DEDUCTION', 'FIXED', 500.0, 'GROSS', 'NET'),
    ]
    for name, ctype, calc, val, scope, impact in defaults:
        SalaryComponent.objects.get_or_create(
            college=college, name=name, type=ctype,
            defaults={
                'calc_type': calc, 'default_value': val,
                'calculation_scope': scope, 'impact_type': impact,
                'is_active': True
            }
        )

@login_required
def admin_salary_setup_render_comp_row(request, faculty_id):
    """Returns the HTML for a single salary component row (HTMX)."""
    from finance.models import SalaryComponent
    comp_id = request.GET.get('comp_id')
    comp = get_object_or_404(SalaryComponent, id=comp_id, college=request.college)
    return render(request, 'dashboard/partials/finance/salary_component_row.html', {
        'comp': comp,
        'faculty_id': faculty_id
    })

@login_required
def faculty_earnings_partial(request):
    """
    Main Intelligence Console for Faculty Earnings (v3).
    """
    faculty = get_object_or_404(Faculty, user=request.user, college=request.college)
    intel = FinancialIntelligenceService.get_faculty_financial_os_data(faculty, request.college)
    
    return render(request, 'dashboard/views/faculty/earnings_partial.html', {
        'intel': intel
    })

@login_required
def faculty_payout_details_drawer(request, payroll_id):
    """
    Context-preserving slide-in drawer for payout granular breakdown.
    """
    payroll = get_object_or_404(Payroll, id=payroll_id, college=request.college)
    return render(request, 'dashboard/views/finance/payout_details_drawer.html', {
        'pr': payroll,
        'breakdown': payroll.breakdown_json
    })
