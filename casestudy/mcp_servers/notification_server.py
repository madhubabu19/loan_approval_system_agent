"""
MCP Server: NotificationSystem
Serves compliance and notification tools to the Compliance & Action Orchestrator Agent.
"""
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP

mcp = FastMCP("NotificationSystem", instructions="Provides compliance actions and notification tools for loan decisions.")


@mcp.tool()
def generate_case_id(applicant_id: str) -> dict:
    """
    Generate a unique case ID for the loan application.
    Returns the case ID and creation timestamp.
    """
    timestamp = datetime.utcnow()
    case_id = f"LOAN-{applicant_id.upper()}-{timestamp.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    return {
        "case_id": case_id,
        "created_at": timestamp.isoformat() + "Z",
    }


@mcp.tool()
def send_approval_notification(
    applicant_id: str,
    case_id: str,
    loan_amount: float,
    loan_tenure_months: int,
    confidence_level: float,
) -> dict:
    """
    Send an approval notification to the applicant.
    Returns notification status and summary.
    """
    estimated_monthly_payment = (loan_amount / loan_tenure_months) * 1.1
    notification_content = (
        f"Dear Applicant {applicant_id},\n\n"
        f"Congratulations! Your loan application (Case ID: {case_id}) has been APPROVED.\n\n"
        f"Approved Amount: ${loan_amount:,.2f}\n"
        f"Tenure: {loan_tenure_months} months\n"
        f"Estimated Monthly Payment: ${estimated_monthly_payment:,.2f}\n"
        f"Decision Confidence: {confidence_level * 100:.0f}%\n\n"
        f"A loan officer will contact you within 2 business days to complete the documentation.\n\n"
        f"Thank you for choosing our services."
    )

    return {
        "notification_sent": True,
        "notification_type": "approval",
        "recipient": applicant_id,
        "case_id": case_id,
        "channel": "email",
        "content_preview": notification_content[:200] + "..." if len(notification_content) > 200 else notification_content,
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }


@mcp.tool()
def send_rejection_notification(
    applicant_id: str,
    case_id: str,
    key_reasons: list,
) -> dict:
    """
    Send a rejection notification to the applicant with reasons.
    Returns notification status and summary.
    """
    reasons_text = "\n".join(f"  - {r}" for r in key_reasons[:3])
    notification_content = (
        f"Dear Applicant {applicant_id},\n\n"
        f"We regret to inform you that your loan application (Case ID: {case_id}) has been DECLINED.\n\n"
        f"Primary reasons for this decision:\n{reasons_text}\n\n"
        f"You may reapply after 90 days or contact our support team for guidance on improving your application.\n\n"
        f"As required by law, you have the right to request a free copy of your credit report."
    )

    return {
        "notification_sent": True,
        "notification_type": "rejection",
        "recipient": applicant_id,
        "case_id": case_id,
        "channel": "email",
        "content_preview": notification_content[:200] + "...",
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }


@mcp.tool()
def send_manual_review_notification(
    applicant_id: str,
    case_id: str,
    review_reasons: list,
) -> dict:
    """
    Send a manual review notification to the applicant and internal review team.
    Returns notification status and summary.
    """
    reasons_text = "\n".join(f"  - {r}" for r in review_reasons[:3])
    notification_content = (
        f"Dear Applicant {applicant_id},\n\n"
        f"Your loan application (Case ID: {case_id}) is currently UNDER MANUAL REVIEW.\n\n"
        f"Factors requiring review:\n{reasons_text}\n\n"
        f"A loan specialist will review your application within 3-5 business days and contact you with a decision.\n\n"
        f"You may track your application status using Case ID: {case_id}."
    )

    return {
        "notification_sent": True,
        "notification_type": "manual_review",
        "recipient": applicant_id,
        "case_id": case_id,
        "channel": "email",
        "internal_team_notified": True,
        "content_preview": notification_content[:200] + "...",
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }


@mcp.tool()
def log_compliance_record(
    case_id: str,
    applicant_id: str,
    decision: str,
    risk_score: float,
    confidence_level: float,
    key_factors: list,
    explanation: str,
) -> dict:
    """
    Log the final compliance record for audit purposes.
    Returns the audit record details.
    """
    audit_record = {
        "case_id": case_id,
        "applicant_id": applicant_id,
        "decision": decision,
        "risk_score": risk_score,
        "confidence_level": confidence_level,
        "key_factors": key_factors,
        "explanation_summary": explanation[:300] if len(explanation) > 300 else explanation,
        "logged_at": datetime.utcnow().isoformat() + "Z",
        "compliance_standards": ["Fair Lending Act", "Equal Credit Opportunity Act", "GDPR"],
        "explainability_provided": True,
        "audit_trail_complete": True,
    }

    return {
        "record_logged": True,
        "audit_record": audit_record,
        "retention_period_years": 7,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
