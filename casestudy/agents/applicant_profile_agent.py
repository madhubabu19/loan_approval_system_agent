"""
Applicant Profile Agent
Analyzes applicant profile data using the ApplicantDB MCP server.
Uses Anthropic Claude Sonnet 4.6 for reasoning and analysis.
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

APPLICANT_DB_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcp_servers",
    "applicant_db_server.py",
)


async def run_applicant_profile_agent(application_data: dict) -> dict:
    """
    Run the Applicant Profile Agent to analyze applicant profile data.
    Connects to ApplicantDB MCP server and uses Claude Sonnet 4.6 for analysis.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async with Client(StdioTransport(command="python3", args=[APPLICANT_DB_SERVER_PATH])) as mcp_client:
        tools = await mcp_client.list_tools()

        claude_tools = []
        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            })

        system_prompt = """You are the Applicant Profile Agent for an Intelligent Loan Approval System.
Your role is to analyze applicant profile data using the ApplicantDB tools provided.

You MUST call ALL THREE tools in this order:
1. analyze_income_stability - to get income stability score and employment risk
2. get_credit_history_summary - to get credit history summary
3. check_application_completeness - to verify all application fields

After calling all tools, synthesize the results into a final JSON response with this exact structure:
{
    "income_stability_score": <float 0-100>,
    "employment_risk": "<low|medium|high>",
    "credit_history_summary": "<string>",
    "application_completeness_flags": ["<flag1>", "<flag2>", ...]
}

Be thorough and call all tools before providing the final structured output."""

        user_message = f"""Analyze the following loan application profile:

Applicant ID: {application_data['applicant_id']}
Age: {application_data['age']}
Annual Income: ${application_data['income']:,.2f}
Employment Type: {application_data['employment_type']}
Credit Score: {application_data['credit_score']}
Loan Amount: ${application_data['loan_amount']:,.2f}
Loan Tenure: {application_data['loan_tenure_months']} months
Existing Monthly Liabilities: ${application_data['existing_liabilities']:,.2f}
Location: {application_data['location']}

Please analyze this applicant's profile thoroughly using all available tools."""

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
                    tool_name = block.name
                    tool_input = block.input

                    try:
                        result = await mcp_client.call_tool(tool_name, tool_input)
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

    return {
        "income_stability_score": 50.0,
        "employment_risk": "medium",
        "credit_history_summary": "Analysis completed with fallback values.",
        "application_completeness_flags": ["Analysis completed"],
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
    result = asyncio.run(run_applicant_profile_agent(test_application))
    print(json.dumps(result, indent=2))
