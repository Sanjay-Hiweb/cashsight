# CashSight — ROADMAP.md

**Purpose:** Define the implementation phases, milestones, dependencies, and key risks for CashSight without adding features beyond the approved product scope.

**Last updated:** 2026-10-02

## Summary

- [FROM BRIEF] Build the MVP first: CSV and Account Aggregator sandbox ingestion, a shared transaction schema, a 14-day cash forecast, cash-crunch warnings, dashboard, and payment-delay What-If simulation.
- [FROM BRIEF] Keep forecasting and risk logic independent of Streamlit UI code.
- [STANDARD PRACTICE] Implement small, testable increments; do not start a dependent milestone until its prerequisites pass.
- [TO VERIFY] Resolve the source of current balance, AA sandbox route, forecast acceptance thresholds, and production privacy/compliance requirements before relying on them.
- [FROM BRIEF] Phase 2 and Phase 3 ideas are not MVP commitments.

## 1. Roadmap Rules

1. [FROM BRIEF] Treat the approved brief, `PRD.md`, and `ARCHITECTURE.md` as the sources of truth. If they conflict, stop and ask Sanjay rather than guessing.
2. [FROM BRIEF] Build one small task at a time from `TODO.md`; test it before moving on.
3. [STANDARD PRACTICE] Keep each milestone demonstrable and record its test result.
4. [FROM BRIEF] Do not add unapproved paid services, API keys, or out-of-scope features.
5. [FROM BRIEF] Label unresolved decisions `[TO VERIFY]`; do not represent assumptions as confirmed facts.

## 2. Phase Overview

| Phase | Goal | Included work | Exit condition |
|---|---|---|---|
| 0 — Decisions and setup | Remove blockers and establish the project baseline | Confirm current-balance source and initial AA sandbox route; create repository and documented environment; prepare synthetic sample data | [STANDARD PRACTICE] The project runs locally, and blocking product decisions are recorded |
| 1 — Data foundation | Ingest and normalize transaction data | CSV upload, AA sandbox adapter, shared transaction schema, validation, cleaning, category mapping | [FROM BRIEF] Both ingestion routes produce the same internal transaction format |
| 2 — Forecast and risk | Produce and test the 14-day outlook | Forecasting interface, Prophet implementation, fallback exponential smoothing, projected balance, uncertainty range, safety-cushion checks | [FROM BRIEF] Forecast and warning outputs pass documented tests; accuracy thresholds remain `[TO VERIFY]` |
| 3 — Core user experience | Make the result understandable and actionable | Onboarding, consent/privacy screen, dashboard, warning card, forecast chart, payment-delay What-If simulator | [FROM BRIEF] A test user can complete the main MVP journey using sample data |
| 4 — Persistence and trial structure | Persist MVP records and represent trial status | SQLite development storage, data lifecycle operations, 30-day trial state, billing stub | [FROM BRIEF] Core data can be saved and deleted; no live payment gateway is added |
| 5 — MVP validation and release | Verify the end-to-end experience | Integration tests, forecast backtesting, error-state checks, privacy review, deployment to an approved free-tier host | [STANDARD PRACTICE] A release candidate passes the agreed acceptance checklist and known limitations are documented |
| Phase 2 — Later | Add post-MVP communication and access features | Weekly voice-note summaries in Hindi, Tamil, Telugu, Kannada, and Punjabi; WhatsApp delivery; phone OTP; real payment gateway; mobile-friendly frontend/PWA; receivables tracking | [FROM BRIEF] Start only after a separate scope decision |
| Phase 3 — Future ideas | Consider additional product directions | Anonymous trade-association benchmarks, GST payment reminders, invoice integration, multi-shop support | [FROM BRIEF] Not part of the MVP; requires future validation and approval |

## 3. Detailed Milestones

### M0 — Resolve blockers and prepare the workspace

**Purpose:** Make implementation decisions that affect data flow and testing.

Tasks:
- [FROM BRIEF] Create the Git repository and planned folder structure.
- [FROM BRIEF] Set up Python 3.10+ and a reproducible dependency file.
- [TO VERIFY] Decide how the MVP obtains the current balance. Do not silently assume it can be derived from transaction history.
- [TO VERIFY] Select the first AA sandbox provider and confirm available sandbox access and documentation.
- [TO VERIFY] Define the CSV input columns and date/amount conventions.
- [TO VERIFY] Record the first forecast backtesting dataset and evaluation method.

**Exit checks:**
- [STANDARD PRACTICE] A clean environment can install dependencies and launch a minimal Streamlit app.
- [STANDARD PRACTICE] Blocking decisions and their owners are recorded.
- [FROM BRIEF] No production bank-data access or paid integration is assumed.

### M1 — Transaction ingestion and common schema

**Purpose:** Make both data sources usable by the same business logic.

