"""
Loan Decision Agent
Makes the final loan classification using the DecisionSynthesis MCP server.
Uses Anthropic Claude Sonnet 4.6 for synthesis and explanation.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from dotenv import load_dotenv

load_dotenv()

DECISION_SYNTHESIS_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcp_servers",
    "decision_synthesis_server.py",
)


async def run_loan_decision_agent(
    application_data: dict,
    applicant_profile: dict,
    financial_risk: dict,
) -> dict:
    """
    Run the Loan Decision Agent to synthesize all analysis and make the final decision.
    Uses DecisionSynthesis MCP server and Claude Sonnet 4.6.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async with Client(StdioTransport(command="python3", args=[DECISION_SYNTHESIS_SERVER_PATH])) as mcp_client:
        tools = await mcp_client.list_tools()

        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            })

        system_prompt = """You are the Loan Decision Agent for an Intelligent Loan Approval System.
Your role is to synthesize all prior analysis and make the final loan decision.

You MUST call ALL THREE tools in order:
1. compute_composite_risk_score - combining all risk factors into a single score
2. classify_loan_decision - to determine Approve/Reject/Review based on risk score
3. extract_key_decision_factors - to identify the most important factors driving the decision

After calling all tools, provide a final JSON with this exact structure:
{
    "classification": "<Approved|Rejected|Requires Manual Review>",
    "risk_score": <float 0-100>,
    "confidence_level": <float 0-1>,
    "key_decision_factors": ["<factor1>", "<factor2>", ...],
    "explanation": "<detailed human-readable explanation of the decision>"
}

The explanation must be clear, fair, and explainable to the applicant."""

        application_flags = applicant_profile.get("application_completeness_flags", [])

        user_message = f"""Make the final loan decision based on all prior analysis:

=== APPLICATION DATA ===
Applicant ID: {application_data['applicant_id']}
Annual Income: ${application_data['income']:,.2f}
Employment Type: {application_data['employment_type']}
Credit Score: {application_data['credit_score']}
Loan Amount: ${application_data['loan_amount']:,.2f}
Loan Tenure: {application_data['loan_tenure_months']} months
Existing Monthly Liabilities: ${application_data['existing_liabilities']:,.2f}

=== APPLICANT PROFILE ANALYSIS ===
Income Stability Score: {applicant_profile.get('income_stability_score', 50)}/100
Employment Risk: {applicant_profile.get('employment_risk', 'medium')}
Credit History: {applicant_profile.get('credit_history_summary', 'N/A')}
Completeness Flags: {', '.join(application_flags)}

=== FINANCIAL RISK ANALYSIS ===
Debt-to-Income Ratio: {financial_risk.get('debt_to_income_ratio', 0):.2f}%
Credit Score Risk Level: {financial_risk.get('credit_score_risk_level', 'medium')}
Loan Amount Risk: {financial_risk.get('loan_amount_risk', 'medium')}
Anomaly Detected: {financial_risk.get('anomaly_detected', False)}
Anomaly Details: {financial_risk.get('anomaly_details', 'None')}
Risk Reasoning: {financial_risk.get('reasoning', 'N/A')}

Use all three tools to compute the composite risk score, classify the decision, and extract key factors."""

        messages = [{"role": "user", "content": user_message}]
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            response = client.messages.create(
                model="global.anthropic.claude-sonnet-4-6",
                max_tokens=3000,
                system=system_prompt,
                tools=claude_tools,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        text = block.text
                        try:
                            start = text.find("{")
                            end = text.rfind("}") + 1
                            if start >= 0 and end > start:
                                result = json.loads(text[start:end])
                                if "classification" in result:
                                    return result
                        except json.JSONDecodeError:
                            pass
                break

            if response.stop_reason != "tool_use":
                break

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        result = await mcp_client.call_tool(block.name, block.input)
                        tool_output = result.content[0].text if result.content else "{}"
                    except Exception as e:
                        tool_output = json.dumps({"error": str(e)})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output,
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

    credit_score = application_data.get("credit_score", 650)
    dti = financial_risk.get("debt_to_income_ratio", 40)

    if credit_score >= 700 and dti < 36:
        classification = "Approved"
    elif credit_score < 580 or dti >= 60:
        classification = "Rejected"
    else:
        classification = "Requires Manual Review"

    return {
        "classification": classification,
        "risk_score": 50.0,
        "confidence_level": 0.75,
        "key_decision_factors": ["Credit score evaluation", "Debt-to-income ratio assessment"],
        "explanation": f"Decision based on credit score of {credit_score} and DTI ratio of {dti:.1f}%.",
    }


if __name__ == "__main__":
    test_app = {
        "applicant_id": "TEST001",
        "age": 35,
        "income": 75000,
        "employment_type": "salaried",
        "credit_score": 720,
        "loan_amount": 150000,
        "loan_tenure_months": 120,
        "existing_liabilities": 1500,
        "location": "New York",
    }
    test_profile = {
        "income_stability_score": 75,
        "employment_risk": "low",
        "credit_history_summary": "Good credit history",
        "application_completeness_flags": ["Application complete"],
    }
    test_risk = {
        "debt_to_income_ratio": 28.5,
        "credit_score_risk_level": "low",
        "loan_amount_risk": "medium",
        "anomaly_detected": False,
        "anomaly_details": None,
        "reasoning": "Standard risk profile",
    }
    result = asyncio.run(run_loan_decision_agent(test_app, test_profile, test_risk))
    print(json.dumps(result, indent=2))
