"""
Comprehensive property calculation engine
Adapted from PropEngineV1 with enhanced functionality for PortSight
"""
import pandas as pd
import numpy as np
import numpy_financial as npf
import xirr
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Dict, Optional, Any
from .schemas import PropertyAssumptions, PropertyMetrics, PortfolioMetrics


class PropertyCalculationEngine:
    """Main calculation engine for property financial analysis"""
    
    def __init__(self):
        pass
    
    def calculate_property_metrics(self, assumptions: PropertyAssumptions) -> PropertyMetrics:
        """
        Calculate comprehensive property metrics from assumptions
        
        Args:
            assumptions: Property assumptions for modeling
            
        Returns:
            PropertyMetrics: Calculated metrics and cash flows
        """
        # Build monthly cash flow projections
        monthly_df = self._build_monthly_cash_flows(assumptions)
        
        # Build equity cash flows
        equity_df = self._build_equity_cash_flows(assumptions, monthly_df)
        
        # Build cash-on-cash table
        coc_table = self._build_cash_on_cash_table(assumptions, monthly_df, equity_df)
        
        # Calculate all metrics
        metrics = self._calculate_all_metrics(assumptions, monthly_df, equity_df, coc_table)
        
        return metrics
    
    def _build_monthly_cash_flows(self, a: PropertyAssumptions) -> pd.DataFrame:
        """Build monthly cash flow projections"""
        # Create date index: first full month after closing
        first_month = (a.date_of_close + relativedelta(months=+1)).replace(day=1)
        idx = pd.date_range(start=first_month, periods=a.hold_period_months + 12, freq='MS')
        
        # Month counter for formulas (n starts at 1)
        month = pd.Series(np.arange(1, len(idx) + 1, dtype=int), index=idx, name="Month")
        year = pd.Series(np.ceil(month/12).astype(int), index=idx, name="Year")
        
        df = pd.DataFrame(index=idx)
        df["MonthNum"] = month
        df["YearNum"] = year
        df["YearsFrac"] = (month-1)/12
        df["YearsFloor"] = np.floor((month-1)/12)
        
        # Add income and operations
        df = self._add_income_operations(df, a)
        
        return df
    
    def _add_income_operations(self, df: pd.DataFrame, a: PropertyAssumptions) -> pd.DataFrame:
        """Add income and operating expense calculations"""
        # Base calculations
        rent_base = a.property_sf * a.gross_potential_rent_per_sf_per_year / 12
        other_income_base = a.property_sf * a.total_other_income_per_sf_per_year / 12
        opex_base = a.property_sf * a.operating_expenses_per_sf_per_year / 12
        capres_base = a.property_sf * a.capital_reserve_per_sf_per_year / 12
        
        # Revenue calculations with growth
        df["GrossPotentialRent"] = rent_base * (1 + a.annual_rent_growth_rate) ** df["YearsFrac"]
        df["GeneralVacancy"] = -df["GrossPotentialRent"] * a.general_vacancy_rate
        df["NetRentalRevenue"] = df["GrossPotentialRent"] + df["GeneralVacancy"]
        
        df["OtherIncome"] = other_income_base * (1 + a.annual_other_income_growth_rate) ** df["YearsFrac"]
        df["EffectiveGrossRevenue"] = df["NetRentalRevenue"] + df["OtherIncome"]
        
        # Expense calculations with growth
        df["OperatingExpenses"] = -opex_base * (1 + a.annual_expense_growth_rate) ** df["YearsFrac"]
        df["NetOperatingIncome"] = df["EffectiveGrossRevenue"] + df["OperatingExpenses"]
        
        df["CapitalReserve"] = -capres_base * (1 + a.capital_reserve_growth_rate) ** df["YearsFloor"]
        df["CapitalImprovements"] = 0.0
        
        # Capital improvements logic
        cis = max(int(getattr(a, "capital_improvement_start_month", 1)), 1)
        cie = min(int(getattr(a, "capital_improvement_end_month", 0)), int(a.hold_period_months))
        
        cap_total = float(a.total_capital_improvements)
        if cap_total > 0 and cie >= cis:
            duration = cie - cis + 1
            monthly = cap_total / duration
            mask = (df["MonthNum"] >= cis) & (df["MonthNum"] <= cie)
            df.loc[mask, "CapitalImprovements"] = -monthly
        
        df["CashFlowBeforeDebtService"] = df["NetOperatingIncome"] + df["CapitalReserve"] + df["CapitalImprovements"]
        
        # Debt service calculations
        per = df["MonthNum"].to_numpy()
        nper = int(a.amortization_years * 12)
        rate = a.interest_rate / 12.0
        pv = a.purchase_price * a.ltv
        
        ip = npf.ipmt(rate, per, nper, pv)  # negative
        pp = npf.ppmt(rate, per, nper, pv)  # negative
        ip = np.where(per <= nper, ip, 0.0)
        pp = np.where(per <= nper, pp, 0.0)
        
        df["InterestPayment"] = ip
        df["PrincipalPayment"] = pp
        df["CashFlowAfterDebtService"] = df["CashFlowBeforeDebtService"] + ip + pp
        
        return df
    
    def _build_equity_cash_flows(self, a: PropertyAssumptions, df_full: pd.DataFrame) -> pd.DataFrame:
        """Build equity cash flow projections including sale"""
        ops = df_full.iloc[:a.hold_period_months].copy()
        
        # Calculate sale price based on exit cap rate
        f12_noi = df_full["NetOperatingIncome"].iloc[a.hold_period_months:a.hold_period_months + 12].sum()
        sale_price = f12_noi / a.exit_cap_rate
        sale_costs = sale_price * a.cost_of_sale_percentage
        
        # Loan calculations
        loan_amount = a.purchase_price * a.ltv
        loan_origin_fee = loan_amount * a.loan_origination_fee
        principal_paid = -ops["PrincipalPayment"].sum()
        loan_payoff_exit = max(loan_amount - principal_paid, 0)
        
        # Create equity cash flow dataframe
        eq_index = [a.date_of_close] + ops.index.tolist()
        eq = pd.DataFrame(index=pd.Index(eq_index, name="Date"))
        
        # Initialize columns
        eq["PurchasePrice"] = 0.0
        eq["ClosingCosts"] = 0.0
        eq["SaleProceeds"] = 0.0
        eq["CostOfSale"] = 0.0
        eq["UnleveredCashFlow"] = 0.0
        eq["LoanProceeds"] = 0.0
        eq["LoanOriginationFee"] = 0.0
        eq["LoanPayoff"] = 0.0
        eq["LeveredCashFlow"] = 0.0
        
        # Acquisition (month 0)
        eq.iloc[0, eq.columns.get_loc("PurchasePrice")] = -a.purchase_price
        eq.iloc[0, eq.columns.get_loc("ClosingCosts")] = -a.closing_costs
        eq.iloc[0, eq.columns.get_loc("LoanProceeds")] = loan_amount
        eq.iloc[0, eq.columns.get_loc("LoanOriginationFee")] = -loan_origin_fee
        
        eq.iloc[0, eq.columns.get_loc("UnleveredCashFlow")] = eq.iloc[0]["PurchasePrice"] + eq.iloc[0]["ClosingCosts"]
        eq.iloc[0, eq.columns.get_loc("LeveredCashFlow")] = (eq.iloc[0]["UnleveredCashFlow"] + 
                                                             eq.iloc[0]["LoanProceeds"] + 
                                                             eq.iloc[0]["LoanOriginationFee"])
        
        # Operating periods
        eq.iloc[1:, eq.columns.get_loc("UnleveredCashFlow")] = ops["CashFlowBeforeDebtService"].values
        eq.iloc[1:, eq.columns.get_loc("LeveredCashFlow")] = ops["CashFlowAfterDebtService"].values
        
        # Sale (final period)
        eq.iloc[-1, eq.columns.get_loc("UnleveredCashFlow")] += sale_price - sale_costs
        eq.iloc[-1, eq.columns.get_loc("LeveredCashFlow")] += sale_price - sale_costs - loan_payoff_exit
        
        eq.iloc[-1, eq.columns.get_loc("SaleProceeds")] = sale_price
        eq.iloc[-1, eq.columns.get_loc("CostOfSale")] = -sale_costs
        eq.iloc[-1, eq.columns.get_loc("LoanPayoff")] = -loan_payoff_exit
        
        return eq
    
    def _build_cash_on_cash_table(self, a: PropertyAssumptions, df_full: pd.DataFrame, eq: pd.DataFrame) -> pd.DataFrame:
        """Build cash-on-cash return table"""
        acq = pd.Timestamp(a.date_of_close)
        idx = pd.DatetimeIndex([acq] + list(df_full.index), name="Date")
        cols = [
            "YearNum",
            "CashFlowBeforeDebtService",
            "CashFlowAfterDebtService",
            "UnleveredCashFlow",
            "LeveredCashFlow",
        ]
        
        tbl = pd.DataFrame(index=idx, columns=cols)
        tbl[:] = 0
        
        tbl.at[acq, "YearNum"] = 0
        
        # Map data from monthly and equity dataframes
        common_df = df_full.index.intersection(tbl.index)
        if not common_df.empty:
            tbl.loc[common_df, "YearNum"] = df_full.loc[common_df, "YearNum"]
            tbl.loc[common_df, "CashFlowBeforeDebtService"] = df_full.loc[common_df, "CashFlowBeforeDebtService"]
            tbl.loc[common_df, "CashFlowAfterDebtService"] = df_full.loc[common_df, "CashFlowAfterDebtService"]
        
        common_eq = eq.index.intersection(tbl.index)
        if not common_eq.empty:
            tbl.loc[common_eq, "UnleveredCashFlow"] = eq.loc[common_eq, "UnleveredCashFlow"]
            tbl.loc[common_eq, "LeveredCashFlow"] = eq.loc[common_eq, "LeveredCashFlow"]
        
        # Calculate cash-on-cash returns
        hold_years = int(a.hold_period_months / 12)
        coc_cols = ["UnleveredCashonCash", "LeveredCashonCash"]
        
        coc_index = pd.Index(np.arange(0, hold_years + 1), name="Year")
        coc_tbl = pd.DataFrame(index=coc_index, columns=coc_cols, dtype=float)
        coc_tbl[:] = np.nan
        
        unlevered_cost = a.purchase_price + a.closing_costs
        levered_cost = (unlevered_cost - a.purchase_price * a.ltv + 
                       a.purchase_price * a.ltv * a.loan_origination_fee)
        
        for i in range(1, hold_years + 1):
            c_mask = tbl["YearNum"] == i
            unlevered_cf = tbl.loc[c_mask, "UnleveredCashFlow"].sum()
            levered_cf = tbl.loc[c_mask, "LeveredCashFlow"].sum()
            coc_tbl.at[i, "UnleveredCashonCash"] = unlevered_cf / unlevered_cost if unlevered_cost != 0 else np.nan
            coc_tbl.at[i, "LeveredCashonCash"] = levered_cf / levered_cost if levered_cost != 0 else np.nan
        
        return coc_tbl
    
    def _calculate_all_metrics(self, a: PropertyAssumptions, df: pd.DataFrame, 
                              eq: pd.DataFrame, coc_tbl: pd.DataFrame) -> PropertyMetrics:
        """Calculate all property metrics"""
        
        # Going-in metrics
        going_in_cap_rate = self._going_in_cap_rate(df, a)
        going_in_dscr = self._going_in_dscr(a, df)
        going_in_debt_yield = self._going_in_debt_yield(a, df)
        loan_constant = self._loan_constant(a, df)
        year1_op_ex_ratio = self._year1_op_ex_ratio(df)
        
        # Exit metrics
        exit_ltv = self._exit_ltv(a, eq)
        
        # Return metrics
        unlevered_irr = self._unlevered_irr(eq)
        levered_irr = self._levered_irr(eq)
        unlevered_equity_multiple = self._unlevered_equity_multiple(eq)
        levered_equity_multiple = self._levered_equity_multiple(eq)
        avg_unlevered_coc = self._avg_unlevered_coc(coc_tbl, a)
        avg_levered_coc = self._avg_levered_coc(coc_tbl, a)
        
        return PropertyMetrics(
            going_in_cap_rate=going_in_cap_rate,
            going_in_dscr=going_in_dscr,
            going_in_debt_yield=going_in_debt_yield,
            loan_constant=loan_constant,
            year1_op_ex_ratio=year1_op_ex_ratio,
            exit_ltv=exit_ltv,
            unlevered_irr=unlevered_irr,
            levered_irr=levered_irr,
            unlevered_equity_multiple=unlevered_equity_multiple,
            levered_equity_multiple=levered_equity_multiple,
            avg_unlevered_coc=avg_unlevered_coc,
            avg_levered_coc=avg_levered_coc,
            monthly_cash_flows=df.to_dict('index'),
            equity_cash_flows=eq.to_dict('index'),
            cash_on_cash_table=coc_tbl.to_dict('index')
        )
    
    # Individual metric calculation methods
    def _going_in_cap_rate(self, df: pd.DataFrame, a: PropertyAssumptions) -> float:
        """Calculate going-in cap rate"""
        noi = df.iloc[0:12]["NetOperatingIncome"].sum()
        return noi / a.purchase_price
    
    def _loan_constant(self, a: PropertyAssumptions, df: pd.DataFrame) -> float:
        """Calculate loan constant"""
        loan_amount = a.purchase_price * a.ltv
        total_debt_service = (df.iloc[0:12]["PrincipalPayment"].sum() + 
                             df.iloc[0:12]["InterestPayment"].sum())
        return total_debt_service / loan_amount
    
    def _going_in_dscr(self, a: PropertyAssumptions, df: pd.DataFrame) -> float:
        """Calculate going-in debt service coverage ratio"""
        noi = df.iloc[0:12]["NetOperatingIncome"].sum()
        total_debt_service = (df.iloc[0:12]["PrincipalPayment"].sum() + 
                             df.iloc[0:12]["InterestPayment"].sum())
        return noi / total_debt_service if total_debt_service != 0 else np.nan
    
    def _going_in_debt_yield(self, a: PropertyAssumptions, df: pd.DataFrame) -> float:
        """Calculate going-in debt yield"""
        loan_amount = a.purchase_price * a.ltv
        noi = df.iloc[0:12]["NetOperatingIncome"].sum()
        return noi / loan_amount if loan_amount != 0 else np.nan
    
    def _exit_ltv(self, a: PropertyAssumptions, eq: pd.DataFrame) -> float:
        """Calculate exit LTV"""
        s_proceeds = eq["SaleProceeds"].sum()
        loan_payoff = eq["LoanPayoff"].sum()
        return loan_payoff / s_proceeds if s_proceeds != 0 and loan_payoff != 0 else np.nan
    
    def _unlevered_irr(self, eq: pd.DataFrame) -> Optional[float]:
        """Calculate unlevered IRR using XIRR"""
        series = eq["UnleveredCashFlow"]
        lib = {}
        for ts, val in series.items():
            if val == 0:
                continue
            if hasattr(ts, "date"):
                dt = ts.date()
            else:
                dt = ts
            lib[dt] = float(val)
        try:
            return xirr.xirr(lib)
        except Exception:
            return None
    
    def _levered_irr(self, eq: pd.DataFrame) -> Optional[float]:
        """Calculate levered IRR using XIRR"""
        series = eq["LeveredCashFlow"]
        lib = {}
        for ts, val in series.items():
            if val == 0:
                continue
            if hasattr(ts, "date"):
                dt = ts.date()
            else:
                dt = ts
            lib[dt] = float(val)
        try:
            return xirr.xirr(lib)
        except Exception:
            return None
    
    def _unlevered_equity_multiple(self, eq: pd.DataFrame) -> float:
        """Calculate unlevered equity multiple"""
        total_invested = eq["UnleveredCashFlow"].loc[eq["UnleveredCashFlow"] < 0].sum()
        total_returned = eq["UnleveredCashFlow"].loc[eq["UnleveredCashFlow"] > 0].sum()
        return total_returned / abs(total_invested) if total_invested != 0 else 0
    
    def _levered_equity_multiple(self, eq: pd.DataFrame) -> float:
        """Calculate levered equity multiple"""
        total_invested = eq["LeveredCashFlow"].loc[eq["LeveredCashFlow"] < 0].sum()
        total_returned = eq["LeveredCashFlow"].loc[eq["LeveredCashFlow"] > 0].sum()
        return total_returned / abs(total_invested) if total_invested != 0 else 0
    
    def _avg_unlevered_coc(self, coc_tbl: pd.DataFrame, a: PropertyAssumptions) -> float:
        """Calculate average unlevered cash-on-cash return"""
        effective_hold = a.hold_period_months if a.hold_period_months <= len(coc_tbl) else len(coc_tbl)
        return coc_tbl["UnleveredCashonCash"].iloc[0:effective_hold].mean()
    
    def _avg_levered_coc(self, coc_tbl: pd.DataFrame, a: PropertyAssumptions) -> float:
        """Calculate average levered cash-on-cash return"""
        effective_hold = a.hold_period_months if a.hold_period_months <= len(coc_tbl) else len(coc_tbl)
        return coc_tbl["LeveredCashonCash"].iloc[0:effective_hold].mean()
    
    def _year1_op_ex_ratio(self, df: pd.DataFrame) -> float:
        """Calculate year 1 operating expense ratio"""
        total_op_ex = df.iloc[0:12]["OperatingExpenses"].sum()
        total_egr = df.iloc[0:12]["EffectiveGrossRevenue"].sum()
        return total_op_ex / total_egr if total_egr != 0 else 0


