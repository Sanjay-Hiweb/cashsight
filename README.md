# CashSight — README

**Purpose:** Introduce CashSight, explain its MVP scope and technology stack, and guide developers and AI coding agents through project setup and execution.

**Last updated:** October 2, 2026

## 1. Project Summary

CashSight is a subscription-based SaaS product designed to help small Indian shop owners forecast their cash flow and anticipate potential cash shortages approximately 14 days in advance.

The product aims to help shop owners understand their future cash position, identify potential shortfalls, and take practical action before payments become difficult.

**Core promise:** Know two weeks ahead if you may run short of cash, and understand what action you could take.

### Key principles

- Keep financial information understandable to non-technical users.
- Use consent-based, read-only financial data ingestion.
- Make uncertainty in forecasts visible.
- Provide a suggested action with every cash-shortage warning.
- Keep business logic independent of the user interface.
- Prefer free and open-source tools where practical.
- Never expand the MVP beyond the approved scope without founder approval.

## 2. Target Users

The primary users are owners of small retail and trading businesses in tier-2 and tier-3 Indian cities.

Typical businesses include hardware shops, clothing stores, kirana stores, and wholesalers.

The intended user may operate with 1–10 employees, use a smartphone and UPI, prefer WhatsApp, and have limited financial or technical knowledge.

The product must use calm, reassuring language and clearly explain how financial data is handled.

## 3. MVP Scope

### 3.1 Required features

The MVP must include:

1. **Onboarding:** Collect name, phone number, business name, business type, and preferred language.
2. **Financial data ingestion:** Support both CSV/statement upload and an Account Aggregator sandbox integration. Both must feed a common internal transaction schema.
3. **Transaction processing:** Clean and categorize transactions as rent, supplier, salary, sales, utilities, or other.
4. **Cash-flow forecasting:** Produce a 14-day projected daily cash balance with an uncertainty range.
5. **Cash-crunch detection:** Compare the conservative forecast against the user's configured safety cushion.
6. **Warnings:** Display the potential shortfall amount, date, severity, and a suggested action in plain language.
7. **Dashboard:** Display current balance, forecast chart, and warning card.
8. **What-If simulator:** Allow the user to delay a specific payment by a specified number of days and inspect the resulting forecast.
9. **Consent and privacy:** Explain data use and consent in simple language.
10. **Subscription structure:** Define a 30-day free trial followed by a paid subscription. Billing integration may be stubbed in the MVP.

### 3.2 Explicitly out of scope for the MVP

Do not implement the following as MVP features:

- Weekly voice-note summaries.
- WhatsApp delivery of alerts.
- Phone OTP login.
- A real payment gateway.
- A separate mobile frontend or PWA.
- Receivables tracking.
- Trade-association benchmarks.
- GST payment reminders.
- Invoice integration.
- Multi-shop support.
- Money transfers, payments, lending, or bank credential storage.
- LLM-based forecasting.
- Cryptocurrency, investments, or personal budgeting.
- Any other feature not explicitly listed in the MVP scope.

Future-phase items may be documented in planning files, but must not be implemented during MVP tasks unless the founder explicitly approves a scope change.

## 4. Technology Stack

The following stack is specified by the project brief.

| Layer | Technology | Intended use |
|---|---|---|
| Programming language | Python 3.10+ | Application and business logic |
| MVP UI | Streamlit | User interface and dashboard |
| Data processing | pandas | Transaction cleaning and date-based processing |
| Primary forecasting | Prophet | Forecasting with weekly seasonality enabled and yearly seasonality disabled |
| Forecast fallback | statsmodels exponential smoothing | Alternative forecasting implementation |
| Development database | SQLite | Local persistence |
| Planned production database | PostgreSQL | Future production deployment |
| Financial data | Account Aggregator sandbox and CSV upload | Transaction ingestion |
| Charts | Plotly or Streamlit native charts | Forecast visualization |
| Version control | Git and GitHub | Source control and change history |
| MVP hosting | Streamlit Community Cloud or an equivalent free tier | Initial deployment |
| Coding agent | Google Antigravity | Code generation and implementation |

Voice-related tools, including `deep-translator` and `gTTS`, are reserved for Phase 2.

### Technology constraints

