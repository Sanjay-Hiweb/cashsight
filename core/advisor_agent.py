"""CashSight Cash-Flow Advisor Agent Module.

Provides an intelligent, interactive conversational agent that analyzes
cash-balance forecasts, impending crunch risks, and transaction patterns to answer
user questions, explain financial outlooks, and recommend concrete actions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import re
import pandas as pd

from config import (
    DEFAULT_SAFETY_CUSHION,
    TRANSACTION_TYPE_OUTFLOW,
    TRANSACTION_TYPE_INFLOW,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from core.risk_engine import RiskEvaluation, CrunchResult


@dataclass
class AgentResponse:
    """Structured response returned by the CashFlowAdvisorAgent."""
    response_text: str
    intent: str
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    suggested_followups: List[str] = field(default_factory=list)


def format_inr(amount: float) -> str:
    """Formats numeric amounts into Indian Rupee format."""
    return f"₹{amount:,.0f}"


class CashFlowAdvisorAgent:
    """Intelligent advisory agent for MSME cash-flow management.

    Evaluates active forecast projections, risk crunches, and transactions
    to generate grounded, plain-language guidance for shop owners.
    """

    def __init__(
        self,
        forecast_df: Optional[pd.DataFrame] = None,
        risk_evaluation: Optional[RiskEvaluation] = None,
        transactions: Optional[pd.DataFrame] = None,
        current_balance: float = 45000.0,
        safety_cushion: float = DEFAULT_SAFETY_CUSHION,
        business_name: str = "Your Shop",
        owner_name: str = "Shop Owner",
        language: str = "en",
    ):
        self.forecast_df = forecast_df
        self.risk_evaluation = risk_evaluation
        self.transactions = transactions
        self.current_balance = current_balance
        self.safety_cushion = safety_cushion
        self.business_name = business_name
        self.owner_name = owner_name
        self.language = language

    def ask(self, query: str) -> AgentResponse:
        """Processes a natural language query and produces an evidence-grounded response."""
        cleaned_query = (query or "").strip().lower()
        if not cleaned_query:
            return self._handle_greeting()

        intent = self._classify_intent(cleaned_query)

        if intent == "GREETING":
            return self._handle_greeting()
        elif intent == "CRUNCH_CHECK":
            return self._handle_crunch_check()
        elif intent == "SHORTFALL_ANALYSIS":
            return self._handle_shortfall_analysis()
        elif intent == "ACTION_RECOMMENDATION":
            return self._handle_action_recommendation()
        elif intent == "EXPENSE_ANALYSIS":
            return self._handle_expense_analysis()
        elif intent == "WHATIF_SUGGESTION":
            return self._handle_whatif_suggestion()
        elif intent == "SAFETY_CUSHION_QUERY":
            return self._handle_cushion_query()
        elif intent == "GENERAL_SUMMARY":
            return self._handle_summary()
        else:
            return self._handle_unknown(cleaned_query)

    def _classify_intent(self, text: str) -> str:
        """Determines the primary financial intent of the user's inquiry."""
        # Greetings
        if re.search(r"\b(hi|hello|hey|namaste|vanakkam|good morning|who are you|help)\b", text):
            if len(text.split()) <= 4:
                return "GREETING"

        # What-If queries
        if re.search(r"\b(what-if|what if|delay|postpone|simulate|reschedule|push payment)\b", text):
            return "WHATIF_SUGGESTION"

        # Actions / Recommendations
        if re.search(r"\b(what should i do|what can i do|suggest|recommend|action|advice|how to avoid|fix|prevent)\b", text):
            return "ACTION_RECOMMENDATION"

        # Shortfall / Numbers
        if re.search(r"\b(shortfall|deficit|how much|amount|numbers|minimum balance|dip below|gap)\b", text):
            return "SHORTFALL_ANALYSIS"

        # Crunch / Shortage Timing
        if re.search(r"\b(crunch|shortage|run short|short of cash|when|safe|out of cash|run out|out of money|trouble|risk)\b", text):
            return "CRUNCH_CHECK"

        # Expenses / Outflows
        if re.search(r"\b(expense|expenses|cost|spending|outflow|supplier|rent|bills|pay)\b", text):
            return "EXPENSE_ANALYSIS"

        # Safety cushion
        if re.search(r"\b(safety cushion|cushion|reserve|buffer)\b", text):
            return "SAFETY_CUSHION_QUERY"

        # Summary / Overview
        if re.search(r"\b(summary|overview|briefing|outlook|status|report|how is|performance|health)\b", text):
            return "GENERAL_SUMMARY"

        return "UNKNOWN"

    def _get_top_outflows(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Extracts the largest recent/upcoming outflow payments."""
        if self.transactions is None or self.transactions.empty:
            return []
        outflows = self.transactions[self.transactions["type"] == TRANSACTION_TYPE_OUTFLOW].copy()
        if outflows.empty:
            return []
        sorted_outflows = outflows.sort_values(by="amount", ascending=False).head(limit)
        results = []
        for _, row in sorted_outflows.iterrows():
            results.append({
                "date": str(row.get("date", "")),
                "description": str(row.get("description", "Unknown")),
                "amount": float(row.get("amount", 0.0)),
                "category": str(row.get("category", "other")),
            })
        return results

    def _handle_greeting(self) -> AgentResponse:
        """Generates friendly onboarding greeting with contextual quick tips."""
        has_crunch = self.risk_evaluation.has_crunch if self.risk_evaluation else False
        status_badge = "⚠️ impending crunch detected" if has_crunch else "🟢 cash flow looks stable"

        greeting_text = (
            f"👋 **Namaste {self.owner_name}!** I am your **CashSight Advisory Agent**.\n\n"
            f"I continuously monitor the 14-day cash outlook for **{self.business_name}**.\n"
            f"- **Current Balance:** {format_inr(self.current_balance)}\n"
            f"- **Safety Cushion:** {format_inr(self.safety_cushion)}\n"
            f"- **Current Status:** {status_badge}\n\n"
            "You can ask me anything about your upcoming cash flow, impending deficits, "
            "or how postponing an invoice can protect your safety cushion."
        )

        return AgentResponse(
            response_text=greeting_text,
            intent="GREETING",
            key_metrics={"current_balance": self.current_balance, "safety_cushion": self.safety_cushion},
            suggested_followups=[
                "⚠️ When will I run short of cash?",
                "💡 What action should I take?",
                "🔍 What are my biggest expenses?",
                "📊 Give me a complete 14-day summary",
            ],
        )

    def _handle_crunch_check(self) -> AgentResponse:
        """Answers questions regarding whether or when a cash crunch will occur."""
        if not self.risk_evaluation:
            return AgentResponse(
                response_text="⚠️ No forecast data is currently available. Please import transaction history to evaluate cash crunch risks.",
                intent="CRUNCH_CHECK",
                suggested_followups=["Load Demo Data"],
            )

        if not self.risk_evaluation.has_crunch:
            min_bal = float(self.forecast_df["projected_balance_lower"].min()) if self.forecast_df is not None and not self.forecast_df.empty else self.current_balance
            buffer_amt = min_bal - self.safety_cushion
            msg = (
                f"✅ **Good news! No cash crunch is projected over the next 14 days.**\n\n"
                f"- Even under conservative estimates, your projected balance stays at or above **{format_inr(min_bal)}**.\n"
                f"- This provides a comfortable **{format_inr(buffer_amt)} safety buffer** above your minimum cushion of {format_inr(self.safety_cushion)}.\n\n"
                "Your working capital is on track. Keep monitoring daily sales and supplier payouts as usual."
            )
            return AgentResponse(
                response_text=msg,
                intent="CRUNCH_CHECK",
                key_metrics={"has_crunch": False, "minimum_conservative_balance": min_bal},
                suggested_followups=[
                    "📊 Give me a 14-day summary",
                    "🔍 What are my largest upcoming expenses?",
                    "🔮 How does the What-If Simulator work?",
                ],
            )

        earliest = self.risk_evaluation.earliest_crunch
        worst = self.risk_evaluation.worst_crunch

        msg = (
            f"🚨 **Attention: Cash shortage projected in {earliest.days_away} days ({earliest.crunch_date}).**\n\n"
            f"- **Earliest Crunch Date:** **{earliest.crunch_date}** (in {earliest.days_away} days)\n"
            f"- **Conservative Balance:** **{format_inr(earliest.conservative_balance)}** (against your {format_inr(self.safety_cushion)} safety cushion)\n"
            f"- **Projected Shortfall:** **{format_inr(earliest.shortfall)}** below cushion\n"
        )

        if worst and worst.crunch_date != earliest.crunch_date:
            msg += (
                f"- **Deepest Deficit:** On **{worst.crunch_date}** with balance reaching **{format_inr(worst.conservative_balance)}** "
                f"({format_inr(worst.shortfall)} deficit).\n"
            )

        if earliest.is_negative_cash:
            msg += "\n⚠️ **Critical:** Your projected balance may drop below zero (overdraft). Immediate mitigation is recommended."

        return AgentResponse(
            response_text=msg,
            intent="CRUNCH_CHECK",
            key_metrics={
                "has_crunch": True,
                "days_away": earliest.days_away,
                "crunch_date": earliest.crunch_date,
                "shortfall": earliest.shortfall,
                "is_negative": earliest.is_negative_cash,
            },
            suggested_followups=[
                "💡 What practical actions should I take?",
                "🔍 What are my biggest expenses?",
                "🔮 Which payment should I delay?",
            ],
        )

    def _handle_shortfall_analysis(self) -> AgentResponse:
        """Detailed analysis of the cash deficit amount and trajectory."""
        if not self.risk_evaluation or not self.risk_evaluation.has_crunch:
            return AgentResponse(
                response_text=f"🟢 You currently have **zero projected shortfall**. Your cash is expected to remain above your {format_inr(self.safety_cushion)} cushion.",
                intent="SHORTFALL_ANALYSIS",
                key_metrics={"shortfall": 0.0},
                suggested_followups=["📊 Give me a 14-day summary", "🔍 Inspect my top expenses"],
            )

        earliest = self.risk_evaluation.earliest_crunch
        worst = self.risk_evaluation.worst_crunch or earliest

        msg = (
            f"📉 **Cash Shortfall Breakdown:**\n\n"
            f"1. **Initial Dip ({earliest.crunch_date}):** Shortfall of **{format_inr(earliest.shortfall)}** below your safety cushion.\n"
            f"2. **Peak Deficit ({worst.crunch_date}):** Shortfall of **{format_inr(worst.shortfall)}** (conservative balance: {format_inr(worst.conservative_balance)}).\n"
            f"3. **Capital Needed to Stay Safe:** You need approximately **{format_inr(worst.shortfall)}** in additional inflows or deferred outflows to keep your cushion intact."
        )

        return AgentResponse(
            response_text=msg,
            intent="SHORTFALL_ANALYSIS",
            key_metrics={"initial_shortfall": earliest.shortfall, "peak_shortfall": worst.shortfall},
            suggested_followups=[
                "💡 What action should I take to bridge this gap?",
                "🔮 Which payment should I delay?",
            ],
        )

    def _handle_action_recommendation(self) -> AgentResponse:
        """Generates pragmatic, prioritized actions tailored to MSME retail reality."""
        top_outflows = self._get_top_outflows(limit=3)

        if not self.risk_evaluation or not self.risk_evaluation.has_crunch:
            msg = (
                "👍 **Recommended Proactive Practices:**\n\n"
                "1. **Maintain Safety Buffer:** Keep maintaining your safety cushion at ₹25,000+ to weather supplier price volatility.\n"
                "2. **Customer Receivables:** Follow up promptly on customer credit (khata) balances.\n"
                "3. **Regular Sync:** Refresh your bank CSV or AA statement weekly to maintain high forecast precision."
            )
            return AgentResponse(
                response_text=msg,
                intent="ACTION_RECOMMENDATION",
                suggested_followups=["📊 Give me a 14-day summary"],
            )

        earliest = self.risk_evaluation.earliest_crunch
        action_text = (
            f"🛡️ **Action Plan to Bridge the {format_inr(earliest.shortfall)} Shortfall:**\n\n"
            f"1. **Postpone an Outflow:**\n"
        )

        if top_outflows:
            top = top_outflows[0]
            action_text += (
                f"   - Delay your **{top['description']}** payment ({format_inr(top['amount'])}) by **5 to 7 days**.\n"
                f"   - This single postponement can completely prevent your balance from dipping below the cushion.\n"
            )
        else:
            action_text += "   - Postpone your largest upcoming supplier payment by 5 to 7 days.\n"

        action_text += (
            "2. **Accelerate Collections:**\n"
            "   - Follow up on outstanding customer credit or store dues due this week.\n"
            "3. **Run What-If Simulation:**\n"
            "   - Use the **What-If Simulator** below on the dashboard to test how delaying specific bills stabilizes your curve."
        )

        return AgentResponse(
            response_text=action_text,
            intent="ACTION_RECOMMENDATION",
            suggested_followups=[
                "🔮 Which payment should I delay?",
                "🔍 What are my biggest expenses?",
                "⚠️ When is the crunch happening?",
            ],
        )

    def _handle_expense_analysis(self) -> AgentResponse:
        """Identifies top expenses and category breakdown."""
        top_outflows = self._get_top_outflows(limit=5)
        if not top_outflows:
            return AgentResponse(
                response_text="ℹ️ No expense records found in your transaction history.",
                intent="EXPENSE_ANALYSIS",
            )

        msg = "📋 **Your Largest Expense Outflows:**\n\n"
        for i, item in enumerate(top_outflows, start=1):
            msg += f"{i}. **{item['description']}** — **{format_inr(item['amount'])}** ({item['category'].title()})\n"

        msg += "\n💡 **Tip:** Delaying or splitting the #1 supplier invoice is usually the most painless way to solve a temporary cash crunch."

        return AgentResponse(
            response_text=msg,
            intent="EXPENSE_ANALYSIS",
            suggested_followups=[
                "🔮 What happens if I delay the largest payment?",
                "💡 What other actions can I take?",
            ],
        )

    def _handle_whatif_suggestion(self) -> AgentResponse:
        """Explains how to use the What-If payment delay simulator."""
        top_outflows = self._get_top_outflows(limit=1)
        example_str = f"such as '{top_outflows[0]['description']}'" if top_outflows else "such as a supplier payment"

        msg = (
            "🔮 **How the What-If Simulator Helps You:**\n\n"
            f"The What-If Simulator lets you select any upcoming outgoing payment ({example_str}) "
            "and simulate what happens if you pay it **3, 7, or 14 days later**.\n\n"
            "**Key benefits:**\n"
            "- Recalculates your entire 14-day cash curve in real-time.\n"
            "- Shows if postponing that single bill eliminates your cash crunch.\n"
            "- Leaves your actual transaction database untouched.\n\n"
            "👉 Scroll down to the **🔮 What-If Simulator** on your dashboard, pick an invoice, choose delay days, and click **Run Simulation**!"
        )

        return AgentResponse(
            response_text=msg,
            intent="WHATIF_SUGGESTION",
            suggested_followups=[
                "🔍 What are my biggest expenses?",
                "⚠️ When will I run short of cash?",
            ],
        )

    def _handle_cushion_query(self) -> AgentResponse:
        """Explains the user's safety cushion setting."""
        msg = (
            f"🛡️ **Your Safety Cushion:** **{format_inr(self.safety_cushion)}**\n\n"
            "CashSight triggers warning alerts whenever your conservative projected balance falls below this line.\n"
            "You can adjust your safety cushion anytime using the slider in the left sidebar."
        )
        return AgentResponse(
            response_text=msg,
            intent="SAFETY_CUSHION_QUERY",
            key_metrics={"safety_cushion": self.safety_cushion},
            suggested_followups=[
                "⚠️ Am I currently projected to fall below my cushion?",
                "📊 Give me a 14-day summary",
            ],
        )

    def _handle_summary(self) -> AgentResponse:
        """Provides an executive briefing of the 14-day cash outlook."""
        if not self.risk_evaluation or self.forecast_df is None or self.forecast_df.empty:
            return AgentResponse(
                response_text="ℹ️ Incomplete forecast data. Please ensure transaction data is loaded.",
                intent="GENERAL_SUMMARY",
            )

        end_balance = float(self.forecast_df["projected_balance"].iloc[-1])
        min_balance = float(self.forecast_df["projected_balance_lower"].min())
        delta = end_balance - self.current_balance
        trend_str = "📈 upward" if delta >= 0 else "📉 downward"

        status_line = (
            f"🚨 **Cash Crunch Alert:** Projected shortfall of {format_inr(self.risk_evaluation.earliest_crunch.shortfall)} on {self.risk_evaluation.earliest_crunch.crunch_date}"
            if self.risk_evaluation.has_crunch
            else "🟢 **Stable Outlook:** Projected to stay above safety cushion throughout the 14-day window"
        )

        msg = (
            f"📊 **14-Day Cash Flow Briefing for {self.business_name}:**\n\n"
            f"- **Current Balance:** {format_inr(self.current_balance)}\n"
            f"- **Expected Ending Balance:** {format_inr(end_balance)} ({trend_str} by {format_inr(abs(delta))})\n"
            f"- **Conservative Minimum:** {format_inr(min_balance)}\n"
            f"- **Configured Safety Cushion:** {format_inr(self.safety_cushion)}\n"
            f"- **Risk Status:** {status_line}\n"
        )

        return AgentResponse(
            response_text=msg,
            intent="GENERAL_SUMMARY",
            key_metrics={
                "current_balance": self.current_balance,
                "end_balance": end_balance,
                "min_conservative_balance": min_balance,
            },
            suggested_followups=[
                "💡 What should I do?",
                "🔍 What are my biggest expenses?",
                "🔮 How can What-If delay help?",
            ],
        )

    def _handle_unknown(self, query: str) -> AgentResponse:
        """Fallback for unrecognized queries, offering grounded guidance."""
        msg = (
            f"🤖 I heard your question: *'{query}'*.\n\n"
            f"As your CashSight Advisor for **{self.business_name}**, I specialize in:\n"
            "- Calculating whether and when you will run short of cash.\n"
            "- Quantifying your cash crunch shortfall in Indian Rupees (₹).\n"
            "- Identifying top expenses and recommending which payment to postpone.\n"
            "- Evaluating What-If scenarios.\n\n"
            "Try one of the quick options below:"
        )

        return AgentResponse(
            response_text=msg,
            intent="UNKNOWN",
            suggested_followups=[
                "⚠️ When will I run short of cash?",
                "💡 What should I do to stay safe?",
                "🔍 What are my biggest expenses?",
                "📊 Give me a complete 14-day summary",
            ],
        )
