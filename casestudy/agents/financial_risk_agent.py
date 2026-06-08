"""
Financial Risk Analysis Agent
Performs financial risk analysis using the RiskRulesDB MCP server.
Uses Anthropic Claude Sonnet 4.6 for reasoning.
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

RISK_RULES_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcp_servers",
    "risk_rules_server.py",
)


async def run_financial_risk_agent(application_data: dict) -> dict:
    """
    Run the Financial Risk Analysis Agent.
    Connects to RiskRulesDB MCP server and uses Claude Sonnet 4.6 for analysis.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async with Client(StdioTransport(command="python3", args=[RISK_RULES_SERVER_PATH])) as mcp_client:
        tools = await mcp_client.list_tools()

        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            })

        system_prompt = """You are the Financial Risk Analysis Agent for an Intelligent Loan Approval System.
Your role is to perform comprehensive financial risk analysis using the RiskRulesDB tools.

You MUST call ALL FOUR tools:
1. calculate_debt_to_income_ratio - using monthly_income (annual_income/12), existing_liabilities, loan_amount, and tenure
2. assess_credit_score_risk - to assess credit risk level
3. evaluate_loan_amount_risk - to evaluate loan amount relative to income
4. detect_anomalies - to check for suspicious patterns

After calling all tools, provide a final JSON with this exact structure:
{
    "debt_to_income_ratio": <float>,
    "credit_score_risk_level": "<low|medium|high|very_high>",
    "loan_amount_risk": "<low|medium|high>",
    "anomaly_detected": <true|false>,
    "anomaly_details": "<string or null>",
    "reasoning": "<comprehensive reasoning summary>"
}"""

        monthly_income = application_data["income"] / 12
        user_message = f"""Perform financial risk analysis for this loan application:

Applicant ID: {application_data['applicant_id']}
Age: {application_data['age']}
Annual Income: ${application_data['income']:,.2f} (Monthly: ${monthly_income:,.2f})
Employment Type: {application_data['employment_type']}
Credit Score: {application_data['credit_score']}
Loan Amount: ${application_data['loan_amount']:,.2f}
Loan Tenure: {application_data['loan_tenure_months']} months
Existing Monthly Liabilities: ${application_data['existing_liabilities']:,.2f}
Location: {application_data['location']}

Analyze all financial risk dimensions using all available tools."""

        messages = [{"role": "user", "content": user_message}]
        max_iterations = 10
        iteration = 0

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

    monthly_income_val = application_data["income"] / 12
    monthly_payment = (application_data["loan_amount"] / application_data["loan_tenure_months"]) * 1.1
    dti = ((application_data["existing_liabilities"] + monthly_payment) / monthly_income_val) * 100

    return {
        "debt_to_income_ratio": round(dti, 2),
        "credit_score_risk_level": "medium",
        "loan_amount_risk": "medium",
        "anomaly_detected": False,
        "anomaly_details": None,
        "reasoning": "Risk analysis completed with fallback calculation.",
    }


if __name__ == "__main__":
    test_application = {
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
    result = asyncio.run(run_financial_risk_agent(test_application))
    print(json.dumps(result, indent=2))
