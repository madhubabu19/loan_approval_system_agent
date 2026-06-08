"""
FastAPI Microservice Layer
Receives and validates loan application data, then passes it to the LangGraph orchestrator.
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import LoanApplication, LoanProcessingResult
from orchestrator.graph import process_loan_application

load_dotenv()

app = FastAPI(
    title="Agentic AI Intelligent Loan Approval System",
    description="Multi-agent AI system for automated loan approval using LangGraph and Claude Sonnet 4.6",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processing_cache: dict = {}


@app.get("/")
async def root():
    return {
        "service": "Agentic AI Intelligent Loan Approval System",
        "version": "1.0.0",
        "status": "operational",
        "agents": [
            "Applicant Profile Agent (MCP: ApplicantDB)",
            "Financial Risk Analysis Agent (MCP: RiskRulesDB)",
            "Loan Decision Agent (MCP: DecisionSynthesis)",
            "Compliance & Action Orchestrator Agent (MCP: NotificationSystem)",
        ],
        "orchestration": "LangGraph",
        "llm": "Anthropic Claude Sonnet 4.6",
    }


@app.get("/health")
async def health_check():
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_api_key_here")
    return {
        "status": "healthy",
        "api_key_configured": api_key_set,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/loan/process", response_model=dict)
async def process_loan(application: LoanApplication):
    """
    Submit a loan application for multi-agent AI processing.

    The application is processed through 4 agents:
    1. Applicant Profile Agent — analyzes income, employment, credit
    2. Financial Risk Analysis Agent — calculates DTI, risk levels, anomalies
    3. Loan Decision Agent — synthesizes final classification
    4. Compliance & Action Orchestrator Agent — handles notifications and audit logging
    """
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_anthropic_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Please set it in the .env file.",
        )

    if application.application_timestamp is None:
        application.application_timestamp = datetime.utcnow()

    application_dict = {
        "applicant_id": application.applicant_id,
        "age": application.age,
        "income": application.income,
        "employment_type": application.employment_type,
        "credit_score": application.credit_score,
        "loan_amount": application.loan_amount,
        "loan_tenure_months": application.loan_tenure_months,
        "existing_liabilities": application.existing_liabilities,
        "location": application.location,
        "application_timestamp": application.application_timestamp.isoformat(),
    }

    try:
        result = await process_loan_application(application_dict)

        response = {
            "success": True,
            "applicant_id": application.applicant_id,
            "applicant_profile": result.get("applicant_profile"),
            "financial_risk": result.get("financial_risk"),
            "loan_decision": result.get("loan_decision"),
            "compliance": result.get("compliance"),
            "processing_log": result.get("processing_log", []),
        }

        if result.get("compliance", {}) and result["compliance"].get("case_id"):
            processing_cache[result["compliance"]["case_id"]] = response

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Loan processing failed: {str(e)}",
        )


@app.get("/api/loan/status/{case_id}")
async def get_loan_status(case_id: str):
    """Retrieve the status and result of a previously processed loan application."""
    if case_id in processing_cache:
        return processing_cache[case_id]
    raise HTTPException(
        status_code=404,
        detail=f"Case ID '{case_id}' not found. It may have expired or not been processed.",
    )


@app.get("/api/loan/sample")
async def get_sample_application():
    """Returns a sample loan application for testing."""
    return {
        "applicant_id": "SAMPLE001",
        "age": 32,
        "income": 85000.0,
        "employment_type": "salaried",
        "credit_score": 730,
        "loan_amount": 200000.0,
        "loan_tenure_months": 180,
        "existing_liabilities": 2000.0,
        "location": "San Francisco, CA",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
