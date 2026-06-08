"""
MCP Server: ApplicantDB
Serves applicant profile analysis tools to the Applicant Profile Agent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

mcp = FastMCP("ApplicantDB", instructions="Provides applicant profile analysis tools for loan evaluation.")


@mcp.tool()
def analyze_income_stability(
    income: float,
    employment_type: str,
    age: int,
) -> dict:
    """
    Analyze income stability based on employment type, income level, and age.
    Returns an income stability score and employment risk level.
    """
    base_score = 50.0

    employment_scores = {
        "salaried": 30,
        "self-employed": 10,
        "contract": 15,
        "unemployed": -40,
    }
    base_score += employment_scores.get(employment_type, 0)

    # Income thresholds in INR (Indian Rupees)
    if income >= 1200000:       # ₹12,00,000+
        base_score += 20
    elif income >= 720000:      # ₹7,20,000+
        base_score += 15
    elif income >= 480000:      # ₹4,80,000+
        base_score += 5
    elif income >= 240000:      # ₹2,40,000+
        base_score -= 5
    else:
        base_score -= 20

    if 25 <= age <= 55:
        base_score += 5
    elif age < 25:
        base_score -= 10
    elif age > 60:
        base_score -= 5

    income_stability_score = max(0.0, min(100.0, base_score))

    if income_stability_score >= 70:
        employment_risk = "low"
    elif income_stability_score >= 45:
        employment_risk = "medium"
    else:
        employment_risk = "high"

    return {
        "income_stability_score": round(income_stability_score, 2),
        "employment_risk": employment_risk,
        "factors": {
            "employment_type": employment_type,
            "income_level": income,
            "age_group": "prime" if 25 <= age <= 55 else "non-prime",
        },
    }


@mcp.tool()
def get_credit_history_summary(credit_score: int) -> dict:
    """
    Generate a credit history summary based on credit score.
    Returns a textual summary and credit tier.
    """
    if credit_score >= 800:
        tier = "Exceptional"
        summary = "Exceptional credit history with consistent on-time payments and very low utilization."
    elif credit_score >= 740:
        tier = "Very Good"
        summary = "Very good credit history with mostly on-time payments and low utilization."
    elif credit_score >= 670:
        tier = "Good"
        summary = "Good credit history with occasional minor delinquencies and moderate utilization."
    elif credit_score >= 580:
        tier = "Fair"
        summary = "Fair credit history with some late payments or high utilization in the past."
    else:
        tier = "Poor"
        summary = "Poor credit history with significant delinquencies, defaults, or very high utilization."

    return {
        "credit_score": credit_score,
        "tier": tier,
        "summary": summary,
    }


@mcp.tool()
def check_application_completeness(
    applicant_id: str,
    age: int,
    income: float,
    employment_type: str,
    credit_score: int,
    loan_amount: float,
    loan_tenure_months: int,
    existing_liabilities: float,
    location: str,
) -> dict:
    """
    Check loan application for completeness and flag any missing or suspicious fields.
    Returns a list of completeness flags.
    """
    flags = []

    if age < 21:
        flags.append("WARNING: Applicant under 21 — may require co-signer")
    if age > 65:
        flags.append("WARNING: Applicant over 65 — loan tenure may exceed working years")

    if income <= 0:
        flags.append("ERROR: Invalid income value")

    if employment_type == "unemployed":
        flags.append("WARNING: Applicant is unemployed — income source unclear")

    if credit_score < 300 or credit_score > 850:
        flags.append("ERROR: Credit score out of valid range")

    if loan_amount <= 0:
        flags.append("ERROR: Invalid loan amount")

    if loan_tenure_months < 6 or loan_tenure_months > 360:
        flags.append("ERROR: Loan tenure out of valid range")

    if not location.strip():
        flags.append("WARNING: Location not specified")

    if loan_amount > income * 10:
        flags.append("WARNING: Loan amount exceeds 10x annual income")

    monthly_income = income / 12
    if existing_liabilities > monthly_income * 0.5:
        flags.append("WARNING: Existing liabilities exceed 50% of monthly income")

    if not flags:
        flags.append("Application is complete with no flags")

    return {"applicant_id": applicant_id, "completeness_flags": flags, "is_complete": len([f for f in flags if f.startswith("ERROR")]) == 0}


if __name__ == "__main__":
    mcp.run(transport="stdio")