# Portfolio-level calculations
def calculate_portfolio_metrics(property_metrics_list: list) -> PortfolioMetrics:
    """
    Calculate portfolio-level aggregated metrics
    
    Args:
        property_metrics_list: List of PropertyMetrics objects
        
    Returns:
        PortfolioMetrics: Aggregated portfolio metrics
    """
    if not property_metrics_list:
        return PortfolioMetrics(
            total_equity=0, total_value=0, total_debt=0,
            avg_irr_actual=0, avg_irr_target=0, avg_dscr=0, avg_ltv=0,
            variance_irr=0, variance_noi=0
        )
    
    # Calculate totals and averages
    total_equity = sum(getattr(m, 'total_equity', 0) for m in property_metrics_list)
    total_value = sum(getattr(m, 'total_value', 0) for m in property_metrics_list)
    total_debt = sum(getattr(m, 'total_debt', 0) for m in property_metrics_list)
    
    # IRR calculations
    irr_values = [m.levered_irr for m in property_metrics_list if m.levered_irr is not None]
    avg_irr_actual = np.mean(irr_values) if irr_values else 0
    
    # DSCR and LTV calculations
    dscr_values = [m.going_in_dscr for m in property_metrics_list if not np.isnan(m.going_in_dscr)]
    avg_dscr = np.mean(dscr_values) if dscr_values else 0
    
    ltv_values = [m.exit_ltv for m in property_metrics_list if not np.isnan(m.exit_ltv)]
    avg_ltv = np.mean(ltv_values) if ltv_values else 0
    
    # Variance calculations
    variance_irr = np.var(irr_values) if len(irr_values) > 1 else 0
    variance_noi = 0  # Would need NOI data to calculate
    
    return PortfolioMetrics(
        total_equity=total_equity,
        total_value=total_value,
        total_debt=total_debt,
        avg_irr_actual=avg_irr_actual,
        avg_irr_target=avg_irr_actual,  # Using actual as target for now
        avg_dscr=avg_dscr,
        avg_ltv=avg_ltv,
        variance_irr=variance_irr,
        variance_noi=variance_noi
    )


