"""CashSight User Onboarding UI Module.

Collects user profile, business details, starting cash balance,
and explicit privacy consent.
Follows docs/ARCHITECTURE.md section 5.11, docs/PRD.md FR-001/FR-002, and docs/DESIGN.md.
"""

from typing import Optional, Dict, Any, Callable
import re
import streamlit as st

from config import (
    SUPPORTED_LANGUAGES,
    SUPPORTED_BUSINESS_TYPES,
    DEFAULT_SAFETY_CUSHION,
)
from storage.db import db


def validate_phone(phone: str) -> bool:
    """Validates 10-digit Indian phone number format."""
    cleaned = re.sub(r"[\s\-\+]", "", phone)
    if cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    return bool(re.match(r"^[6-9]\d{9}$", cleaned))


def render_onboarding(on_complete: Callable[[str], None]) -> None:
    """Renders the onboarding form and captures initial setup.

    Args:
        on_complete: Callback invoked with the newly created user_id.
    """
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1E3A8A; font-size: 2.2rem; margin-bottom: 0.2rem;">CashSight</h1>
        <p style="color: #4B5563; font-size: 1.1rem;">
            Know 2 weeks ahead if you will run short of cash, and what to do about it.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("### Step 1: Your Business Profile")
        st.caption("Tell us about your shop so we can personalize your cash-flow alerts.")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Shop Owner Name *", placeholder="e.g. Ramesh Patel")
            phone = st.text_input("Mobile Number (WhatsApp) *", placeholder="e.g. 9876543210")
            lang_options = {l["label"]: l["code"] for l in SUPPORTED_LANGUAGES}
            selected_lang_label = st.selectbox("Preferred Language", list(lang_options.keys()))
            selected_lang_code = lang_options[selected_lang_label]

        with col2:
            business_name = st.text_input("Shop / Business Name *", placeholder="e.g. Patel Kirana & General Store")
            business_type = st.selectbox("Business Type *", SUPPORTED_BUSINESS_TYPES)

        st.markdown("---")
        st.markdown("### Step 2: Cash & Safety Cushion Baseline")
        st.caption("CashSight uses your verified starting balance as the foundation for the 14-day projection.")

        col3, col4 = st.columns(2)
        with col3:
            current_balance = st.number_input(
                "Current Cash & Bank Balance (₹) *",
                min_value=0.0,
                max_value=50000000.0,
                value=45000.0,
                step=1000.0,
                help="Your actual cash on hand plus bank account balance right now.",
            )
        with col4:
            safety_cushion = st.number_input(
                "Minimum Safety Cushion (₹) *",
                min_value=0.0,
                max_value=10000000.0,
                value=DEFAULT_SAFETY_CUSHION,
                step=1000.0,
                help="The minimum reserve balance you want in your account. CashSight alerts you if you are projected to fall below this.",
            )

        st.markdown("---")
        st.markdown("### Step 3: Consent & Privacy Agreement")
        st.info(
            "🔒 **Your Privacy is Protected:**\n"
            "- CashSight is read-only. We **never** ask for, collect, or store your bank passwords or PINs.\n"
            "- Your financial transaction records are used strictly to calculate your 14-day cash outlook.\n"
            "- You can revoke consent and permanently erase all your data at any time with one click.\n"
            "- Includes a **30-Day Free Trial** with no payment or credit card required."
        )

        consent_checked = st.checkbox(
            "I understand and agree to the privacy policy and consent to processing my transaction data for cash-flow forecasting.",
            value=True,
        )

        submit_btn = st.button("Complete Setup & Open Dashboard", type="primary", use_container_width=True)

        if submit_btn:
            errors = []
            if not name.strip():
                errors.append("Please enter your name.")
            if not phone.strip() or not validate_phone(phone):
                errors.append("Please enter a valid 10-digit Indian mobile number (starting with 6, 7, 8, or 9).")
            if not business_name.strip():
                errors.append("Please enter your shop or business name.")
            if not consent_checked:
                errors.append("You must agree to the privacy consent to continue.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                user_id = db.save_user({
                    "name": name.strip(),
                    "phone": phone.strip(),
                    "business_name": business_name.strip(),
                    "business_type": business_type,
                    "language": selected_lang_code,
                    "current_balance": current_balance,
                    "safety_cushion": safety_cushion,
                })
                db.record_consent(user_id=user_id, provider="Initial Onboarding Consent")
                st.success("Setup complete! Loading your cash dashboard...")
                on_complete(user_id)
