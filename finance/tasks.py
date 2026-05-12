from celery import shared_task
from django.utils import timezone
from django.db import transaction
from finance.models import PayrollRunBatch, SalaryProfile, Payroll
from finance.services.compensation import CompensationEngine
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def execute_payroll_batch(self, batch_id):
    """
    SaaS-Grade Bulk Payroll Execution Task.
    Handles chunked processing, failure recovery, and real-time status updates.
    """
    try:
        batch = PayrollRunBatch.objects.get(id=batch_id)
        batch.status = 'PROCESSING'
        batch.save()

        # Fetch all active profiles for this college
        profiles = SalaryProfile.objects.filter(
            college=batch.college, 
            is_active=True
        )
        
        batch.total_records = profiles.count()
        batch.save()

        # Chunked Processing (Size 50 for stability)
        CHUNK_SIZE = 50
        processed_count = 0
        errors = []

        for i in range(0, batch.total_records, CHUNK_SIZE):
            chunk = profiles[i : i + CHUNK_SIZE]
            
            for profile in chunk:
                try:
                    with transaction.atomic():
                        # Check for idempotency (Don't duplicate if already exists)
                        if Payroll.objects.filter(
                            faculty=profile.faculty, 
                            month=batch.month, 
                            year=batch.year, 
                            college=batch.college
                        ).exists():
                            continue

                        # Calculate using Engine
                        calc = CompensationEngine.calculate_pay(profile, batch.month, batch.year)
                        
                        # Create Payroll record
                        Payroll.objects.create(
                            college=batch.college,
                            faculty=profile.faculty,
                            month=batch.month,
                            year=batch.year,
                            base_salary=calc['base'],
                            gross_salary=calc['gross'],
                            deductions=calc['deductions'],
                            net_salary=calc['net'],
                            ctc_amount=calc['ctc'],
                            breakdown_json=calc,
                            status='DRAFT'
                        )
                except Exception as e:
                    error_msg = f"Error processing {profile.faculty.user.get_full_name()}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                processed_count += 1
            
            # Update progress after each chunk
            batch.processed_records = processed_count
            batch.save()

        # Finalize Batch
        batch.status = 'COMPLETED' if not errors else 'FAILED'
        if errors:
            batch.error_log = {'errors': errors}
        batch.completed_at = timezone.now()
        batch.save()

    except Exception as e:
        logger.error(f"Batch {batch_id} failed: {str(e)}")
        if 'batch' in locals():
            batch.status = 'FAILED'
            batch.error_log = {'critical_error': str(e)}
            batch.save()
