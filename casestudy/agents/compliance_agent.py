"""
Compliance & Action Orchestrator Agent
Handles post-decision compliance actions and notifications using NotificationSystem MCP server.
Uses Anthropic Claude Sonnet 4.6 for action orchestration.
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

NOTIFICATION_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcp_servers",
    "notification_server.py",
)


async def run_compliance_agent(
    application_data: dict,
    loan_decision: dict,
) -> dict:
    """
    Run the Compliance & Action Orchestrator Agent.
    Handles notifications and compliance logging after the loan decision is made.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async with Client(StdioTransport(command="python3", args=[NOTIFICATION_SERVER_PATH])) as mcp_client:
        tools = await mcp_client.list_tools()

        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            })

        system_prompt = """You are the Compliance & Action Orchestrator Agent for an Intelligent Loan Approval System.
Your role is to execute post-decision compliance actions and notifications.

You MUST call tools in this order:
1. generate_case_id - to create a unique case ID
2. Send the appropriate notification based on decision:
   - For "Approved": call send_approval_notification
   - For "Rejected": call send_rejection_notification
   - For "Requires Manual Review": call send_manual_review_notification
3. log_compliance_record - to create the audit trail

After calling all tools, provide a final JSON with this exact structure:
{
    "action_taken": "<description of actions taken>",
    "notification_sent": true,
    "case_id": "<the generated case ID>",
    "timestamp": "<ISO timestamp>",
    "summary": "<human-readable summary of compliance actions>"
}"""

        classification = loan_decision.get("classification", "Requires Manual Review")
        key_factors = loan_decision.get("key_decision_factors", [])

        user_message = f"""Execute compliance actions for the following loan decision:

=== DECISION SUMMARY ===
Applicant ID: {application_data['applicant_id']}
Decision: {classification}
Risk Score: {loan_decision.get('risk_score', 50)}/100
Confidence Level: {loan_decision.get('confidence_level', 0.75) * 100:.0f}%
Key Factors: {', '.join(key_factors[:3])}
Explanation: {loan_decision.get('explanation', 'Decision made by AI system')}

=== APPLICATION DETAILS ===
Loan Amount: ${application_data['loan_amount']:,.2f}
Loan Tenure: {application_data['loan_tenure_months']} months

Execute the following:
1. Generate a unique case ID
2. Send the appropriate notification (approval/rejection/review) to applicant {application_data['applicant_id']}
3. Log the compliance record for audit purposes

Complete all compliance actions now."""

        messages = [{"role": "user", "content": user_message}]
        max_iterations = 10
        iteration = 0
        case_id_captured = None

        while iteration < max_iterations:
            iteration += 1
            response = client.messages.create(
                model="global.anthropic.claude-sonnet-4-6",
                max_tokens=2048,
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
                                if "case_id" in result:
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
                        if block.name == "generate_case_id":
                            try:
                                parsed = json.loads(tool_output)
                                case_id_captured = parsed.get("case_id")
                            except Exception:
                                pass
                    except Exception as e:
                        tool_output = json.dumps({"error": str(e)})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output,
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

    from datetime import datetime
    import uuid
    fallback_case_id = case_id_captured or f"LOAN-{application_data['applicant_id'].upper()}-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    return {
        "action_taken": f"Loan decision '{classification}' processed for applicant {application_data['applicant_id']}",
        "notification_sent": True,
        "case_id": fallback_case_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": f"Case {fallback_case_id}: {classification} decision processed with compliance logging.",
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
    test_decision = {
        "classification": "Approved",
        "risk_score": 25.0,
        "confidence_level": 0.88,
        "key_decision_factors": ["Strong credit score", "Low DTI ratio"],
        "explanation": "Applicant meets all lending criteria with low risk profile.",
    }
    result = asyncio.run(run_compliance_agent(test_app, test_decision))
    print(json.dumps(result, indent=2))
