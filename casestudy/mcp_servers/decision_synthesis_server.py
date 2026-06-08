"""
MCP Server: DecisionSynthesis
Serves decision synthesis tools to the Loan Decision Agent.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

mcp = FastMCP("DecisionSynthesis", instructions="Provides decision synthesis tools for final loan classification.")


@mcp.tool()
def compute_composite_risk_score(
    income_stability_score: float,
    employment_risk: str,
    credit_score: int,
    dti_ratio: float,
    loan_amount_risk: str,
    anomaly_detected: bool,
) -> dict:
    """
    Compute a composite risk score by weighing all risk factors together.
    Returns a normalized risk score from 0 (lowest risk) to 100 (highest risk).
    """
    risk_score = 0.0

    income_risk = 100 - income_stability_score
    risk_score += income_risk * 0.20

    employment_weights = {"low": 0, "medium": 15, "high": 35}
    risk_score += employment_weights.get(employment_risk, 15) * 0.15

    if credit_score >= 750:
        credit_risk = 5
    elif credit_score >= 700:
        credit_risk = 15
    elif credit_score >= 650:
        credit_risk = 35
    elif credit_score >= 600:
        credit_risk = 55
    else:
        credit_risk = 80
    risk_score += credit_risk * 0.30

    dti_risk = min(100, dti_ratio * 1.5)
    risk_score += dti_risk * 0.25

    loan_amount_weights = {"low": 0, "medium": 20, "high": 45}
    risk_score += loan_amount_weights.get(loan_amount_risk, 20) * 0.10

    if anomaly_detected:
        risk_score = min(100, risk_score + 20)

    composite_risk_score = round(min(100, max(0, risk_score)), 2)

    return {
        "composite_risk_score": composite_risk_score,
        "component_scores": {
            "income_risk": round(income_risk, 2),
            "employment_risk_contribution": round(employment_weights.get(employment_risk, 15) * 0.15, 2),
            "credit_risk_contribution": round(credit_risk * 0.30, 2),
            "dti_risk_contribution": round(dti_risk * 0.25, 2),
            "loan_amount_risk_contribution": round(loan_amount_weights.get(loan_amount_risk, 20) * 0.10, 2),
            "anomaly_penalty": 20 if anomaly_detected else 0,
        },
    }


@mcp.tool()
def classify_loan_decision(
    composite_risk_score: float,
    credit_score: int,
    employment_type: str,
    dti_ratio: float,
    anomaly_detected: bool,
    application_flags: list,
) -> dict:
    """
    Classify the loan decision as Approved, Rejected, or Requires Manual Review
    based on the composite risk score and key factors.
    """
    has_errors = any(f.startswith("ERROR") for f in application_flags)
    if has_errors:
        return {
            "classification": "Rejected",
            "reason": "Application contains critical errors requiring correction.",
            "override_applied": True,
        }

    if employment_type == "unemployed":
        return {
            "classification": "Rejected",
            "reason": "Applicant is unemployed — no verified income source.",
            "override_applied": True,
        }

    if composite_risk_score < 30 and credit_score >= 650 and dti_ratio < 36:
        classification = "Approved"
        reason = "Low composite risk score with acceptable credit and DTI."
    elif composite_risk_score >= 70 or credit_score < 550:
        classification = "Rejected"
        reason = "Risk score too high or credit score critically low."
    elif anomaly_detected or (30 <= composite_risk_score < 50 and credit_score < 650):
        classification = "Requires Manual Review"
        reason = "Anomalies detected or borderline risk profile requires human review."
    elif 50 <= composite_risk_score < 70:
        classification = "Requires Manual Review"
        reason = "Elevated risk score requires human assessment."
    else:
        classification = "Approved"
        reason = "Acceptable risk profile within lending parameters."

    confidence = 1.0 - (composite_risk_score / 100) * 0.5
    if classification == "Rejected":
        confidence = 0.5 + (composite_risk_score / 100) * 0.5
    confidence = round(max(0.5, min(0.99, confidence)), 2)

    return {
        "classification": classification,
        "reason": reason,
        "confidence_level": confidence,
        "override_applied": False,
    }


@mcp.tool()
def extract_key_decision_factors(
    income_stability_score: float,
    employment_risk: str,
    credit_score: int,
    dti_ratio: float,
    loan_amount_risk: str,
    anomaly_detected: bool,
    composite_risk_score: float,
) -> dict:
    """
    Extract and rank the top factors driving the loan decision.
    Returns an ordered list of key decision factors.
    """
    factors = []

    if credit_score >= 750:
        factors.append(f"Strong credit score ({credit_score}) significantly improves approval chances")
    elif credit_score >= 650:
        factors.append(f"Acceptable credit score ({credit_score}) within standard lending criteria")
    else:
        factors.append(f"Below-average credit score ({credit_score}) increases default risk")

    if dti_ratio < 20:
        factors.append(f"Excellent debt-to-income ratio ({dti_ratio:.1f}%) — ample repayment capacity")
    elif dti_ratio < 36:
        factors.append(f"Manageable debt-to-income ratio ({dti_ratio:.1f}%) within acceptable limits")
    else:
        factors.append(f"High debt-to-income ratio ({dti_ratio:.1f}%) raises repayment concerns")

    if income_stability_score >= 70:
        factors.append(f"High income stability score ({income_stability_score:.0f}/100)")
    elif income_stability_score >= 45:
        factors.append(f"Moderate income stability score ({income_stability_score:.0f}/100)")
    else:
        factors.append(f"Low income stability score ({income_stability_score:.0f}/100) — income reliability concern")

    if employment_risk == "high":
        factors.append("High employment risk — unstable or no employment")
    elif employment_risk == "medium":
        factors.append("Moderate employment risk — consider income verification")

    if loan_amount_risk == "high":
        factors.append("Requested loan amount is high relative to income")
    elif loan_amount_risk == "medium":
        factors.append("Loan amount is within moderate risk range")

    if anomaly_detected:
        factors.append("Anomalies detected in application — requires investigation")

    return {
        "key_factors": factors[:5],
        "composite_risk_score": composite_risk_score,
        "total_factors_analyzed": len(factors),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
