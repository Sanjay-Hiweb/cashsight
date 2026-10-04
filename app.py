"""CashSight — Main Application Entry Point.

Coordinates top-level Streamlit flow between Onboarding and the Dashboard.
Follows docs/ARCHITECTURE.md section 5.1 and docs/PRD.md.
Core business logic remains strictly isolated in core/ and storage/.
"""

import streamlit as st
from config import PRODUCT_NAME, PRODUCT_TAGLINE
from storage.db import db
from ui.onboarding import render_onboarding
from ui.dashboard import render_dashboard

# Streamlit Page Setup
st.set_page_config(
    page_title=f"{PRODUCT_NAME} — Cash-Flow Forecasting",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # Initialize session state for active user
    if "user_id" not in st.session_state:
        # Check if an existing demo/default user is in local database
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users ORDER BY created_at DESC LIMIT 1;")
        row = cursor.fetchone()
        if row:
            st.session_state["user_id"] = row["id"]
        else:
            st.session_state["user_id"] = None

    def handle_onboarding_complete(new_user_id: str):
        st.session_state["user_id"] = new_user_id
        st.rerun()

    def handle_logout():
        st.session_state["user_id"] = None
        st.rerun()

    # Flow routing
    if not st.session_state["user_id"]:
        render_onboarding(on_complete=handle_onboarding_complete)
    else:
        render_dashboard(user_id=st.session_state["user_id"], on_logout=handle_logout)


if __name__ == "__main__":
    main()
