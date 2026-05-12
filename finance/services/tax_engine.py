from decimal import Decimal
from finance.models import TaxRegime, TaxSlab

class TaxEngine:
    """
    Enterprise-Grade Tax Engine.
    Handles progressive slab accumulation, standard deductions, and rebates.
    """

    @staticmethod
    def calculate_monthly_tax(regime, annual_gross):
        """
        Calculates monthly TDS based on annual projected gross income and specific regime.
        """
        if not regime or not regime.is_active:
            return Decimal('0.00')

        # 1. Apply Standard Deduction
        taxable_income = max(Decimal(str(annual_gross)) - Decimal(str(regime.standard_deduction)), Decimal('0.00'))

        # 2. Check for Rebate Eligibility
        # (e.g., In India, if taxable income <= 5L, tax is rebated)
        if regime.rebate_limit and taxable_income <= regime.rebate_limit:
            # We still calculate tax, but we'll apply the rebate later
            pass

        # 3. Progressive Slab Calculation
        total_annual_tax = Decimal('0.00')
        slabs = regime.slabs.all().order_by('min_income')
        
        if not slabs.exists():
            return Decimal('0.00')

        remaining_income = taxable_income
        
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            # Determine income in this slab
            slab_min = slab.min_income
            slab_max = slab.max_income if slab.max_income else Decimal('Infinity')
            
            taxable_in_this_slab = 0
            if taxable_income > slab_min:
                upper = min(taxable_income, slab_max)
                taxable_in_this_slab = upper - slab_min
                
                # Calculate tax for this slab
                slab_tax = (taxable_in_this_slab * slab.tax_rate) / Decimal('100.00')
                total_annual_tax += slab_tax

        # 4. Apply Rebate
        if regime.rebate_limit and taxable_income <= regime.rebate_limit:
            total_annual_tax = max(total_annual_tax - regime.rebate_amount, Decimal('0.00'))

        # 5. Return Monthly TDS
        return round(total_annual_tax / Decimal('12.00'), 2)
