"""Unit tests for CashFlowAdvisorAgent."""

import pytest
import pandas as pd
from core.advisor_agent import CashFlowAdvisorAgent, AgentResponse
from core.risk_engine import (
    RiskEvaluation,
    CrunchResult,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)


@pytest.fixture
def sample_transactions():
    return pd.DataFrame([
        {"date": "2026-10-01", "description": "Daily Store Sales", "amount": 8000.0, "type": "inflow", "category": "sales"},
        {"date": "2026-10-02", "description": "Wholesale Grains Supplier", "amount": 25000.0, "type": "outflow", "category": "supplier"},
        {"date": "2026-10-03", "description": "Shop Monthly Rent", "amount": 12000.0, "type": "outflow", "category": "rent"},
        {"date": "2026-10-04", "description": "Electricity Bill", "amount": 3500.0, "type": "outflow", "category": "utilities"},
    ])


@pytest.fixture
def crunch_risk_evaluation():
    earliest = CrunchResult(
        crunch_date="2026-10-08",
        days_away=5,
        projected_balance=26000.0,
        conservative_balance=18000.0,
        safety_cushion=25000.0,
        shortfall=7000.0,
        is_negative_cash=False,
        severity=SEVERITY_HIGH,
        title="Cash Shortfall in 5 Days",
        message="Conservative balance drops below safety cushion.",
        suggested_action="Delay supplier payment by 5 days.",
    )
    worst = CrunchResult(
        crunch_date="2026-10-12",
        days_away=9,
        projected_balance=20000.0,
        conservative_balance=12000.0,
        safety_cushion=25000.0,
        shortfall=13000.0,
        is_negative_cash=False,
        severity=SEVERITY_HIGH,
        title="Peak Cash Shortfall in 9 Days",
        message="Conservative balance drops to ₹12,000.",
        suggested_action="Delay supplier payment.",
    )
    return RiskEvaluation(
        has_crunch=True,
        crunches=[earliest, worst],
        earliest_crunch=earliest,
        worst_crunch=worst,
        overall_severity=SEVERITY_HIGH,
        headline="Shortfall Risk in 5 Days",
        summary_message="Conservative balance drops below cushion.",
        recommended_action="Postpone supplier payment.",
    )


@pytest.fixture
def sample_forecast_df():
    dates = [f"2026-10-{i:02d}" for i in range(1, 15)]
    return pd.DataFrame({
        "ds": dates,
        "projected_balance": [45000.0 - i * 1500 for i in range(14)],
        "projected_balance_lower": [40000.0 - i * 2000 for i in range(14)],
        "projected_balance_upper": [50000.0 - i * 1000 for i in range(14)],
    })


def test_agent_greeting():
    agent = CashFlowAdvisorAgent(owner_name="Ramesh", business_name="Patel Kirana")
    res = agent.ask("Hello")
    assert res.intent == "GREETING"
    assert "Namaste Ramesh" in res.response_text
    assert "Patel Kirana" in res.response_text
    assert len(res.suggested_followups) > 0


def test_agent_crunch_check_with_shortfall(sample_forecast_df, crunch_risk_evaluation, sample_transactions):
    agent = CashFlowAdvisorAgent(
        forecast_df=sample_forecast_df,
        risk_evaluation=crunch_risk_evaluation,
        transactions=sample_transactions,
        current_balance=45000.0,
        safety_cushion=25000.0,
    )
    res = agent.ask("When will I run short of cash?")
    assert res.intent == "CRUNCH_CHECK"
    assert "2026-10-08" in res.response_text
    assert "5 days" in res.response_text
    assert res.key_metrics["has_crunch"] is True
    assert res.key_metrics["shortfall"] == 7000.0


def test_agent_shortfall_analysis(sample_forecast_df, crunch_risk_evaluation, sample_transactions):
    agent = CashFlowAdvisorAgent(
        forecast_df=sample_forecast_df,
        risk_evaluation=crunch_risk_evaluation,
        transactions=sample_transactions,
    )
    res = agent.ask("How much is my cash shortfall?")
    assert res.intent == "SHORTFALL_ANALYSIS"
    assert "₹7,000" in res.response_text
    assert "₹13,000" in res.response_text


def test_agent_action_recommendations(sample_forecast_df, crunch_risk_evaluation, sample_transactions):
    agent = CashFlowAdvisorAgent(
        forecast_df=sample_forecast_df,
        risk_evaluation=crunch_risk_evaluation,
        transactions=sample_transactions,
    )
    res = agent.ask("What should I do to stay safe?")
    assert res.intent == "ACTION_RECOMMENDATION"
    assert "Wholesale Grains Supplier" in res.response_text
    assert "5 to 7 days" in res.response_text


def test_agent_expense_analysis(sample_transactions):
    agent = CashFlowAdvisorAgent(transactions=sample_transactions)
    res = agent.ask("What are my biggest expenses?")
    assert res.intent == "EXPENSE_ANALYSIS"
    assert "Wholesale Grains Supplier" in res.response_text
    assert "₹25,000" in res.response_text
    assert "Shop Monthly Rent" in res.response_text


def test_agent_whatif_guidance(sample_transactions):
    agent = CashFlowAdvisorAgent(transactions=sample_transactions)
    res = agent.ask("How does the What-If simulation work?")
    assert res.intent == "WHATIF_SUGGESTION"
    assert "What-If Simulator" in res.response_text


def test_agent_healthy_cash_flow():
    safe_risk = RiskEvaluation(
        has_crunch=False,
        headline="Cash Balance Safe",
        summary_message="Balance remains healthy.",
    )
    safe_forecast = pd.DataFrame({
        "ds": [f"2026-10-{i:02d}" for i in range(1, 15)],
        "projected_balance": [60000.0 + i * 1000 for i in range(14)],
        "projected_balance_lower": [50000.0 + i * 800 for i in range(14)],
        "projected_balance_upper": [70000.0 + i * 1200 for i in range(14)],
    })
    agent = CashFlowAdvisorAgent(
        forecast_df=safe_forecast,
        risk_evaluation=safe_risk,
        current_balance=60000.0,
        safety_cushion=25000.0,
    )
    res = agent.ask("Will I run out of money?")
    assert res.intent == "CRUNCH_CHECK"
    assert "Good news! No cash crunch is projected" in res.response_text
    assert res.key_metrics["has_crunch"] is False


def test_agent_unknown_fallback():
    agent = CashFlowAdvisorAgent()
    res = agent.ask("Tell me a random joke")
    assert res.intent == "UNKNOWN"
    assert "CashSight Advisor" in res.response_text
    assert len(res.suggested_followups) > 0
