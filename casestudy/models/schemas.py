from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class LoanApplication(BaseModel):
    applicant_id: str = Field(..., description="Unique applicant identifier")
    age: int = Field(..., ge=18, le=80, description="Applicant age")
    income: float = Field(..., gt=0, description="Annual income in USD")
    employment_type: Literal["salaried", "self-employed", "contract", "unemployed"] = Field(
        ..., description="Type of employment"
    )
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount in USD")
    loan_tenure_months: int = Field(..., ge=6, le=360, description="Loan tenure in months")
    existing_liabilities: float = Field(default=0.0, ge=0, description="Total existing monthly liabilities in USD")
    location: str = Field(..., description="Applicant location/city")
    application_timestamp: Optional[datetime] = Field(default=None, description="Application submission time")


class ApplicantProfileOutput(BaseModel):
    income_stability_score: float = Field(..., ge=0, le=100)
    employment_risk: Literal["low", "medium", "high"]
    credit_history_summary: str
    application_completeness_flags: list[str]


class FinancialRiskOutput(BaseModel):
    debt_to_income_ratio: float
    credit_score_risk_level: Literal["low", "medium", "high", "very_high"]
    loan_amount_risk: Literal["low", "medium", "high"]
    anomaly_detected: bool
    anomaly_details: Optional[str]
    reasoning: str


class LoanDecisionOutput(BaseModel):
    classification: Literal["Approved", "Rejected", "Requires Manual Review"]
    risk_score: float = Field(..., ge=0, le=100)
    confidence_level: float = Field(..., ge=0, le=1)
    key_decision_factors: list[str]
    explanation: str


class ComplianceOutput(BaseModel):
    action_taken: str
    notification_sent: bool
    case_id: str
    timestamp: str
    summary: str


class LoanProcessingResult(BaseModel):
    applicant_profile: Optional[ApplicantProfileOutput] = None
    financial_risk: Optional[FinancialRiskOutput] = None
    loan_decision: Optional[LoanDecisionOutput] = None
    compliance: Optional[ComplianceOutput] = None
    error: Optional[str] = None
