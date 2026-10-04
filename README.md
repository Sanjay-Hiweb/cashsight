# CashSight

Cash-flow forecasting and liquidity risk alerts for small businesses and retail shops.

CashSight helps retail shop owners, traders, and small business owners anticipate cash flow crunches up to 14 days in advance. By ingesting past bank statements (via Account Aggregator sandbox or CSV upload), CashSight projects daily balances using time-series models and allows business owners to simulate the effect of delaying upcoming supplier payments or expenses.

---

## Features

- **14-Day Balance Forecasting:** Projects daily net cash flow and balance trends using Prophet with a Statsmodels exponential smoothing fallback.
- **Cash-Crunch Early Warnings:** Compares conservative projections against a configurable safety cushion (e.g. ₹25,000) and provides actionable guidance before shortfalls occur.
- **What-If Payment Simulator:** Test the impact of postponing a specific supplier invoice or rent payment by a few days to see if a crunch is averted.
- **Flexible Data Ingestion:** Import bank statements via CSV with auto-categorization (rent, suppliers, salary, utilities, sales) or connect through an Account Aggregator sandbox.
- **Interactive Dashboard:** Built with Streamlit and Plotly for responsive, clear visualization of balance trajectories, uncertainty ranges, and cash breakdown.
- **Privacy & Data Protection:** Consent-based data handling with complete user data deletion (Right to Erasure) support.

---

## Tech Stack

| Component | Technology |
|---|---|
| UI & Dashboard | Streamlit, Plotly |
| Time-Series Forecasting | Meta Prophet, Statsmodels |
| Data Processing | Pandas, NumPy |
| Persistence | SQLite (parameterized queries) |
| Test Suite | Pytest |

---

## Project Structure

```text
cashsight/
├── app.py                      # Main Streamlit application entry point
├── config.py                   # Non-secret application configuration & defaults
├── requirements.txt            # Python dependencies
├── aggregator/
│   ├── csv_import.py           # CSV statement parser, normalizer & categorizer
│   └── setu_sandbox.py         # Account Aggregator sandbox adapter
├── core/
│   ├── forecasting.py          # Prophet and Holt-Winters forecasting engine
│   ├── risk_engine.py          # Shortfall & safety cushion crunch detector
│   ├── whatif_simulator.py     # Outflow postponement simulator
│   ├── backtesting.py          # Historical forecast validation & metrics
│   └── advisor_agent.py        # Conversational guidance & recommendations
├── data/
│   ├── data_loader.py          # Transaction loaders & aggregators
│   └── generate_sample_data.py # Realistic synthetic business sample data generator
├── storage/
│   └── db.py                   # SQLite persistence, user isolation & data deletion
├── tests/                      # Full unit and integration test suite
└── ui/
    ├── onboarding.py           # Shop profile and consent onboarding flow
    └── dashboard.py            # Main analytics dashboard & simulator UI
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- Git

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/Sanjay-Hiweb/cashsight.git
cd cashsight

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application

Launch the Streamlit web dashboard:

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

### 4. Running Tests

Run the test suite with pytest:

```bash
python -m pytest
```

---

## License

This project is licensed under the MIT License.