Tasks:
- [FROM BRIEF] Define and validate the common transaction model.
- [FROM BRIEF] Implement CSV upload and validation.
- [FROM BRIEF] Implement the selected AA sandbox adapter as a separate module.
- [FROM BRIEF] Normalize both sources to the same transaction schema.
- [FROM BRIEF] Clean and categorize transactions into rent, supplier, salary, sales, utilities, and other.
- [STANDARD PRACTICE] Handle malformed rows, missing values, duplicate records, invalid dates, and unsupported formats without crashing the whole app.
- [STANDARD PRACTICE] Use synthetic or approved sandbox data for repeatable tests.

**Exit checks:**
- [FROM BRIEF] CSV and AA sandbox data reach the same internal schema.
- [STANDARD PRACTICE] Tests cover valid input and representative invalid input.
- [TO VERIFY] Any provider-specific limitations are documented rather than hidden.

### M2 — Forecasting and cash-crunch detection

**Purpose:** Produce the 14-day projected balance and flag possible shortages.

Tasks:
- [FROM BRIEF] Define a stable forecasting function contract independent of Streamlit.
- [FROM BRIEF] Implement Prophet with weekly seasonality and yearly seasonality disabled.
- [FROM BRIEF] Implement the statsmodels exponential-smoothing fallback with the same function signature.
- [FROM BRIEF] Generate a 14-day forecast with an uncertainty range.
- [FROM BRIEF] Convert forecast outputs into projected daily balances using the confirmed current-balance approach.
- [FROM BRIEF] Compare the conservative forecast estimate against the user's safety cushion.
- [FROM BRIEF] Produce warning data containing date, days away, estimated shortfall, severity, and a plain-language suggested action.
- [STANDARD PRACTICE] Test empty, short, irregular, and unsuitable histories; handle model failures clearly.
- [STANDARD PRACTICE] Backtest on held-out historical periods where suitable data exists.

**Exit checks:**
- [FROM BRIEF] The forecast horizon is 14 days.
- [FROM BRIEF] The warning uses the conservative lower estimate as specified in the brief.
- [TO VERIFY] Sanjay approves measurable forecast-accuracy and warning-quality thresholds before treating the model as validated.
- [TO VERIFY] The meaning of forecast fields and interval propagation is settled and consistent.

### M3 — Onboarding and core dashboard

**Purpose:** Let a shop owner understand the forecast and its implications.

Tasks:
- [FROM BRIEF] Collect name, phone number, business name, business type, and preferred language.
- [FROM BRIEF] Show a consent/privacy screen in simple language.
- [FROM BRIEF] Display current balance, forecast chart, and warning card.
- [FROM BRIEF] Show warning amount, date, severity, and suggested action.
- [FROM BRIEF] Add the What-If simulator for delaying a specific payment by N days.
- [STANDARD PRACTICE] Include loading, empty-data, invalid-input, and failure states.
- [STANDARD PRACTICE] Keep labels and actions understandable to a non-financially technical user.

**Exit checks:**
- [STANDARD PRACTICE] A tester can move from onboarding to a populated dashboard using sample data.
- [FROM BRIEF] The What-If simulation changes the forecast without moving money or initiating a payment.
- [STANDARD PRACTICE] A simulation does not mutate the original transaction records.

### M4 — Storage and trial-state stub

**Purpose:** Persist the minimum data required by the MVP.

Tasks:
- [FROM BRIEF] Use SQLite for development storage.
- [FROM BRIEF] Store user details, consent records, transaction data, and forecast-related records only as needed by the approved data model.
- [FROM BRIEF] Support consent revocation and user data deletion.
- [FROM BRIEF] Represent the 30-day free-trial and paid status in the product flow.
- [FROM BRIEF] Stub billing; do not integrate a live payment gateway in the MVP.
- [TO VERIFY] Confirm a practical encryption approach and storage boundaries before using real personal or financial data.

**Exit checks:**
- [STANDARD PRACTICE] Data persists across app restarts in the development environment.
- [STANDARD PRACTICE] Deletion behavior is tested and documented.
- [FROM BRIEF] No bank login credentials are stored.
- [FROM BRIEF] No live payment processing is present.

### M5 — End-to-end validation and MVP release candidate

**Purpose:** Verify that the pieces work together and that limitations are visible.

Tasks:
- [STANDARD PRACTICE] Run unit tests for ingestion, normalization, forecasting, risk detection, and What-If logic.
- [STANDARD PRACTICE] Run integration tests for CSV-to-dashboard and AA-sandbox-to-dashboard flows.
- [STANDARD PRACTICE] Test invalid uploads, unavailable provider responses, forecast failures, and empty histories.
- [FROM BRIEF] Backtest forecast behavior and document results and limitations.
- [FROM BRIEF] Verify consent revocation and deletion paths.
- [TO VERIFY] Review the applicable DPDP Act 2023 obligations and production AA requirements with appropriate authoritative sources or qualified advice.
- [STANDARD PRACTICE] Deploy only to a suitable approved host and use non-sensitive test data until production safeguards are verified.
- [STANDARD PRACTICE] Run a small usability check with shop owners; the brief calls for 5–10 interviews to validate pricing and product assumptions.

