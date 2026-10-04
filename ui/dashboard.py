"""CashSight Main Dashboard UI Module.

Renders:
- Current balance & trial status summary
- 14-Day cash-balance forecast chart with uncertainty bands (Plotly)
- Cash-crunch warning card with practical suggested action
- What-If payment delay simulator
- Multi-source data ingestion (CSV upload, Setu AA sandbox, demo synthetic data)
- Privacy controls (consent revocation & Right to Erasure data deletion)
"""

from typing import Dict, Any, Optional, List, Tuple
import datetime
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from config import (
    DEFAULT_SAFETY_CUSHION,
    FORECAST_HORIZON_DAYS,
    TRANSACTION_TYPE_OUTFLOW,
    TRANSACTION_TYPE_INFLOW,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from storage.db import db
from aggregator.csv_import import parse_and_validate_csv, generate_sample_csv_template
from aggregator.setu_sandbox import SetuSandboxAdapter
from data.generate_sample_data import generate_retail_shop_data
from data.data_loader import aggregate_daily_net_cash_flow, inspect_transaction_dataset
from core.forecasting import forecast_cash_balance, ForecastResult, InsufficientHistoryError
from core.risk_engine import detect_cash_crunches, RiskEvaluation
from core.whatif_simulator import simulate_payment_delay, WhatIfComparison
from core.advisor_agent import CashFlowAdvisorAgent


def format_inr(val: float) -> str:
    """Formats numeric values into Indian Rupee format."""
    return f"₹{val:,.0f}"


def build_forecast_plot(
    forecast_df: pd.DataFrame,
    safety_cushion: float,
    current_balance: float,
    simulated_df: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """Generates an interactive Plotly chart with baseline and conservative uncertainty bounds."""
    fig = go.Figure()

    dates = forecast_df["ds"].tolist()
    proj = forecast_df["projected_balance"].tolist()
    lower = forecast_df["projected_balance_lower"].tolist()
    upper = forecast_df["projected_balance_upper"].tolist()

    # 1. Uncertainty band (Upper bound)
    fig.add_trace(go.Scatter(
        x=dates,
        y=upper,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="Upper Estimate",
        hoverinfo="skip",
    ))

    # 2. Uncertainty band (Lower bound filled to upper)
    fig.add_trace(go.Scatter(
        x=dates,
        y=lower,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(59, 130, 246, 0.15)",
        name="Uncertainty Range",
        hoverinfo="skip",
    ))

    # 3. Conservative Lower Bound
    fig.add_trace(go.Scatter(
        x=dates,
        y=lower,
        mode="lines+markers",
        line=dict(color="#DC2626", width=2, dash="dot"),
        marker=dict(size=4),
        name="Conservative Estimate (Used for Warnings)",
        hovertemplate="<b>%{x}</b><br>Conservative Balance: ₹%{y:,.0f}<extra></extra>",
    ))

    # 4. Baseline Expected Balance
    fig.add_trace(go.Scatter(
        x=dates,
        y=proj,
        mode="lines+markers",
        line=dict(color="#2563EB", width=3),
        marker=dict(size=6),
        name="Expected Projected Balance",
        hovertemplate="<b>%{x}</b><br>Expected Balance: ₹%{y:,.0f}<extra></extra>",
    ))

    # 5. Optional Simulated Curve from What-If
    if simulated_df is not None and not simulated_df.empty:
        sim_dates = simulated_df["ds"].tolist()
        sim_proj = simulated_df["projected_balance"].tolist()
        fig.add_trace(go.Scatter(
            x=sim_dates,
            y=sim_proj,
            mode="lines+markers",
            line=dict(color="#10B981", width=3, dash="dash"),
            marker=dict(size=6),
            name="What-If Delayed Payment Scenario",
            hovertemplate="<b>%{x}</b><br>Simulated Balance: ₹%{y:,.0f}<extra></extra>",
        ))

    # 6. Safety Cushion Reference Line
    fig.add_hline(
        y=safety_cushion,
        line_dash="dash",
        line_color="#E11D48",
        line_width=2,
        annotation_text=f"Safety Cushion: ₹{safety_cushion:,.0f}",
        annotation_position="top left",
        annotation_font_color="#E11D48",
    )

    # Zero Balance Reference Line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="#475569",
        line_width=1,
    )

    fig.update_layout(
        title="14-Day Cash Balance Outlook (INR)",
        xaxis_title="Date",
        yaxis_title="Projected Balance (₹)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=450,
    )
    return fig


def render_dashboard(user_id: str, on_logout: Any) -> None:
    """Renders the comprehensive CashSight main dashboard."""
    user = db.get_user(user_id)
    if not user:
        st.error("User session not found. Please restart onboarding.")
        if st.button("Back to Onboarding"):
            on_logout()
        return

    trial_info = db.get_trial_status(user_id)

    # Header section
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title(f"📊 {user['business_name']}")
        st.caption(f"Shop Owner: {user['name']} | Category: {user['business_type']} | Phone: {user['phone']}")
    with col_h2:
        st.markdown(
            f"""
            <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 10px; text-align: center;">
                <span style="color: #1E40AF; font-size: 0.85rem; font-weight: 600;">{trial_info.get('plan_type', 'Trial')}</span><br>
                <span style="color: #4B5563; font-size: 0.8rem;">{trial_info.get('days_remaining', 30)} days left</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Load transactions for user
    df_txns = db.get_transactions(user_id)

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Settings & Controls")
        current_bal = st.number_input(
            "Verified Current Balance (₹)",
            value=float(user.get("current_balance", 45000.0)),
            step=1000.0,
            help="Update your verified starting cash balance on hand + bank account.",
        )
        if current_bal != float(user.get("current_balance", 0.0)):
            db.update_user_balance(user_id, current_bal)
            user["current_balance"] = current_bal

        safety_cushion = st.number_input(
            "Safety Cushion Threshold (₹)",
            value=float(user.get("safety_cushion", DEFAULT_SAFETY_CUSHION)),
            step=1000.0,
            help="Minimum reserve threshold for cash shortage alerts.",
        )
        if safety_cushion != float(user.get("safety_cushion", DEFAULT_SAFETY_CUSHION)):
            db.update_safety_cushion(user_id, safety_cushion)
            user["safety_cushion"] = safety_cushion

        forecast_engine = st.selectbox(
            "Forecasting Method",
            ["prophet", "statsmodels"],
            index=0,
            help="Choose primary Prophet engine or statsmodels Holt-Winters fallback.",
        )

        st.markdown("---")
        st.caption("🔒 Financial Data Privacy")
        if st.button("Revoke AA Consent", use_container_width=True):
            db.revoke_consent(user_id)
            st.warning("Consent revoked. No further external data synchronization will take place.")

        if st.button("🗑️ Delete All My Data", type="secondary", use_container_width=True):
            del_res = db.delete_user_data(user_id)
            st.success("All personal and financial records permanently erased.")
            on_logout()
            st.rerun()

    # Empty State: If no transactions yet
    if df_txns.empty:
        st.info("👋 Welcome! You have not uploaded any transactions yet. Get started below:")
        render_ingestion_tabs(user_id, current_bal)
        return

    # Aggregate cash flow and generate forecast
    daily_df = aggregate_daily_net_cash_flow(df_txns)

    try:
        forecast_result = forecast_cash_balance(
            historical_net_cash_flow=daily_df,
            current_balance=current_bal,
            horizon_days=FORECAST_HORIZON_DAYS,
            method=forecast_engine,
        )
        risk_evaluation = detect_cash_crunches(forecast_result, safety_cushion=safety_cushion)
    except InsufficientHistoryError as e:
        st.warning(f"⚠️ {str(e)}")
        st.info("Please import at least 14 days of transactions to generate forecasts.")
        render_ingestion_tabs(user_id, current_bal)
        return
    except Exception as e:
        st.error(f"Error computing forecast: {str(e)}")
        return

    # Top KPI Metrics Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Current Balance", format_inr(current_bal))
    with kpi2:
        end_proj = float(forecast_result.forecast_df["projected_balance"].iloc[-1])
        delta_val = end_proj - current_bal
        st.metric("14-Day Expected Balance", format_inr(end_proj), delta=format_inr(delta_val))
    with kpi3:
        st.metric("Safety Cushion", format_inr(safety_cushion))
    with kpi4:
        if risk_evaluation.has_crunch:
            if risk_evaluation.overall_severity == SEVERITY_CRITICAL:
                st.error("🚨 Critical Shortage")
            elif risk_evaluation.overall_severity == SEVERITY_HIGH:
                st.warning("⚠️ High Deficit Risk")
            else:
                st.warning("🟡 Dip Below Cushion")
        else:
            st.success("🟢 Cash Healthy")

    # Cash-Crunch Warning Card
    if risk_evaluation.has_crunch:
        worst = risk_evaluation.worst_crunch
        earliest = risk_evaluation.earliest_crunch

        st.markdown(
            f"""
            <div style="background-color: #FEF2F2; border-left: 6px solid #DC2626; border-radius: 6px; padding: 1.2rem; margin-top: 1rem; margin-bottom: 1.5rem;">
                <h3 style="color: #991B1B; margin-top: 0;">⚠️ {risk_evaluation.headline}</h3>
                <p style="color: #7F1D1D; font-size: 1.05rem; line-height: 1.5;">
                    {risk_evaluation.summary_message}
                </p>
                <div style="background-color: #FFFFFF; border: 1px solid #FECACA; border-radius: 6px; padding: 0.8rem; margin-top: 0.8rem;">
                    <strong style="color: #B91C1C;">💡 Practical Suggested Action:</strong><br>
                    <span style="color: #374151;">{risk_evaluation.recommended_action}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: #ECFDF5; border-left: 6px solid #059669; border-radius: 6px; padding: 1rem; margin-top: 1rem; margin-bottom: 1.5rem;">
                <h4 style="color: #065F46; margin: 0;">✅ {risk_evaluation.headline}</h4>
                <p style="color: #047857; margin-bottom: 0;">{risk_evaluation.summary_message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Model & History info notes
    if forecast_result.warning_notes:
        with st.expander("ℹ️ Forecast Notes & Data Quality"):
            for note in forecast_result.warning_notes:
                st.caption(f"• {note}")
            st.caption(f"Engine active: **{forecast_result.method_used}** | History: **{forecast_result.history_days} days**")

    # Interactive Forecast Plot
    fig = build_forecast_plot(
        forecast_df=forecast_result.forecast_df,
        safety_cushion=safety_cushion,
        current_balance=current_bal,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Interactive Cash Flow Advisor Agent (Demo)
    render_advisor_agent(
        user=user,
        forecast_result=forecast_result,
        risk_evaluation=risk_evaluation,
        df_txns=df_txns,
        current_bal=current_bal,
        safety_cushion=safety_cushion,
    )

    st.markdown("---")

    # What-If Payment Delay Simulator
    st.subheader("🔮 What-If Simulator: Delay a Payment")
    st.caption("See what happens to your cash forecast if an upcoming supplier payment or expense is delayed by a few days.")

    # Filter out recent or upcoming outflow transactions
    outflows = df_txns[df_txns["type"] == TRANSACTION_TYPE_OUTFLOW].copy()
    if not outflows.empty:
        outflow_options = {}
        for idx, row in outflows.tail(15).iterrows():
            lbl = f"{row['date']} — {row['description']} ({format_inr(row['amount'])}) [{row['category']}]"
            outflow_options[lbl] = idx

        sim_col1, sim_col2, sim_col3 = st.columns([3, 2, 1])
        with sim_col1:
            selected_label = st.selectbox("Select Outgoing Payment to Delay:", list(outflow_options.keys()))
            selected_idx = outflow_options[selected_label]
        with sim_col2:
            delay_days = st.slider("Postpone Payment By (Days):", min_value=1, max_value=21, value=7)
        with sim_col3:
            st.write("")
            st.write("")
            run_sim = st.button("Run Simulation", type="primary", use_container_width=True)

        if run_sim:
            try:
                sim_comparison = simulate_payment_delay(
                    transactions=df_txns,
                    payment_index=selected_idx,
                    delay_days=delay_days,
                    current_balance=current_bal,
                    safety_cushion=safety_cushion,
                    method=forecast_engine,
                )

                st.markdown(
                    f"""
                    <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                        <h4 style="color: #166534; margin-top: 0;">Simulation Result: Payment Postponed to {sim_comparison.simulated_date}</h4>
                        <p style="color: #15803D; font-size: 1.05rem;">{sim_comparison.plain_language_summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Show updated chart comparing baseline vs simulation
                sim_fig = build_forecast_plot(
                    forecast_df=forecast_result.forecast_df,
                    safety_cushion=safety_cushion,
                    current_balance=current_bal,
                    simulated_df=sim_comparison.simulated_forecast.forecast_df,
                )
                st.plotly_chart(sim_fig, use_container_width=True)

            except Exception as e:
                st.error(f"Simulation error: {str(e)}")
    else:
        st.info("No outflow payments available to simulate delay.")

    st.markdown("---")

    # Ingestion Tabs for updating or adding data
    st.subheader("📥 Transaction Data Management")
    render_ingestion_tabs(user_id, current_bal)


def render_ingestion_tabs(user_id: str, current_bal: float) -> None:
    """Renders the data ingestion options."""
    tab_csv, tab_aa, tab_demo = st.tabs(["📄 Upload Bank/Shop CSV", "🏦 Setu AA Sandbox", "🧪 Load Demo Data"])

    # Tab 1: CSV Upload
    with tab_csv:
        st.markdown("#### Upload CSV or Bank Statement")
        st.caption("Upload your daily transactions. We automatically categorize Rent, Supplier, Salary, Sales, and Utilities.")

        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

        template_csv = generate_sample_csv_template()
        st.download_button(
            "⬇️ Download Accepted CSV Format Template",
            data=template_csv,
            file_name="cashsight_sample_template.csv",
            mime="text/csv",
        )

        if uploaded_file is not None:
            result = parse_and_validate_csv(uploaded_file, file_size_bytes=uploaded_file.size)
            if not result.is_valid:
                st.error("Validation Failed:")
                for err in result.errors:
                    st.error(f"• {err}")
            else:
                st.success(f"Successfully validated {result.valid_rows} transaction records!")
                if result.warnings:
                    with st.expander("Warnings / Notes"):
                        for w in result.warnings:
                            st.caption(f"• {w}")

                st.dataframe(result.data.head(10), use_container_width=True)

                if st.button("Save Transactions to Dashboard", type="primary"):
                    db.save_transactions(user_id, result.data, source="csv")
                    st.success("Transactions saved! Refreshing dashboard...")
                    st.rerun()

    # Tab 2: Account Aggregator Sandbox
    with tab_aa:
        st.markdown("#### Account Aggregator (Setu Sandbox)")
        st.caption("Read-only consent-based integration with India's RBI-regulated Account Aggregator framework.")

        st.info(
            "🔒 **Consent Guarantee:**\n"
            "- Read-only access to transaction history.\n"
            "- CashSight **never** receives your net-banking password or UPI PIN.\n"
            "- Revocable anytime."
        )

        adapter = SetuSandboxAdapter()

        if st.button("Connect & Request AA Sandbox Consent"):
            consent = adapter.create_consent_request(user_id=user_id, phone_number="9876543210")
            db.record_consent(user_id, provider=adapter.PROVIDER_NAME)
            st.success(f"Consent #{consent.consent_id} approved in Sandbox!")

            ext_res = adapter.fetch_sandbox_transactions(consent.consent_id)
            if ext_res.success and ext_res.data is not None:
                db.save_transactions(user_id, ext_res.data, source="setu_sandbox")
                st.success(f"Fetched {ext_res.total_fetched} transactions from Setu AA Sandbox!")
                st.rerun()
            else:
                st.error(f"Failed to fetch from AA Sandbox: {ext_res.error_message}")

    # Tab 3: Synthetic Demo Data
    with tab_demo:
        st.markdown("#### Load Pre-built Realistic Shop Demo")
        st.caption("Loads 6 months of realistic synthetic data for Shree Ganesh Kirana Store, designed to test cash-crunch warnings.")

        if st.button("🚀 Load Kirana Store Demo Data", type="primary"):
            demo_df = generate_retail_shop_data(
                shop_name="Shree Ganesh Kirana",
                shop_type="Kirana / Grocery",
                history_days=180,
            )
            count = db.save_transactions(user_id, demo_df, source="sample_data")
            db.update_user_balance(user_id, 38000.0)
            st.success(f"Loaded {count} synthetic transactions! Starting balance set to ₹38,000.")
            st.rerun()


def render_advisor_agent(
    user: Dict[str, Any],
    forecast_result: ForecastResult,
    risk_evaluation: RiskEvaluation,
    df_txns: pd.DataFrame,
    current_bal: float,
    safety_cushion: float,
) -> None:
    """Renders the interactive CashSight Advisory Agent panel."""
    st.subheader("🤖 CashSight Advisor Agent (Demo)")
    st.caption("Ask questions about your cash balance, understand impending crunches, and explore actions.")

    agent = CashFlowAdvisorAgent(
        forecast_df=forecast_result.forecast_df,
        risk_evaluation=risk_evaluation,
        transactions=df_txns,
        current_balance=current_bal,
        safety_cushion=safety_cushion,
        business_name=user.get("business_name", "Your Shop"),
        owner_name=user.get("name", "Shop Owner"),
        language=user.get("language", "en"),
    )

    user_id = str(user.get("id", "default"))
    chat_key = f"advisor_chat_{user_id}"

    if chat_key not in st.session_state:
        welcome_res = agent.ask("")
        st.session_state[chat_key] = [
            {"role": "assistant", "content": welcome_res.response_text, "followups": welcome_res.suggested_followups}
        ]

    # Quick prompt chips
    latest_followups = st.session_state[chat_key][-1].get("followups", []) if st.session_state[chat_key] else []
    if not latest_followups:
        latest_followups = [
            "⚠️ When will I run short of cash?",
            "💡 What action should I take?",
            "🔍 What are my biggest expenses?",
            "📊 Give me a complete 14-day summary",
        ]

    st.markdown("**Suggested Quick Questions:**")
    chip_cols = st.columns(min(len(latest_followups), 4))
    selected_chip = None
    for i, col in enumerate(chip_cols):
        if i < len(latest_followups):
            q_text = latest_followups[i]
            if col.button(q_text, key=f"chip_{user_id}_{i}", use_container_width=True):
                selected_chip = q_text

    # Chat history display container
    chat_container = st.container(height=320)
    with chat_container:
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # User chat input or chip trigger
    user_prompt = selected_chip or st.chat_input("Ask your CashSight advisor a question...", key=f"chat_input_{user_id}")

    col_rst1, col_rst2 = st.columns([5, 1])
    with col_rst2:
        if st.button("🔄 Reset Chat", key=f"clear_chat_{user_id}", help="Reset conversation history"):
            welcome_res = agent.ask("")
            st.session_state[chat_key] = [
                {"role": "assistant", "content": welcome_res.response_text, "followups": welcome_res.suggested_followups}
            ]
            st.rerun()

    if user_prompt:
        st.session_state[chat_key].append({"role": "user", "content": user_prompt})
        resp = agent.ask(user_prompt)
        st.session_state[chat_key].append({
            "role": "assistant",
            "content": resp.response_text,
            "followups": resp.suggested_followups,
        })
        st.rerun()

