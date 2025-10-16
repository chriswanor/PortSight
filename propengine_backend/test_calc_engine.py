"""
Test script to demonstrate the enhanced calculation engine
"""
from services.calc_engine import calculate_property_analysis
from datetime import date

def test_property_calculation():
    """Test the property calculation engine with sample data"""
    
    # Sample property assumptions
    sample_assumptions = {
        "property_sf": 2000,
        "purchase_price": 500000,
        "date_of_close": date(2024, 1, 1),
        "ltv": 0.75,
        "interest_rate": 0.065,
        "amortization_years": 30,
        "hold_period_months": 60,
        "gross_potential_rent_per_sf_per_year": 18.0,
        "total_other_income_per_sf_per_year": 1.0,
        "general_vacancy_rate": 0.05,
        "annual_rent_growth_rate": 0.03,
        "annual_other_income_growth_rate": 0.02,
        "operating_expenses_per_sf_per_year": 6.0,
        "capital_reserve_per_sf_per_year": 1.0,
        "annual_expense_growth_rate": 0.03,
        "capital_reserve_growth_rate": 0.02,
        "total_capital_improvements": 25000,
        "capital_improvement_start_month": 1,
        "capital_improvement_end_month": 12,
        "exit_cap_rate": 0.055,
        "cost_of_sale_percentage": 0.03,
        "closing_costs": 10000,
        "loan_origination_fee": 0.01,
    }
    
    try:
        # Calculate property metrics
        results = calculate_property_analysis(sample_assumptions)
        
        print("=== PROPERTY ANALYSIS RESULTS ===")
        print(f"Property: {sample_assumptions['property_sf']} sq ft, ${sample_assumptions['purchase_price']:,}")
        print()
        
        print("GOING-IN METRICS:")
        going_in = results["going_in_metrics"]
        print(f"  Cap Rate: {going_in['cap_rate']:.2%}")
        print(f"  DSCR: {going_in['dscr']:.2f}x")
        print(f"  Debt Yield: {going_in['debt_yield']:.2%}")
        print(f"  Loan Constant: {going_in['loan_constant']:.2%}")
        print(f"  Op Ex Ratio: {going_in['op_ex_ratio']:.2%}")
        print()
        
        print("RETURN METRICS:")
        returns = results["return_metrics"]
        print(f"  Levered IRR: {returns['levered_irr']:.2%}" if returns['levered_irr'] else "  Levered IRR: N/A")
        print(f"  Unlevered IRR: {returns['unlevered_irr']:.2%}" if returns['unlevered_irr'] else "  Unlevered IRR: N/A")
        print(f"  Levered Equity Multiple: {returns['levered_equity_multiple']:.2f}x")
        print(f"  Unlevered Equity Multiple: {returns['unlevered_equity_multiple']:.2f}x")
        print(f"  Avg Levered CoC: {returns['avg_levered_coc']:.2%}")
        print(f"  Avg Unlevered CoC: {returns['avg_unlevered_coc']:.2%}")
        print()
        
        print("EXIT METRICS:")
        exit_metrics = results["exit_metrics"]
        print(f"  Exit LTV: {exit_metrics['ltv']:.2%}" if not exit_metrics['ltv'] != exit_metrics['ltv'] else "  Exit LTV: N/A")
        print()
        
        print("CASH FLOW SUMMARY:")
        monthly_cf = results["cash_flows"]["monthly"]
        equity_cf = results["cash_flows"]["equity"]
        
        # Show first year cash flows
        first_year_cf = sum(v.get("CashFlowAfterDebtService", 0) for k, v in monthly_cf.items() if k.month <= 12)
        print(f"  Year 1 Cash Flow: ${first_year_cf:,.2f}")
        
        # Show total equity invested and returned
        total_invested = sum(v.get("LeveredCashFlow", 0) for v in equity_cf.values() if v.get("LeveredCashFlow", 0) < 0)
        total_returned = sum(v.get("LeveredCashFlow", 0) for v in equity_cf.values() if v.get("LeveredCashFlow", 0) > 0)
        print(f"  Total Equity Invested: ${abs(total_invested):,.2f}")
        print(f"  Total Equity Returned: ${total_returned:,.2f}")
        print(f"  Net Profit: ${total_returned + total_invested:,.2f}")
        
        return results
        
    except Exception as e:
        print(f"Error in calculation: {str(e)}")
        return None

if __name__ == "__main__":
    test_property_calculation()