- Core business logic must not depend on Streamlit.
- Both forecasting implementations must expose the same function signature.
- The forecasting implementation must not use an LLM.
- No paid service, paid API, or API key may be introduced without founder approval.
- Hosting compatibility and dependency versions must be tested rather than assumed.
- Production Account Aggregator access requirements remain `TO VERIFY`.

## 5. Project Structure

The intended repository layout is:

```text
cashsight/
├── README.md
├── app.py
├── config.py
├── requirements.txt
├── data/
│   ├── sample_data/       # Sample data files, if required
│   ├── generator.py       # Sample-data generation, if required
│   └── data_loader.py
├── core/
│   ├── forecasting.py
│   ├── risk_engine.py
│   ├── backtesting.py
│   ├── whatif_simulator.py
│   └── advisor_agent.py
├── aggregator/
│   ├── setu_sandbox.py
│   └── csv_import.py
├── storage/
│   └── db.py
├── voice/
│   ├── translator.py
│   └── tts_generator.py
├── ui/
│   ├── onboarding.py
│   └── dashboard.py
└── docs/
    ├── PRD.md
    ├── ARCHITECTURE.md
    ├── ROADMAP.md
    ├── TODO.md
    ├── DESIGN.md
    ├── RULES.md
    └── SECURITY.md
```

**Structure rules:**

- `README.md` stays in the repository root.
- The seven remaining planning documents belong in `docs/`.
- Business logic belongs in `core/`.
- Streamlit calls belong only in `app.py` and `ui/`.
- Data ingestion belongs in `aggregator/`.
- Database access belongs in `storage/`.
- Voice modules are reserved for Phase 2 and must not be implemented as part of the MVP.
- Supporting files and tests may be added only when required by the approved architecture and TODO tasks.
- The structure describes the intended organization; it does not authorize implementing every module immediately.

## 6. Data Model Overview

The initial data model includes the following entities.

| Entity | Fields |
|---|---|
| Transaction | date, description, category, type, amount in INR |
| User | id, name, phone, business_name, business_type, language, safety_cushion |
| Consent | user_id, provider, data_period, granted_at, revoked_at |
| Forecast row | ds, yhat, yhat_lower, yhat_upper, projected_balance |
| Crunch result | crunch_date, days_away, shortfall, severity |

Transaction amounts are stored as positive values. The `type` field distinguishes inflows from outflows.

The detailed database schema, relationships, validation rules, and function contracts will be defined in `docs/ARCHITECTURE.md`.

## 7. Forecasting Requirements

The forecasting system must:

- Use approximately six months of daily net cash-flow history when available.
- Forecast 14 days into the future.
- Produce projected daily balances beginning from the current cash balance.
- Provide an uncertainty range.
- Use the conservative lower estimate when evaluating potential cash shortages.
- Support a statsmodels fallback with the same function signature as the primary forecasting implementation.
- Be backtested before its results are treated as reliable.

The acceptable accuracy thresholds, minimum usable history, current-balance source, and treatment of false alarms and missed warnings remain `TO VERIFY`.

Forecasts must communicate uncertainty and must not present uncertain projections as guaranteed outcomes.

## 8. Privacy and Financial Data

CashSight must follow these baseline requirements:

- Financial data access must be read-only and consent-based.
- Bank login credentials must never be stored.
- Only the approved user, business, consent, and transaction data may be stored.
- Users must have a way to revoke consent and request data deletion.
- Stored data must be encrypted.
- The consent and privacy screen must use simple language.

The exact security controls, encryption design, access-control approach, data lifecycle, and applicable legal obligations will be specified in `docs/SECURITY.md`.

The exact obligations under India's Digital Personal Data Protection Act, 2023, and production Account Aggregator requirements are `TO VERIFY`.

## 9. Development Setup

### Prerequisites

- Python 3.10 or later.
- Git.
- A GitHub account for version control.
- Google Antigravity for AI-assisted implementation.

Additional provider accounts are required only when working on the relevant integration tasks.

### Environment setup

1. Obtain the project repository.
2. Create and activate a Python virtual environment.
3. Install dependencies listed in `requirements.txt`.
4. Follow the setup and execution instructions maintained in this README as the implementation becomes available.
5. Run the application and tests after each completed implementation task.

