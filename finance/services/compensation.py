import calendar
from datetime import date
from django.db.models import Q
from finance.models import SalaryProfile, ProfileComponent, SalaryComponent
from finance.services.tax_engine import TaxEngine
from decimal import Decimal

class CompensationEngine:
    """
    SaaS-Grade Compensation Engine for calculating complex payroll runs.
    Handles prioritized components, pro-rata logic, and CTC calculations.
    """

    @staticmethod
    def calculate_pay(profile, month, year):
        """
        Calculates full breakdown for a specific faculty profile and month.
        """
        base_salary = profile.base_salary
        
        # 1. Determine Pro-rata multiplier (if applicable)
        # For now, we assume full month. In a more advanced version, 
        # we'd compare effective_from/to against the month range.
        days_in_month = calendar.monthrange(year, month)[1]
        multiplier = 1.0 # Default full month
        
        # 2. Fetch components (Ordered by Priority)
        # We need both Profile-specific components and GLOBAL components
        components = ProfileComponent.objects.filter(
            profile=profile,
            component__is_active=True
        ).select_related('component').order_by('component__priority')
        
        # Add Global components that aren't already in the profile
        # (This handles mandatory taxes/fees defined at the college level)
        global_comps = SalaryComponent.objects.filter(
            college=profile.college,
            visibility_scope='GLOBAL',
            is_active=True
        ).exclude(id__in=[pc.component.id for pc in components])
        
        all_entries = []
        
        # Initial stats
        gross_salary = base_salary
        total_deductions = 0.0
        total_ctc_only = 0.0
        
        # 3. Multi-Pass Calculation logic
        # Pass 1: Allowances (Priority-based)
        for pc in components.filter(component__type='ALLOWANCE'):
            amt = CompensationEngine._resolve_value(pc.component, pc.value_override, base_salary, gross_salary)
            all_entries.append({
                'name': pc.component.name,
                'type': 'ALLOWANCE',
                'amount': amt,
                'impact': pc.component.impact_type
            })
            if pc.component.impact_type == 'NET':
                gross_salary += amt
            else:
                total_ctc_only += amt
                
        for gc in global_comps.filter(type='ALLOWANCE'):
            amt = CompensationEngine._resolve_value(gc, gc.default_value, base_salary, gross_salary)
            all_entries.append({
                'name': gc.name,
                'type': 'ALLOWANCE',
                'amount': amt,
                'impact': gc.impact_type
            })
            if gc.impact_type == 'NET':
                gross_salary += amt
            else:
                total_ctc_only += amt

        # Pass 2: Deductions (Scoped to Base or Gross)
        for pc in components.filter(component__type='DEDUCTION'):
            amt = CompensationEngine._resolve_value(pc.component, pc.value_override, base_salary, gross_salary)
            all_entries.append({
                'name': pc.component.name,
                'type': 'DEDUCTION',
                'amount': amt,
                'impact': pc.component.impact_type
            })
            if pc.component.impact_type == 'NET':
                total_deductions += amt
            else:
                total_ctc_only += amt
                
        for gc in global_comps.filter(type='DEDUCTION'):
            amt = CompensationEngine._resolve_value(gc, gc.default_value, base_salary, gross_salary)
            all_entries.append({
                'name': gc.name,
                'type': 'DEDUCTION',
                'amount': amt,
                'impact': gc.impact_type
            })
            if gc.impact_type == 'NET':
                total_deductions += amt
            else:
                total_ctc_only += amt

        # Pass 3: Tax Calculation (Compliance Layer)
        # Project annual gross to calculate slab-based tax
        annual_projected_gross = gross_salary * Decimal('12.00')
        monthly_tax = TaxEngine.calculate_monthly_tax(profile.tax_regime, annual_projected_gross)
        
        if monthly_tax > 0:
            all_entries.append({
                'name': 'Income Tax (TDS)',
                'type': 'DEDUCTION',
                'amount': float(monthly_tax),
                'impact': 'NET',
                'is_system': True
            })
            total_deductions += float(monthly_tax)

        # 4. Final Totals & Rounding
        net_salary = max(gross_salary - total_deductions, 0)
        ctc_amount = gross_salary + total_ctc_only
        
        return {
            'base': round(base_salary, 2),
            'gross': round(gross_salary, 2),
            'deductions': round(total_deductions, 2),
            'net': round(net_salary, 2),
            'ctc': round(ctc_amount, 2),
            'breakdown': all_entries,
            'warnings': [] if net_salary > 0 else ["⚠ Net salary reached zero"]
        }

    @staticmethod
    def _resolve_value(component, value, base, gross):
        """Helper to resolve percentage vs fixed amount based on scope."""
        if component.calc_type == 'FIXED':
            return value
        
        # Percentage logic
        scope_amount = base if component.calculation_scope == 'BASE' else gross
        return (value / 100.0) * scope_amount
