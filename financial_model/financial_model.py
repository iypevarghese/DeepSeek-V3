# Financial Modeling Application for Specialized Optometry Services
# This script computes monthly projections, cash flows, and ratios based on
# user-defined inputs. It supports simple scenario analysis.

from dataclasses import dataclass, field
from typing import Dict, List
import pandas as pd

# --------------------------- Data Definitions ---------------------------
@dataclass
class Inputs:
    avg_patient_visits: int
    avg_revenue_per_visit: float
    monthly_product_sales: float
    fixed_overheads: float
    variable_cost_per_visit: float
    equipment_purchase: float
    receivable_days: int
    payable_days: int
    debt_interest_rate: float  # annual rate
    equity_injection: float

    def to_dict(self) -> Dict[str, float]:
        return self.__dict__


# --------------------------- Core Functions ----------------------------
MONTHS = [
    "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025", "Jun 2025",
    "Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025",
]


def build_projection(inputs: Inputs) -> pd.DataFrame:
    """Return a DataFrame with revenue and expense projections."""
    patient_revenue = [inputs.avg_patient_visits * inputs.avg_revenue_per_visit] * 12
    product_revenue = [inputs.monthly_product_sales] * 12
    total_revenue = [pr + prod for pr, prod in zip(patient_revenue, product_revenue)]
    variable_costs = [inputs.avg_patient_visits * inputs.variable_cost_per_visit] * 12
    gross_profit = [tr - vc for tr, vc in zip(total_revenue, variable_costs)]

    df = pd.DataFrame({
        "Month": MONTHS,
        "Patient Revenue": patient_revenue,
        "Product Revenue": product_revenue,
        "Total Revenue": total_revenue,
        "Variable Costs": variable_costs,
        "Gross Profit": gross_profit,
    })

    df["Fixed Overheads"] = inputs.fixed_overheads
    df["EBITDA"] = df["Gross Profit"] - df["Fixed Overheads"]
    # Straight-line depreciation over 5 years for equipment
    df["Depreciation"] = inputs.equipment_purchase / (5 * 12)
    df["EBIT"] = df["EBITDA"] - df["Depreciation"]
    opening_debt = 0.0
    df["Interest Expense"] = opening_debt * inputs.debt_interest_rate / 12
    df["Net Profit"] = df["EBIT"] - df["Interest Expense"]
    return df


def build_cash_flow(inputs: Inputs, projection: pd.DataFrame) -> pd.DataFrame:
    """Return the cash flow statement."""
    receivable_change = projection["Total Revenue"].diff().fillna(0) * inputs.receivable_days / 365
    payable_change = projection["Variable Costs"].diff().fillna(0) * inputs.payable_days / 365

    cash_from_ops = projection["Net Profit"] + projection["Depreciation"] - receivable_change + payable_change
    investing = [-inputs.equipment_purchase] + [0] * 11
    financing = [inputs.equity_injection] + [0] * 11

    net_change = cash_from_ops + investing + financing
    opening_cash: List[float] = [0]
    for change in net_change[:-1]:
        opening_cash.append(opening_cash[-1] + change)
    closing_cash = [o + n for o, n in zip(opening_cash, net_change)]

    cf = pd.DataFrame({
        "Month": MONTHS,
        "Cash from Operations": cash_from_ops,
        "Investing": investing,
        "Financing": financing,
        "Net Change in Cash": net_change,
        "Opening Cash": opening_cash,
        "Closing Cash": closing_cash,
    })
    return cf


def ratios(inputs: Inputs, projection: pd.DataFrame, cf: pd.DataFrame) -> Dict[str, float]:
    """Compute key financial ratios."""
    current_assets = projection["Total Revenue"].iloc[-1] * inputs.receivable_days / 365
    current_liabilities = projection["Variable Costs"].iloc[-1] * inputs.payable_days / 365
    current_ratio = current_assets / current_liabilities if current_liabilities else float("inf")

    operating_margin = projection["EBITDA"].sum() / projection["Total Revenue"].sum()
    return_on_equity = projection["Net Profit"].sum() / inputs.equity_injection
    debt_service_coverage = cf["Cash from Operations"].sum() / 1  # no debt repayments modeled

    return {
        "Current Ratio": current_ratio,
        "Operating Margin": operating_margin,
        "Return on Equity": return_on_equity,
        "Debt Service Coverage Ratio": debt_service_coverage,
    }


# --------------------------- Scenario Utility -------------------------
SCENARIOS = {
    "Base": 0.0,
    "Upside": 0.10,
    "Downside": -0.10,
}


def apply_scenario(inputs: Inputs, scenario: str) -> Inputs:
    """Return a new Inputs object adjusted for the scenario."""
    factor = 1 + SCENARIOS.get(scenario, 0)
    return Inputs(
        avg_patient_visits=inputs.avg_patient_visits,
        avg_revenue_per_visit=inputs.avg_revenue_per_visit * factor,
        monthly_product_sales=inputs.monthly_product_sales * factor,
        fixed_overheads=inputs.fixed_overheads,
        variable_cost_per_visit=inputs.variable_cost_per_visit,
        equipment_purchase=inputs.equipment_purchase,
        receivable_days=inputs.receivable_days,
        payable_days=inputs.payable_days,
        debt_interest_rate=inputs.debt_interest_rate,
        equity_injection=inputs.equity_injection,
    )


# --------------------------- Main Entry -------------------------------
def main():
    base_inputs = Inputs(
        avg_patient_visits=1200,
        avg_revenue_per_visit=1500.0,
        monthly_product_sales=50000.0,
        fixed_overheads=200000.0,
        variable_cost_per_visit=200.0,
        equipment_purchase=100000.0,
        receivable_days=30,
        payable_days=45,
        debt_interest_rate=0.085,
        equity_injection=500000.0,
    )

    scenario = "Base"  # change to "Upside" or "Downside" as needed
    scenario_inputs = apply_scenario(base_inputs, scenario)

    proj = build_projection(scenario_inputs)
    cf = build_cash_flow(scenario_inputs, proj)
    ratio_vals = ratios(scenario_inputs, proj, cf)

    print("Projection:\n", proj)
    print("\nCash Flow:\n", cf)
    print("\nRatios:")
    for k, v in ratio_vals.items():
        print(f"  {k}: {v:.2f}")


if __name__ == "__main__":
    main()