**Exit checks:**
- [STANDARD PRACTICE] The MVP acceptance checklist derived from `PRD.md` passes.
- [STANDARD PRACTICE] Known defects, unsupported cases, and forecast limitations are recorded.
- [TO VERIFY] Release readiness is not declared until privacy, data handling, forecast thresholds, and AA access questions have owners and documented decisions.

## 4. Dependencies and Critical Path

| Dependency | Needed before | Why it matters |
|---|---|---|
| Current-balance source `[TO VERIFY]` | M2 | A projected balance cannot be calculated reliably without a defined starting balance |
| Common transaction schema | M1 completion / M2 | CSV and AA data must feed the same forecasting logic |
| AA sandbox route `[TO VERIFY]` | AA ingestion work | Provider access and sandbox behavior cannot be assumed |
| CSV schema and validation rules `[TO VERIFY]` | CSV ingestion | Import behavior must be testable and predictable |
| Forecast output semantics | M2 | Forecasted net flow and projected balance must not be confused |
| Safety-cushion and severity rules `[TO VERIFY]` | M2/M3 | Warnings must be consistent and interpretable |
| Encryption and deletion design `[TO VERIFY]` | M4 / release review | Real transaction data should not be used before safeguards are established |
| Forecast acceptance thresholds `[TO VERIFY]` | M5 | “Accurate enough” must be measurable, not assumed |

**Critical path:** M0 decisions → M1 common transaction data → M2 forecast/risk engine → M3 dashboard/What-If → M4 persistence/trial stub → M5 validation.

[STANDARD PRACTICE] Some UI scaffolding and synthetic-data work may proceed in parallel, but integration should follow the dependency order above.

## 5. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Unclear current-balance source | Forecasted balances may be misleading | [TO VERIFY] Resolve before finalizing balance calculations |
| AA sandbox access or provider behavior differs from expectations | Integration delay | [STANDARD PRACTICE] Isolate provider code behind an adapter; validate sandbox access early |
| CSV data is inconsistent | Incorrect categories or forecasts | [STANDARD PRACTICE] Validate inputs and show actionable import errors |
| Limited or noisy transaction history | Weak forecast quality | [FROM BRIEF] Use approximately six months of history where available; [STANDARD PRACTICE] disclose limitations and backtest |
| False alarms or missed cash crunches | Loss of trust or missed action | [FROM BRIEF] Use conservative estimates; [TO VERIFY] define evaluation thresholds and warning behavior |
| Financial data exposure | User harm and trust loss | [FROM BRIEF] Do not store bank credentials; support consent revocation and deletion; [TO VERIFY] verify encryption and compliance requirements |
| MVP scope expands | Delayed validation | [FROM BRIEF] Keep Phase 2/3 items out of MVP unless Sanjay explicitly approves a scope change |
| Model or dependency failure | Forecast unavailable | [FROM BRIEF] Keep the fallback model interface consistent; [STANDARD PRACTICE] surface failures instead of fabricating a forecast |
| Users do not trust or pay for the product | Weak adoption | [FROM BRIEF] Conduct 5–10 shop-owner interviews and validate willingness to pay |

## 6. Founder Validation Milestones

These are validation activities, not additional product features.

- [FROM BRIEF] Interview 5–10 small shop owners about cash-flow planning, trust, and willingness to pay.
- [TO VERIFY] Ask which current-balance entry/source they would trust and use.
- [TO VERIFY] Validate whether a 14-day forecast and safety-cushion warning are understandable and useful.
- [TO VERIFY] Validate the proposed ₹199–₹499/month and ₹1,999–₹3,999/year price hypotheses; do not treat them as confirmed prices.
- [STANDARD PRACTICE] Record interview evidence and update assumptions before making scope or pricing decisions.

## 7. Suggestions (not in scope)

- [STANDARD PRACTICE] Keep a lightweight decision log for unresolved questions and approved changes.
- [STANDARD PRACTICE] Add a release checklist that confirms test status, known limitations, and data-safety checks.
- [FROM BRIEF] Do not implement Phase 2 or Phase 3 ideas as part of the MVP without explicit approval.

## 8. Open Questions / TO VERIFY

1. What is the approved source of the starting/current cash balance?
2. Which AA sandbox provider—Setu or Finvu—will be used first, and what access is available?
3. What CSV columns, date formats, and amount conventions will be accepted?
4. What exact rules define warning severity and suggested actions?
5. Which forecast metrics and acceptance thresholds will determine whether results are usable?
6. How will forecast uncertainty be propagated into projected balance?
7. What encryption method and data-access controls are appropriate for the selected deployment?
8. What exact DPDP Act 2023 obligations and production AA requirements apply to the planned service?
9. Is Streamlit acceptable for initial user validation, or is a mobile-friendly frontend needed earlier?
10. Which hosting option will be approved after data-safety requirements are reviewed?
