"""
LangGraph Orchestration Engine
Coordinates all 4 agents in the loan approval workflow using LangGraph state machine.
"""
import asyncio
import os
import sys
from typing import TypedDict, Optional, Annotated
import operator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from agents.applicant_profile_agent import run_applicant_profile_agent
from agents.financial_risk_agent import run_financial_risk_agent
from agents.loan_decision_agent import run_loan_decision_agent
from agents.compliance_agent import run_compliance_agent

load_dotenv()


class LoanWorkflowState(TypedDict):
    """State object passed between nodes in the LangGraph workflow."""
    application_data: dict
    applicant_profile: Optional[dict]
    financial_risk: Optional[dict]
    loan_decision: Optional[dict]
    compliance_result: Optional[dict]
    error: Optional[str]
    processing_log: Annotated[list, operator.add]


async def applicant_profile_node(state: LoanWorkflowState) -> dict:
    """LangGraph node: runs the Applicant Profile Agent."""
    print("[Orchestrator] Running Applicant Profile Agent...")
    try:
        result = await run_applicant_profile_agent(state["application_data"])
        return {
            "applicant_profile": result,
            "processing_log": ["Applicant Profile Agent completed successfully"],
        }
    except Exception as e:
        error_msg = f"Applicant Profile Agent failed: {str(e)}"
        print(f"[Orchestrator] ERROR: {error_msg}")
        return {
            "applicant_profile": {
                "income_stability_score": 50.0,
                "employment_risk": "medium",
                "credit_history_summary": "Analysis unavailable due to error",
                "application_completeness_flags": [f"Error: {str(e)}"],
            },
            "processing_log": [error_msg],
        }


async def financial_risk_node(state: LoanWorkflowState) -> dict:
    """LangGraph node: runs the Financial Risk Analysis Agent."""
    print("[Orchestrator] Running Financial Risk Analysis Agent...")
    try:
        result = await run_financial_risk_agent(state["application_data"])
        return {
            "financial_risk": result,
            "processing_log": ["Financial Risk Analysis Agent completed successfully"],
        }
    except Exception as e:
        error_msg = f"Financial Risk Agent failed: {str(e)}"
        print(f"[Orchestrator] ERROR: {error_msg}")
        app = state["application_data"]
        monthly_income = app["income"] / 12
        monthly_payment = (app["loan_amount"] / app["loan_tenure_months"]) * 1.1
        dti = ((app["existing_liabilities"] + monthly_payment) / monthly_income) * 100
        return {
            "financial_risk": {
                "debt_to_income_ratio": round(dti, 2),
                "credit_score_risk_level": "medium",
                "loan_amount_risk": "medium",
                "anomaly_detected": False,
                "anomaly_details": None,
                "reasoning": f"Fallback calculation used. Error: {str(e)}",
            },
            "processing_log": [error_msg],
        }


async def loan_decision_node(state: LoanWorkflowState) -> dict:
    """LangGraph node: runs the Loan Decision Agent."""
    print("[Orchestrator] Running Loan Decision Agent...")
    try:
        result = await run_loan_decision_agent(
            state["application_data"],
            state["applicant_profile"],
            state["financial_risk"],
        )
        return {
            "loan_decision": result,
            "processing_log": [f"Loan Decision Agent completed: {result.get('classification', 'Unknown')}"],
        }
    except Exception as e:
        error_msg = f"Loan Decision Agent failed: {str(e)}"
        print(f"[Orchestrator] ERROR: {error_msg}")
        credit_score = state["application_data"].get("credit_score", 650)
        dti = state["financial_risk"].get("debt_to_income_ratio", 50) if state.get("financial_risk") else 50
        if credit_score >= 700 and dti < 36:
            classification = "Approved"
        elif credit_score < 580 or dti >= 60:
            classification = "Rejected"
        else:
            classification = "Requires Manual Review"
        return {
            "loan_decision": {
                "classification": classification,
                "risk_score": 50.0,
                "confidence_level": 0.70,
                "key_decision_factors": ["Credit score", "Debt-to-income ratio"],
                "explanation": f"Fallback decision based on core metrics. Error: {str(e)}",
            },
            "processing_log": [error_msg],
        }