# Convenience function for easy integration
def calculate_property_analysis(assumptions_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to calculate property analysis from dictionary input
    
    Args:
        assumptions_dict: Dictionary containing property assumptions
        
    Returns:
        Dictionary containing calculated metrics and cash flows
    """
    # Convert dictionary to PropertyAssumptions object
    assumptions = PropertyAssumptions(**assumptions_dict)
    
    # Calculate metrics
    engine = PropertyCalculationEngine()
    metrics = engine.calculate_property_metrics(assumptions)
    
    # Convert to dictionary for JSON serialization
    return {
        'going_in_metrics': {
            'cap_rate': metrics.going_in_cap_rate,
            'dscr': metrics.going_in_dscr,
            'debt_yield': metrics.going_in_debt_yield,
            'loan_constant': metrics.loan_constant,
            'op_ex_ratio': metrics.year1_op_ex_ratio
        },
        'exit_metrics': {
            'ltv': metrics.exit_ltv
        },
        'return_metrics': {
            'unlevered_irr': metrics.unlevered_irr,
            'levered_irr': metrics.levered_irr,
            'unlevered_equity_multiple': metrics.unlevered_equity_multiple,
            'levered_equity_multiple': metrics.levered_equity_multiple,
            'avg_unlevered_coc': metrics.avg_unlevered_coc,
            'avg_levered_coc': metrics.avg_levered_coc
        },
        'cash_flows': {
            'monthly': metrics.monthly_cash_flows,
            'equity': metrics.equity_cash_flows,
            'cash_on_cash': metrics.cash_on_cash_table
        }
    }