Example virtual-environment commands:

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies after `requirements.txt` has been created:

```bash
python -m pip install -r requirements.txt
```

### Running the application

Once the application entry point and dependencies are implemented:

```bash
streamlit run app.py
```

These commands describe the intended workflow. Successful installation, dependency compatibility, and application startup must be verified in the actual development environment.

## 10. Version Control Workflow

Use Git and GitHub to track implementation progress.

- Commit after each working implementation step.
- Keep each change limited to its assigned TODO task.
- Test changes before considering a task complete.
- Do not combine unrelated tasks into one implementation.
- Report errors and failed tests instead of hiding or bypassing them.
- Do not overwrite existing work without inspecting it first.

The detailed coding constraints will be defined in `docs/RULES.md`.

## 11. AI Coding Agent Instructions

Google Antigravity is responsible for implementing the application according to the approved project documents.

Before implementing code, the agent must:

1. Read `README.md`.
2. Read `docs/RULES.md` when available.
3. Read `docs/TODO.md` when available.
4. Follow the relevant approved architecture, requirements, design, roadmap, and security documents.
5. Work on one TODO task at a time.
6. Modify only files required by the current task.
7. Run the relevant tests and report their results.
8. Stop and request clarification when a requirement conflicts with an approved document or cannot be implemented without an unapproved assumption.

The agent must not:

- Add unapproved features.
- Invent provider APIs, legal requirements, or external service behavior.
- Introduce paid services or API keys without approval.
- Implement production financial-data access before its requirements have been verified.
- Treat sample data or unvalidated forecasts as proof of real-world accuracy.
- Begin unrelated future-phase work.

## 12. Founder Responsibilities

The founder is responsible for:

- Approving the product scope and planning documents.
- Creating required external accounts.
- Copying approved documents into the project repository.
- Running and testing the application after implementation steps.
- Reporting actual errors and observed behavior.
- Interviewing 5–10 shop owners to validate the problem and pricing.
- Verifying legal and regulatory items marked `TO VERIFY`.
- Approving any proposed changes to the scope or technology stack.

Technical decisions should be documented clearly so the founder can approve or reject them without needing to implement the code personally.

## 13. Business Model

The initial business model is a hypothesis, not a validated commercial result.

| Item | Proposed model |
|---|---|
| Trial | 30 days free |
| Monthly pricing hypothesis | ₹199–₹499 |
| Annual pricing hypothesis | ₹1,999–₹3,999 |
| Initial distribution hypothesis | Trade associations and supplier networks |
| Validation | Interviews with 5–10 shop owners |

Willingness to pay, final pricing, subscription enforcement, and the appropriate acquisition strategy remain `TO VERIFY`.

## 14. Suggestions (not in scope)

The following are process recommendations, not new product features:

- Validate the cash-shortage problem with shop owners before investing heavily in integrations.
- Test forecasting with representative sample data before using real financial data.
- Maintain a clear distinction between demonstrated forecast performance and unverified assumptions.
- Require explicit approval before changing the scope or introducing a paid dependency.

These recommendations do not authorize additional MVP functionality.

## 15. Open Questions / TO VERIFY

| Question | Why it matters |
|---|---|
| What is the source of the current cash balance? | Required to calculate projected daily balances accurately. |
| Which Account Aggregator sandbox will be implemented first? | Determines the initial integration path. |
| What are the production Account Aggregator access requirements? | Required before production financial-data integration. |
| What are the applicable DPDP Act obligations? | Required to finalize compliance controls. |
| What forecast accuracy is acceptable? | Required to evaluate forecasting performance. |
| What minimum transaction history is sufficient? | Required to handle new or incomplete datasets. |
| What encryption and access-control implementation will be used? | Required to protect stored financial information. |
| What are the hosting limits and dependency constraints? | Required to verify deployment feasibility. |
| Will shop owners pay the proposed subscription prices? | Required to validate the business model. |
| Is a mobile frontend needed earlier than Phase 2? | Requires validation with target users. |

**Document status:** Draft — awaiting founder approval.

This README establishes the project overview and working constraints. Detailed requirements, architecture, implementation tasks, UX rules, coding rules, and security controls will be defined in their respective documents.
