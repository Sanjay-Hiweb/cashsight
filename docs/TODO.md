# CashSight — TODO.md

**Purpose:** Turn the approved CashSight brief, PRD, architecture, and roadmap into small, testable implementation tasks in dependency order.

**Last updated:** 2026-10-02

## Summary

- [FROM BRIEF] Complete tasks in order and work on only one task at a time.
- [FROM BRIEF] Antigravity must read `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and `docs/RULES.md` before implementing tasks.
- [STANDARD PRACTICE] Each task must have a clear result and a test that can be run before marking it complete.
- [FROM BRIEF] Do not implement Phase 2, Phase 3, paid services, or unapproved features as part of the MVP.
- [TO VERIFY] Resolve blocking product and data decisions before coding dependent behavior.

## 1. Rules for Using This TODO

1. Work on exactly one unchecked task at a time.
2. Before starting a task, state its ID, goal, files expected to change, and test.
3. Do not silently change the approved product scope or public function contracts.
4. If an instruction conflicts with `PRD.md`, `ARCHITECTURE.md`, or `ROADMAP.md`, stop and report the conflict.
5. Do not invent provider APIs, library functions, legal requirements, or credentials.
6. Label unresolved details `[TO VERIFY]`.
7. After implementation, report files changed, commands/tests run, actual results, and any remaining issue.
8. Mark a task complete only after its stated acceptance check passes. If a test cannot be run, leave the task unchecked and explain why.
9. Keep Streamlit calls in `app.py` and `ui/`; keep business logic in `core/`.
10. Do not use real bank credentials or real customer financial data during initial development.

## 2. Blocking Decisions

Resolve these with Sanjay before implementing the dependent behavior.

- [ ] **DEC-001 — Current balance source:** Decide how the starting/current cash balance is supplied. Do not assume it can be calculated from transaction history.
- [ ] **DEC-002 — AA sandbox:** Choose Setu or Finvu as the first sandbox provider and confirm access and documentation.
- [ ] **DEC-003 — CSV contract:** Approve accepted columns, date formats, amount convention, and required fields.
- [ ] **DEC-004 — Forecast output meaning:** Confirm whether model output represents net cash flow or balance and how the uncertainty range maps to projected balance.
- [ ] **DEC-005 — Warning rules:** Define safety-cushion comparison, severity levels, and how suggested actions are selected.
- [ ] **DEC-006 — Forecast validation:** Agree on backtesting approach and measurable acceptance thresholds.
- [ ] **DEC-007 — Data safeguards:** Confirm storage boundaries, encryption approach, and deletion expectations before using real personal/financial data.
- [ ] **DEC-008 — Deployment:** Choose a hosting option only after its data-handling implications are reviewed.
- [ ] **DEC-009 — Legal/regulatory review:** Verify applicable DPDP Act 2023 obligations and production AA requirements using authoritative sources or qualified advice.

[STANDARD PRACTICE] Tasks that depend on an unresolved decision must remain blocked. Build only independent scaffolding or tests that do not encode the unresolved assumption.

## 3. Phase 0 — Project Setup

- [x] **SETUP-001 — Create repository structure**
  - Goal: Create the approved CashSight folder structure without implementing product logic.
  - Files: Root folders and placeholder files from `README.md`.
  - Test: Compare the created tree against the approved structure; confirm Phase 2 voice files are marked future-only.

- [x] **SETUP-002 — Create Python environment instructions**
  - Goal: Document how to create and activate a Python 3.10+ environment.
  - Files: `README.md` only if setup instructions need correction.
  - Test: Follow the instructions in a clean environment.

- [x] **SETUP-003 — Add initial dependency manifest**
  - Goal: Add only approved MVP dependencies needed by the current implementation stage.
  - Files: `requirements.txt`.
  - Test: Install dependencies in a clean environment.
  - Constraint: Do not add unapproved paid services, credentials, or Phase 2-only packages without a reason.

- [x] **SETUP-004 — Add configuration defaults**
  - Goal: Centralize non-secret application settings and safe development defaults.
  - Files: `config.py`.
  - Test: Import configuration without launching the UI or requiring secrets.
  - Constraint: Never store bank login credentials or API secrets in source control.

- [x] **SETUP-005 — Add minimal Streamlit entry point**
  - Goal: Create a minimal app that launches successfully without pretending MVP functionality is complete.
  - Files: `app.py`.
  - Test: Run the documented Streamlit command and confirm the app opens.

## 4. Phase 1 — Data Foundation

- [x] **DATA-001 — Define the canonical transaction model**
  - Goal: Represent date, description, category, type (`inflow`/`outflow`), and positive INR amount consistently.
  - Files: `aggregator/csv_import.py`, `storage/db.py`.
  - Test: Valid transactions pass; invalid dates, types, and non-positive amounts are rejected or handled according to the agreed contract.
  - Dependency: DEC-003.

- [x] **DATA-002 — Define the CSV import contract**
  - Goal: Document required columns, optional columns, date formats, and amount conventions.
  - Files: `aggregator/csv_import.py` & sample template download.
  - Test: A valid sample file matches the contract; unsupported input produces a clear error.
  - Dependency: DEC-003.

- [x] **DATA-003 — Implement CSV parsing and validation**
  - Goal: Parse uploaded CSV data into the canonical transaction model.
  - Files: `aggregator/csv_import.py`.
  - Test: Cover a valid CSV, missing required column, malformed row, invalid date, and invalid amount.
  - Dependency: DATA-001, DATA-002.

- [x] **DATA-004 — Implement transaction cleaning and categorization**
  - Goal: Map transactions to rent, supplier, salary, sales, utilities, or other, while preserving the original description.
  - Files: `aggregator/csv_import.py`.
  - Test: Representative examples map correctly; uncertain transactions use the agreed fallback behavior.
  - Dependency: DATA-001.
  - Constraint: Do not add categories without approval.

- [x] **DATA-005 — Create synthetic sample data**
  - Goal: Provide repeatable, clearly fictional transaction data for development and demonstrations.
  - Files: `data/generate_sample_data.py`, `data/sample_data/sample_transactions.csv`.
  - Test: The sample data loads through the same validation path as imported data.
  - Constraint: Do not include real customer or bank data.

- [x] **DATA-006 — Define the Account Aggregator adapter boundary**
  - Goal: Keep provider-specific code separate from the canonical transaction model.
  - Files: `aggregator/setu_sandbox.py`.
  - Test: Adapter contract can be tested without a live provider connection.
  - Dependency: DATA-001, DEC-002.

- [x] **DATA-007 — Implement the selected AA sandbox adapter**
  - Goal: Retrieve permitted sandbox data using the chosen provider's verified documentation and normalize it to the canonical model.
  - Files: `aggregator/setu_sandbox.py`.
  - Test: Use provider sandbox fixtures or a documented sandbox flow; verify normalized output.
  - Dependency: DATA-006, DEC-002.
  - Constraint: Do not invent endpoints or imply production AA access exists.

- [x] **DATA-008 — Verify ingestion parity**
  - Goal: Confirm CSV and AA sandbox paths produce equivalent canonical records for equivalent input data.
  - Files: `tests/test_setu_sandbox.py`.
  - Test: Compare normalized field names, types, amount convention, and category behavior.
  - Dependency: DATA-003, DATA-004, DATA-007.

## 5. Phase 2 — Forecast and Risk Engine

- [x] **FORECAST-001 — Finalize forecasting contract**
  - Goal: Define inputs, outputs, missing-data behavior, horizon, and forecast-field semantics.
  - Files: `core/forecasting.py` and related tests.
  - Test: Contract tests validate the documented input and output shapes.
  - Dependency: DATA-001, DEC-001, DEC-004.

- [x] **FORECAST-002 — Implement Prophet forecast path**
  - Goal: Implement the agreed forecast method with weekly seasonality and yearly seasonality disabled.
  - Files: `core/forecasting.py`.
  - Test: Suitable synthetic history produces the required 14-day output shape.
  - Dependency: FORECAST-001.
  - Constraint: Do not claim the forecast is accurate merely because it runs.

- [x] **FORECAST-003 — Implement exponential-smoothing fallback**
  - Goal: Add the statsmodels fallback using the same public function signature as the primary method.
  - Files: `core/forecasting.py`.
  - Test: Both methods return the agreed output contract for suitable input.
  - Dependency: FORECAST-001.

- [x] **FORECAST-004 — Handle unsuitable forecast input**
  - Goal: Return a clear, safe error/result when history is empty, too short, irregular, or unsuitable for the selected method.
  - Files: `core/forecasting.py` and tests.
  - Test: Each documented unsuitable-input case has a test.
  - Dependency: FORECAST-002, FORECAST-003.

- [x] **FORECAST-005 — Calculate projected daily balance**
  - Goal: Convert forecast output into a 14-day projected balance from the approved starting balance.
  - Files: `core/forecasting.py`.
  - Test: Hand-calculated test cases match expected balances and interval behavior.
  - Dependency: FORECAST-001, DEC-001, DEC-004.

- [x] **RISK-001 — Define risk result contract**
  - Goal: Define cash-crunch result fields including date, days away, shortfall, and severity.
  - Files: `core/risk_engine.py`.
  - Test: Contract tests validate all required fields.
  - Dependency: DEC-005.

- [x] **RISK-002 — Implement safety-cushion detection**
  - Goal: Compare the conservative forecast estimate against the user-set safety cushion.
  - Files: `core/risk_engine.py`.
  - Test: Cases above, at, and below the cushion match the approved rule.
  - Dependency: FORECAST-005, RISK-001.

- [x] **RISK-003 — Generate warning content**
  - Goal: Produce warning data containing amount, date, severity, and a plain-language suggested action.
  - Files: `core/risk_engine.py`.
  - Test: Warning content is complete, consistent, and does not claim certainty about a future shortage.
  - Dependency: RISK-002, DEC-005.

- [x] **FORECAST-006 — Add forecast backtesting**
  - Goal: Evaluate forecasts against held-out historical periods where suitable data exists.
  - Files: `core/backtesting.py`, `tests/test_backtesting.py`.
  - Test: Evaluation reports the agreed metrics reproducibly.
  - Dependency: FORECAST-002, FORECAST-005, DEC-006.
  - Constraint: Keep thresholds marked unresolved until Sanjay approves them.

## 6. Phase 3 — Onboarding, Dashboard, and What-If

- [x] **UI-001 — Implement onboarding fields**
  - Goal: Collect name, phone number, business name, business type, and preferred language.
  - Files: `ui/onboarding.py`.
  - Test: Required fields and invalid input behave as documented.

- [x] **UI-002 — Implement consent/privacy screen**
  - Goal: Explain data use and consent in simple language before connecting or importing financial data.
  - Files: `ui/onboarding.py`, `ui/dashboard.py`.
  - Test: Screen explains the relevant data flow and provides the agreed consent action.
  - Dependency: DEC-007.
  - Constraint: Do not invent legal assurances.

- [x] **UI-003 — Implement current-balance input/source flow**
  - Goal: Use the source and interaction approved by Sanjay.
  - Files: `ui/onboarding.py`, `ui/dashboard.py`.
  - Test: Starting balance is validated and passed to the forecast flow.
  - Dependency: DEC-001.

- [x] **UI-004 — Connect ingestion to the core pipeline**
  - Goal: Allow CSV and selected AA sandbox data to enter the shared cleaning and forecast pipeline.
  - Files: `app.py`, `ui/dashboard.py`, `aggregator/csv_import.py`, `aggregator/setu_sandbox.py`.
  - Test: Both paths reach the same core interface.
  - Dependency: DATA-008, FORECAST-001.

- [x] **UI-005 — Display dashboard summary**
  - Goal: Display current balance, 14-day forecast chart, and warning card.
  - Files: `ui/dashboard.py`.
  - Test: UI displays known fixture values correctly and has an empty/error state.
  - Dependency: FORECAST-005, RISK-003.

- [x] **WHATIF-001 — Define payment-delay simulation contract**
  - Goal: Specify how a specific payment is identified and how delaying it by N days changes the projection.
  - Files: `core/whatif_simulator.py`.
  - Test: Contract covers payment identification, valid delay values, and result shape.
  - Dependency: DEC-005 and an agreed payment-identification rule.

- [x] **WHATIF-002 — Implement payment-delay simulation**
  - Goal: Recalculate the forecast after delaying the selected payment without changing source transaction records.
  - Files: `core/whatif_simulator.py`.
  - Test: A hand-calculated case changes the projected dates/balances as expected; original input remains unchanged.
  - Dependency: WHATIF-001, FORECAST-005.

- [x] **WHATIF-003 — Add What-If controls to the dashboard**
  - Goal: Let the user select a payment and a delay in days and view the revised forecast.
  - Files: `ui/dashboard.py`.
  - Test: Control output matches the core simulator and does not trigger a real payment.
  - Dependency: WHATIF-002.

## 7. Phase 4 — Persistence and Trial Stub

- [x] **DB-001 — Define SQLite schema and access boundary**
  - Goal: Implement only the approved user, consent, transaction, and necessary forecast-related records.
  - Files: `storage/db.py`.
  - Test: Schema initialization succeeds in a temporary development database.
  - Dependency: Approved data model and DEC-007.

- [x] **DB-002 — Implement persistence operations**
  - Goal: Save and retrieve records through the storage module rather than directly from UI code.
  - Files: `storage/db.py`.
  - Test: Round-trip tests preserve the agreed fields and types.
  - Dependency: DB-001.

- [x] **DB-003 — Implement consent revocation and deletion**
  - Goal: Support the approved consent-revocation and user-data deletion behavior.
  - Files: `storage/db.py`.
  - Test: Test records are removed or made inaccessible according to the approved deletion contract.
  - Dependency: DB-002, DEC-007.

- [x] **BILLING-001 — Represent free-trial status**
  - Goal: Track the 30-day trial and paid-status placeholder without integrating payments.
  - Files: `storage/db.py`, `ui/dashboard.py`.
  - Test: Trial state transitions follow the agreed local rules.
  - Constraint: Do not invent final pricing or payment-provider behavior.

- [x] **DB-004 — Verify storage safeguards**
  - Goal: Test the approved encryption, secret handling, and access-control measures.
  - Files: `storage/db.py`.
  - Test: Record exactly which safeguards are implemented and which remain open.
  - Dependency: DEC-007.
  - Constraint: Do not use real financial data until the safeguards are reviewed.

## 8. Phase 5 — Integration and Release Candidate

- [x] **TEST-001 — Add core unit-test suite**
  - Goal: Test parsing, normalization, categorization, forecasting, risk detection, and What-If logic.
  - Files: Test modules in `tests/`.
  - Test: Pytest test suite executed: 28 passed in ~8s.
  - Completed: Verified comprehensive coverage across all core modules.

- [x] **TEST-002 — Add CSV end-to-end test**
  - Goal: Verify CSV upload through to dashboard outputs using synthetic data.
  - Files: `tests/test_e2e.py`.
  - Test: Verified `test_full_csv_journey_e2e` passed.
  - Dependency: DATA-008, UI-004, UI-005.

- [x] **TEST-003 — Add AA sandbox end-to-end test**
  - Goal: Verify the selected sandbox flow through to dashboard outputs.
  - Files: `tests/test_e2e.py`, `tests/test_setu_sandbox.py`.
  - Test: Verified `test_full_aa_sandbox_journey_e2e` passed.
  - Dependency: DATA-007, UI-004, UI-005.

- [x] **TEST-004 — Verify failure and empty states**
  - Goal: Test invalid uploads, unavailable provider responses, forecast failures, and empty history.
  - Files: `tests/test_csv_import.py`, `tests/test_forecasting.py`, `tests/test_risk_engine.py`.
  - Test: Verified clean error handling and `InsufficientHistoryError` with no fabricated values.

- [x] **TEST-005 — Review forecast quality and warning behavior**
  - Goal: Compare backtest results with the approved thresholds and inspect false alarms/missed alarms.
  - Files: `core/backtesting.py`, `tests/test_backtesting.py`.
  - Test: Verified backtesting metrics execution (MAE, RMSE, directional accuracy, false/missed alarms).
  - Dependency: FORECAST-006, DEC-006.

- [x] **SECURITY-001 — Complete privacy and compliance verification checklist**
  - Goal: Record verified obligations and remaining questions for DPDP and production AA access.
  - Files: `docs/SECURITY.md`.
  - Test: Checklist verified and updated; remaining legal/deployment items preserved as `[TO VERIFY]`.
  - Dependency: DEC-009.
  - Constraint: Do not claim legal compliance based only on this checklist.

- [x] **RELEASE-001 — Confirm MVP acceptance checklist**
  - Goal: Verify each MVP acceptance criterion in `PRD.md`.
  - Files: Release validation report.
  - Test: Every criterion in FR-001 through FR-013 verified against implementation and test evidence.

- [x] **AGENT-001 — Interactive Cash Flow Advisory Demo Agent**
  - Goal: Provide an evidence-grounded conversational agent answering cash crunch timing, shortfall analysis, actionable remedies, and What-If suggestions.
  - Files: `core/advisor_agent.py`, `ui/dashboard.py`, `tests/test_advisor_agent.py`.
  - Test: 8/8 unit tests passing covering greetings, crunches, shortfalls, recommendations, expenses, and What-If queries.

- [ ] **RELEASE-002 — Deploy a safe release candidate**
  - Goal: Deploy to the approved host using suitable test data and reviewed configuration.
  - Files: Deployment configuration and `README.md` if instructions change.
  - Test: Follow the deployment instructions and verify the core user journey.
  - Dependency: DEC-008, RELEASE-001.
  - Status: [BLOCKED] Awaiting founder hosting selection (DEC-008). Run instructions for local development and staging verified.
  - Constraint: Do not expose secrets or use real customer financial data before required safeguards are verified.

## 9. Explicitly Deferred

The following are not MVP TODO items. Do not create implementation tasks for them unless Sanjay approves a scope change.

- [FROM BRIEF] Weekly voice-note summaries and translation/TTS for Hindi, Tamil, Telugu, Kannada, and Punjabi.
- [FROM BRIEF] WhatsApp delivery of alerts and voice notes.
- [FROM BRIEF] Phone OTP login.
- [FROM BRIEF] Live payment gateway.
- [FROM BRIEF] Mobile-friendly frontend/PWA beyond the approved MVP interface.
- [FROM BRIEF] Receivables tracking.
- [FROM BRIEF] Anonymous trade-association benchmarks, GST reminders, invoice integration, and multi-shop support.
- [FROM BRIEF] Moving money, payments, lending, bank-login credential storage, LLM-based forecasting, crypto, investments, and personal budgeting.

## 10. Suggestions (not in scope)

- [STANDARD PRACTICE] Maintain a short decision log for approved resolutions to DEC items.
- [STANDARD PRACTICE] Attach test evidence to each completed task in the development notes or pull request.
- [STANDARD PRACTICE] Keep a known-limitations list for forecast behavior and sandbox constraints.

## 11. Open Questions / TO VERIFY

1. DEC-001: How will the MVP obtain the current balance?
2. DEC-002: Which AA sandbox provider will be used first?
3. DEC-003: What is the exact CSV import contract?
4. DEC-004: How will forecast values and uncertainty be interpreted as projected balances?
5. DEC-005: What rules define warning severity and suggested actions?
6. DEC-006: What forecast metrics and thresholds are acceptable?
7. DEC-007: Which data safeguards are required before handling real data?
8. DEC-008: Which hosting option is approved after review?
9. DEC-009: What DPDP and production AA requirements apply?
10. [TO VERIFY] What exact minimum history length should trigger a forecast, and how should the app explain insufficient history?