async def compliance_node(state: LoanWorkflowState) -> dict:
    """LangGraph node: runs the Compliance & Action Orchestrator Agent."""
    print("[Orchestrator] Running Compliance & Action Orchestrator Agent...")
    try:
        result = await run_compliance_agent(
            state["application_data"],
            state["loan_decision"],
        )
        return {
            "compliance_result": result,
            "processing_log": [f"Compliance Agent completed. Case ID: {result.get('case_id', 'N/A')}"],
        }
    except Exception as e:
        error_msg = f"Compliance Agent failed: {str(e)}"
        print(f"[Orchestrator] ERROR: {error_msg}")
        from datetime import datetime
        import uuid
        app = state["application_data"]
        decision = state.get("loan_decision", {})
        fallback_case_id = f"LOAN-{app['applicant_id'].upper()}-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        return {
            "compliance_result": {
                "action_taken": f"Decision '{decision.get('classification', 'Unknown')}' logged",
                "notification_sent": False,
                "case_id": fallback_case_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "summary": f"Compliance logging completed with errors: {str(e)}",
            },
            "processing_log": [error_msg],
        }


def should_proceed_after_profile(state: LoanWorkflowState) -> str:
    """Routing function: check if we should continue after profile analysis."""
    profile = state.get("applicant_profile", {})
    flags = profile.get("application_completeness_flags", [])
    critical_errors = [f for f in flags if f.startswith("ERROR")]
    if len(critical_errors) >= 2:
        print("[Orchestrator] Critical application errors detected — routing to compliance for rejection")
        return "compliance_direct"
    return "financial_risk"


def build_loan_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow for loan processing."""
    workflow = StateGraph(LoanWorkflowState)

    workflow.add_node("applicant_profile", applicant_profile_node)
    workflow.add_node("financial_risk", financial_risk_node)
    workflow.add_node("loan_decision", loan_decision_node)
    workflow.add_node("compliance", compliance_node)

    async def compliance_direct_node(state: LoanWorkflowState) -> dict:
        """Direct compliance path for critically invalid applications."""
        app = state["application_data"]
        flags = state.get("applicant_profile", {}).get("application_completeness_flags", [])
        state_copy = {
            **state,
            "loan_decision": {
                "classification": "Rejected",
                "risk_score": 95.0,
                "confidence_level": 0.99,
                "key_decision_factors": flags[:3],
                "explanation": "Application rejected due to critical data errors that prevent proper evaluation.",
            }
        }
        return await compliance_node(state_copy)

    workflow.add_node("compliance_direct", compliance_direct_node)

    workflow.set_entry_point("applicant_profile")

    workflow.add_conditional_edges(
        "applicant_profile",
        should_proceed_after_profile,
        {
            "financial_risk": "financial_risk",
            "compliance_direct": "compliance_direct",
        },
    )

    workflow.add_edge("financial_risk", "loan_decision")
    workflow.add_edge("loan_decision", "compliance")
    workflow.add_edge("compliance", END)
    workflow.add_edge("compliance_direct", END)

    return workflow.compile()


async def process_loan_application(application_data: dict) -> dict:
    """
    Main entry point: process a loan application through the full multi-agent workflow.
    Returns a LoanProcessingResult-compatible dict.
    """
    print(f"\n[Orchestrator] Starting loan processing for applicant: {application_data['applicant_id']}")
    print("[Orchestrator] Initializing LangGraph workflow...")

    graph = build_loan_workflow()

    initial_state: LoanWorkflowState = {
        "application_data": application_data,
        "applicant_profile": None,
        "financial_risk": None,
        "loan_decision": None,
        "compliance_result": None,
        "error": None,
        "processing_log": [f"Workflow started for applicant {application_data['applicant_id']}"],
    }

    final_state = await graph.ainvoke(initial_state)

    print(f"[Orchestrator] Workflow complete. Decision: {final_state.get('loan_decision', {}).get('classification', 'Unknown')}")

    return {
        "applicant_profile": final_state.get("applicant_profile"),
        "financial_risk": final_state.get("financial_risk"),
        "loan_decision": final_state.get("loan_decision"),
        "compliance": final_state.get("compliance_result"),
        "error": final_state.get("error"),
        "processing_log": final_state.get("processing_log", []),
    }


if __name__ == "__main__":
    import json

    test_application = {
        "applicant_id": "TEST001",
        "age": 35,
        "income": 75000.0,
        "employment_type": "salaried",
        "credit_score": 720,
        "loan_amount": 150000.0,
        "loan_tenure_months": 120,
        "existing_liabilities": 1500.0,
        "location": "New York",
    }

    result = asyncio.run(process_loan_application(test_application))
    print("\n=== FINAL RESULT ===")
    print(json.dumps(result, indent=2, default=str))
