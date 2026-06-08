"""
MCP Server: RiskRulesDB
Serves financial risk analysis tools to the Financial Risk Analysis Agent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

mcp = FastMCP("RiskRulesDB", instructions="Provides financial risk analysis tools using risk rules database.")


@mcp.tool()
def calculate_debt_to_income_ratio(
    monthly_income: float,
    existing_liabilities: float,
    proposed_loan_amount: float,
    loan_tenure_months: int,
) -> dict:
    """
    Calculate the debt-to-income (DTI) ratio including the proposed loan payment.
    Returns DTI ratio and risk assessment.
    """
    if monthly_income <= 0:
        return {"error": "Monthly income must be positive", "dti_ratio": None}

    estimated_monthly_payment = (proposed_loan_amount / loan_tenure_months) * 1.1
    total_monthly_debt = existing_liabilities + estimated_monthly_payment
    dti_ratio = (total_monthly_debt / monthly_income) * 100

    if dti_ratio < 20:
        dti_risk = "low"
        assessment = "Excellent DTI ratio — borrower has significant capacity for new debt."
    elif dti_ratio < 36:
        dti_risk = "medium"
        assessment = "Acceptable DTI ratio — borrower can manage new debt with some caution."
    elif dti_ratio < 50:
        dti_risk = "high"
        assessment = "High DTI ratio — borrower may struggle with additional debt obligations."
    else:
        dti_risk = "very_high"
        assessment = "Very high DTI ratio — borrower is likely over-leveraged."

    return {
        "monthly_income": monthly_income,
        "existing_liabilities": existing_liabilities,
        "estimated_loan_payment": round(estimated_monthly_payment, 2),
        "total_monthly_debt": round(total_monthly_debt, 2),
        "dti_ratio": round(dti_ratio, 2),
        "dti_risk": dti_risk,
        "assessment": assessment,
    }


@mcp.tool()
def assess_credit_score_risk(credit_score: int) -> dict:
    """
    Assess the risk level based on credit score using standard lending risk rules.
    Returns risk level and detailed assessment.
    """
    if credit_score >= 750:
        risk_level = "low"
        approval_likelihood = "high"
        notes = "Excellent creditworthiness. Prime lending candidate."
    elif credit_score >= 700:
        risk_level = "low"
        approval_likelihood = "high"
        notes = "Good creditworthiness. Standard loan terms applicable."
    elif credit_score >= 650:
        risk_level = "medium"
        approval_likelihood = "medium"
        notes = "Moderate creditworthiness. May require higher interest rate."
    elif credit_score >= 600:
        risk_level = "high"
        approval_likelihood = "low"
        notes = "Below-average creditworthiness. Requires manual review."
    else:
        risk_level = "very_high"
        approval_likelihood = "very_low"
        notes = "Poor creditworthiness. High default risk."

    return {
        "credit_score": credit_score,
        "risk_level": risk_level,
        "approval_likelihood": approval_likelihood,
        "notes": notes,
    }


@mcp.tool()
def evaluate_loan_amount_risk(
    loan_amount: float,
    annual_income: float,
    credit_score: int,
    loan_tenure_months: int,
) -> dict:
    """
    Evaluate the risk associated with the requested loan amount relative to income.
    Returns risk level and lending policy assessment.
    """
    loan_to_income_ratio = loan_amount / annual_income if annual_income > 0 else float("inf")

    monthly_income = annual_income / 12
    estimated_monthly_payment = (loan_amount / loan_tenure_months) * 1.1
    payment_to_income = (estimated_monthly_payment / monthly_income) * 100 if monthly_income > 0 else 100

    if loan_to_income_ratio < 2 and payment_to_income < 20:
        risk_level = "low"
        policy_assessment = "Loan amount within conservative lending limits."
    elif loan_to_income_ratio < 4 and payment_to_income < 35:
        risk_level = "medium"
        policy_assessment = "Loan amount acceptable but warrants standard review."
    elif loan_to_income_ratio < 7:
        risk_level = "high"
        policy_assessment = "Loan amount high relative to income — enhanced review required."
    else:
        risk_level = "high"
        policy_assessment = "Loan amount exceeds safe lending thresholds for this income level."

    if credit_score >= 720 and risk_level == "high":
        risk_level = "medium"
        policy_assessment += " Good credit score partially offsets loan amount risk."

    return {
        "loan_amount": loan_amount,
        "annual_income": annual_income,
        "loan_to_income_ratio": round(loan_to_income_ratio, 2),
        "estimated_monthly_payment": round(estimated_monthly_payment, 2),
        "payment_to_income_pct": round(payment_to_income, 2),
        "risk_level": risk_level,
        "policy_assessment": policy_assessment,
    }


@mcp.tool()
def detect_anomalies(
    applicant_id: str,
    age: int,
    income: float,
    employment_type: str,
    credit_score: int,
    loan_amount: float,
    existing_liabilities: float,
) -> dict:
    """
    Detect anomalies or suspicious patterns in the loan application data.
    Returns anomaly flag and details.
    """
    anomalies = []

    # Thresholds in INR (Indian Rupees)
    if employment_type == "unemployed" and income > 60000:      # ₹60,000/yr
        anomalies.append("Unemployed applicant reporting significant income — income source unverified.")

    if credit_score > 800 and existing_liabilities > income * 0.4:
        anomalies.append("High credit score with disproportionately high liabilities — possible recent financial stress.")

    if loan_amount > income * 8:
        anomalies.append(f"Loan amount (₹{loan_amount:,.0f}) is more than 8x annual income (₹{income:,.0f}) — unusually high.")

    if age < 22 and income > 960000:                            # ₹9,60,000/yr
        anomalies.append("Very young applicant with high income — verify income source.")

    if credit_score < 500 and loan_amount > 600000:             # ₹6,00,000
        anomalies.append("Poor credit score with large loan request — high default risk.")

    if existing_liabilities > income / 12 * 0.7:
        anomalies.append("Monthly liabilities exceed 70% of monthly income — potential debt trap.")

    return {
        "applicant_id": applicant_id,
        "anomaly_detected": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "anomaly_details": anomalies if anomalies else ["No anomalies detected"],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
