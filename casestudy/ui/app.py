"""
Streamlit Chatbot UI
Loan application submission and result display for the Agentic AI Loan Approval System.
"""
import streamlit as st
import httpx
import json
import asyncio
from datetime import datetime

FASTAPI_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Loan Approval System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .agent-card {
        background: #f8f9fa;
        border-left: 4px solid #0f3460;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .approved-badge {
        background: #28a745;
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2em;
    }
    .rejected-badge {
        background: #dc3545;
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2em;
    }
    .review-badge {
        background: #ffc107;
        color: black;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2em;
    }
    .metric-box {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .chat-message {
        padding: 10px 15px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
    }
    .user-message {
        background: #0f3460;
        color: white;
        margin-left: auto;
    }
    .bot-message {
        background: #f1f3f4;
        color: #333;
    }
    .stProgress > div > div {
        background-color: #0f3460;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "processing" not in st.session_state:
    st.session_state.processing = False

st.markdown("""
<div class="main-header">
    <h1>🏦 Agentic AI Intelligent Loan Approval System</h1>
    <p>Powered by Multi-Agent AI with LangGraph Orchestration & Anthropic Claude Sonnet 4.6</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🤖 System Architecture")
    st.markdown("""
    **Agents:**
    - 👤 Applicant Profile Agent
    - 📊 Financial Risk Analysis Agent
    - ⚖️ Loan Decision Agent
    - ✅ Compliance & Action Orchestrator

    **Technology Stack:**
    - 🔗 LangGraph Orchestration
    - 🛠️ FastMCP (4 MCP Servers)
    - 🤖 Claude Sonnet 4.6 (LLM)
    - 🚀 FastAPI Microservice
    - 🎨 Streamlit UI
    """)

    st.markdown("---")
    st.markdown("## 📋 MCP Servers")
    st.markdown("""
    - **ApplicantDB** — Profile analysis
    - **RiskRulesDB** — Risk evaluation
    - **DecisionSynthesis** — Decision making
    - **NotificationSystem** — Compliance
    """)

    st.markdown("---")
    if st.button("📝 Fill Sample Application", use_container_width=True):
        st.session_state["prefill"] = True

    st.markdown("---")
    st.markdown("### 🔗 API Status")
    try:
        response = httpx.get(f"{FASTAPI_URL}/health", timeout=3)
        if response.status_code == 200:
            health = response.json()
            if health.get("api_key_configured"):
                st.success("✅ API: Online")
            else:
                st.warning("⚠️ API: Online (No API Key)")
        else:
            st.error("❌ API: Offline")
    except Exception:
        st.error("❌ API: Offline\nStart with: python main.py")

tab1, tab2, tab3 = st.tabs(["📝 Submit Application", "📊 Analysis Results", "💬 Chat History"])

with tab1:
    st.markdown("### 📋 Loan Application Form")

    prefill = st.session_state.pop("prefill", False)
    default_vals = {
        "applicant_id": "APP-2024-001",
        "age": 32,
        "income": 1000000.0,
        "employment_type": "salaried",
        "credit_score": 730,
        "loan_amount": 2500000.0,
        "loan_tenure_months": 180,
        "existing_liabilities": 25000.0,
        "location": "Mumbai, Maharashtra",
    } if prefill else {
        "applicant_id": "",
        "age": 30,
        "income": 600000.0,
        "employment_type": "salaried",
        "credit_score": 650,
        "loan_amount": 1500000.0,
        "loan_tenure_months": 120,
        "existing_liabilities": 8000.0,
        "location": "",
    }

    with st.form("loan_application_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 👤 Applicant Information")
            applicant_id = st.text_input("Applicant ID *", value=default_vals["applicant_id"], placeholder="e.g., APP-2024-001")
            age = st.number_input("Age *", min_value=18, max_value=80, value=default_vals["age"])
            income = st.number_input("Annual Income (₹ INR) *", min_value=1000.0, value=default_vals["income"], step=10000.0, format="%.2f")
            employment_type = st.selectbox(
                "Employment Type *",
                ["salaried", "self-employed", "contract", "unemployed"],
                index=["salaried", "self-employed", "contract", "unemployed"].index(default_vals["employment_type"]),
            )
            location = st.text_input("Location *", value=default_vals["location"], placeholder="e.g., Mumbai, Maharashtra")

        with col2:
            st.markdown("#### 💰 Loan Details")
            credit_score = st.number_input("Credit Score *", min_value=300, max_value=850, value=default_vals["credit_score"])
            loan_amount = st.number_input("Loan Amount (₹ INR) *", min_value=10000.0, value=default_vals["loan_amount"], step=50000.0, format="%.2f")
            loan_tenure_months = st.slider("Loan Tenure (Months) *", min_value=6, max_value=360, value=default_vals["loan_tenure_months"], step=6)
            existing_liabilities = st.number_input("Existing Monthly Liabilities (₹ INR)", min_value=0.0, value=default_vals["existing_liabilities"], step=1000.0, format="%.2f")

            st.markdown("#### 📊 Quick Metrics")
            monthly_income = income / 12
            estimated_payment = (loan_amount / loan_tenure_months) * 1.1
            dti_preview = ((existing_liabilities + estimated_payment) / monthly_income) * 100 if monthly_income > 0 else 0
            loan_to_income = loan_amount / income if income > 0 else 0

            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Est. Monthly EMI", f"₹{estimated_payment:,.0f}")
                st.metric("Loan-to-Income Ratio", f"{loan_to_income:.1f}x")
            with metric_col2:
                st.metric("Est. DTI Ratio", f"{dti_preview:.1f}%")
                st.metric("Credit Tier", "Good" if credit_score >= 670 else "Fair" if credit_score >= 580 else "Poor")

        st.markdown("---")
        submit_btn = st.form_submit_button("🚀 Submit for AI Analysis", use_container_width=True, type="primary")

    if submit_btn:
        if not applicant_id.strip():
            st.error("❌ Applicant ID is required.")
        elif not location.strip():
            st.error("❌ Location is required.")
        else:
            payload = {
                "applicant_id": applicant_id.strip(),
                "age": age,
                "income": income,
                "employment_type": employment_type,
                "credit_score": credit_score,
                "loan_amount": loan_amount,
                "loan_tenure_months": loan_tenure_months,
                "existing_liabilities": existing_liabilities,
                "location": location.strip(),
                "application_timestamp": datetime.utcnow().isoformat(),
            }

            st.session_state.chat_history.append({
                "role": "user",
                "content": f"Submitted loan application for {applicant_id} — ₹{loan_amount:,.0f} over {loan_tenure_months} months.",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })

            with st.spinner("🤖 Multi-Agent AI Processing..."):
                progress_bar = st.progress(0, text="Initializing orchestrator...")

                progress_bar.progress(10, text="📡 Connecting to LangGraph orchestrator...")

                try:
                    with httpx.Client(timeout=300) as client:
                        progress_bar.progress(20, text="👤 Agent 1/4: Applicant Profile Agent (MCP: ApplicantDB)...")
                        response = client.post(f"{FASTAPI_URL}/api/loan/process", json=payload)

                    if response.status_code == 200:
                        progress_bar.progress(60, text="📊 Agent 2/4: Financial Risk Analysis (MCP: RiskRulesDB)...")
                        progress_bar.progress(75, text="⚖️ Agent 3/4: Loan Decision Synthesis (MCP: DecisionSynthesis)...")
                        progress_bar.progress(90, text="✅ Agent 4/4: Compliance & Notification (MCP: NotificationSystem)...")
                        progress_bar.progress(100, text="✅ Processing complete!")

                        result = response.json()
                        st.session_state.last_result = result

                        classification = result.get("loan_decision", {}).get("classification", "Unknown")
                        case_id = result.get("compliance", {}).get("case_id", "N/A")
                        confidence = result.get("loan_decision", {}).get("confidence_level", 0)

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"✅ Analysis complete! Decision: **{classification}** | Case ID: `{case_id}` | Confidence: {confidence * 100:.0f}%. View full results in the Analysis Results tab.",
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                        })

                        if classification == "Approved":
                            st.success(f"✅ **LOAN APPROVED** — Case ID: {case_id}")
                        elif classification == "Rejected":
                            st.error(f"❌ **LOAN REJECTED** — Case ID: {case_id}")
                        else:
                            st.warning(f"⚠️ **REQUIRES MANUAL REVIEW** — Case ID: {case_id}")

                        st.info("📊 See the **Analysis Results** tab for the full AI breakdown.")

                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"❌ Processing failed: {error_detail}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"❌ Processing failed: {error_detail}",
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                        })

                except httpx.ConnectError:
                    st.error("❌ Cannot connect to FastAPI server. Start it with: `python main.py` or `python -m uvicorn main:app --port 8000`")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

with tab2:
    if st.session_state.last_result:
        result = st.session_state.last_result
        applicant_id_display = result.get("applicant_id", "N/A")
        loan_decision = result.get("loan_decision", {})
        applicant_profile = result.get("applicant_profile", {})
        financial_risk = result.get("financial_risk", {})
        compliance = result.get("compliance", {})

        classification = loan_decision.get("classification", "Unknown")
        risk_score = loan_decision.get("risk_score", 0)
        confidence = loan_decision.get("confidence_level", 0)

        st.markdown(f"### Decision for Applicant: `{applicant_id_display}`")

        dec_col1, dec_col2, dec_col3, dec_col4 = st.columns(4)
        with dec_col1:
            badge_class = "approved-badge" if classification == "Approved" else "rejected-badge" if classification == "Rejected" else "review-badge"
            icon = "✅" if classification == "Approved" else "❌" if classification == "Rejected" else "⚠️"
            st.markdown(f'<div class="{badge_class}">{icon} {classification}</div>', unsafe_allow_html=True)
        with dec_col2:
            st.metric("Risk Score", f"{risk_score:.1f}/100")
        with dec_col3:
            st.metric("Confidence", f"{confidence * 100:.0f}%")
        with dec_col4:
            st.metric("Case ID", compliance.get("case_id", "N/A"))

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 👤 Agent 1: Applicant Profile Analysis")
            if applicant_profile:
                st.markdown(f'<div class="agent-card">', unsafe_allow_html=True)
                st.markdown(f"**MCP Server:** ApplicantDB")
                st.markdown(f"**Income Stability Score:** {applicant_profile.get('income_stability_score', 'N/A')}/100")
                stability = applicant_profile.get('income_stability_score', 50)
                st.progress(int(stability) / 100)
                st.markdown(f"**Employment Risk:** {applicant_profile.get('employment_risk', 'N/A').upper()}")
                st.markdown(f"**Credit History:** {applicant_profile.get('credit_history_summary', 'N/A')}")
                flags = applicant_profile.get('application_completeness_flags', [])
                if flags:
                    st.markdown("**Completeness Flags:**")
                    for flag in flags:
                        if flag.startswith("ERROR"):
                            st.error(f"  {flag}")
                        elif flag.startswith("WARNING"):
                            st.warning(f"  {flag}")
                        else:
                            st.success(f"  ✅ {flag}")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("#### 📊 Agent 2: Financial Risk Analysis")
            if financial_risk:
                st.markdown(f'<div class="agent-card">', unsafe_allow_html=True)
                st.markdown(f"**MCP Server:** RiskRulesDB")
                dti = financial_risk.get('debt_to_income_ratio', 0)
                st.markdown(f"**Debt-to-Income Ratio:** {dti:.1f}%")
                dti_color = "green" if dti < 36 else "orange" if dti < 50 else "red"
                st.progress(min(dti / 100, 1.0))
                st.markdown(f"**Credit Score Risk:** {financial_risk.get('credit_score_risk_level', 'N/A').upper()}")
                st.markdown(f"**Loan Amount Risk:** {financial_risk.get('loan_amount_risk', 'N/A').upper()}")
                if financial_risk.get('anomaly_detected'):
                    st.warning(f"⚠️ **Anomaly Detected:** {financial_risk.get('anomaly_details', 'Unknown anomaly')}")
                else:
                    st.success("✅ No anomalies detected")
                st.markdown(f"**Reasoning:** {financial_risk.get('reasoning', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown("#### ⚖️ Agent 3: Loan Decision Synthesis")
            if loan_decision:
                st.markdown(f'<div class="agent-card">', unsafe_allow_html=True)
                st.markdown(f"**MCP Server:** DecisionSynthesis")
                st.markdown(f"**Final Classification:** **{classification}**")
                st.markdown(f"**Risk Score:** {risk_score:.1f}/100")
                st.progress(risk_score / 100)
                st.markdown(f"**Confidence Level:** {confidence * 100:.0f}%")
                factors = loan_decision.get('key_decision_factors', [])
                if factors:
                    st.markdown("**Key Decision Factors:**")
                    for i, factor in enumerate(factors, 1):
                        st.markdown(f"  {i}. {factor}")
                st.markdown("**AI Explanation:**")
                st.info(loan_decision.get('explanation', 'N/A'))
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("#### ✅ Agent 4: Compliance & Action Orchestrator")
            if compliance:
                st.markdown(f'<div class="agent-card">', unsafe_allow_html=True)
                st.markdown(f"**MCP Server:** NotificationSystem")
                st.markdown(f"**Action Taken:** {compliance.get('action_taken', 'N/A')}")
                notif_sent = compliance.get('notification_sent', False)
                if notif_sent:
                    st.success("✅ Notification sent to applicant")
                else:
                    st.warning("⚠️ Notification pending")
                st.markdown(f"**Case ID:** `{compliance.get('case_id', 'N/A')}`")
                st.markdown(f"**Timestamp:** {compliance.get('timestamp', 'N/A')}")
                st.markdown(f"**Summary:** {compliance.get('summary', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📋 Processing Log")
        processing_log = result.get("processing_log", [])
        with st.expander(f"View Processing Log ({len(processing_log)} entries)", expanded=False):
            for i, log_entry in enumerate(processing_log, 1):
                st.markdown(f"`{i}.` {log_entry}")

        st.markdown("---")
        st.markdown("#### 📄 Raw JSON Response")
        with st.expander("View Raw API Response", expanded=False):
            st.json(result)

    else:
        st.info("📝 Submit a loan application in the **Submit Application** tab to see the AI analysis results here.")

        st.markdown("### 🔄 System Workflow")
        st.markdown("""
        ```
        User Submits Application (Streamlit UI)
                    ↓
        FastAPI Microservice (Validation)
                    ↓
        LangGraph Orchestration Engine
                    ↓
        ┌─────────────────────────────────────┐
        │  Agent 1: Applicant Profile Agent   │
        │  MCP Server: ApplicantDB            │
        │  → Income Stability, Employment Risk│
        └─────────────────────────────────────┘
                    ↓
        ┌─────────────────────────────────────┐
        │  Agent 2: Financial Risk Agent      │
        │  MCP Server: RiskRulesDB            │
        │  → DTI, Credit Risk, Anomalies      │
        └─────────────────────────────────────┘
                    ↓
        ┌─────────────────────────────────────┐
        │  Agent 3: Loan Decision Agent       │
        │  MCP Server: DecisionSynthesis      │
        │  → Approve / Reject / Review        │
        └─────────────────────────────────────┘
                    ↓
        ┌─────────────────────────────────────┐
        │  Agent 4: Compliance Orchestrator   │
        │  MCP Server: NotificationSystem     │
        │  → Notifications, Audit Logging     │
        └─────────────────────────────────────┘
                    ↓
        Final Decision → Streamlit UI
        ```
        """)

with tab3:
    st.markdown("### 💬 Chat History")
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")
            if role == "user":
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 8px 0;">
                    <div style="background: #0f3460; color: white; padding: 10px 15px; border-radius: 15px 15px 0 15px; max-width: 70%;">
                        <small style="opacity: 0.7;">You • {timestamp}</small><br>
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin: 8px 0;">
                    <div style="background: #f1f3f4; color: #333; padding: 10px 15px; border-radius: 15px 15px 15px 0; max-width: 70%;">
                        <small style="opacity: 0.7;">🤖 AI Loan System • {timestamp}</small><br>
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.info("No chat history yet. Submit a loan application to start.")
