# CashSight — RULES.md

**Purpose:** Give Antigravity explicit, enforceable rules for implementing CashSight safely, consistently, and one approved TODO task at a time.

**Last updated:** 2026-10-02

## Summary

- [FROM BRIEF] The approved brief and project documents define the product scope; do not invent or silently expand it.
- [FROM BRIEF] Implement exactly one TODO task at a time, with a clear goal, limited file scope, and a test.
- [FROM BRIEF] Keep business logic independent of Streamlit UI code.
- [FROM BRIEF] Do not store bank login credentials, add unapproved paid services, or implement Phase 2/3 features in the MVP.
- [STANDARD PRACTICE] Report actual changes and test results honestly; never claim a test passed unless it was run and passed.

## 1. Source of Truth and Precedence

Before changing code, read these files:

1. `README.md`
2. `docs/PRD.md`
3. `docs/ARCHITECTURE.md`
4. `docs/ROADMAP.md`
5. `docs/TODO.md`
6. `docs/DESIGN.md`
7. `docs/RULES.md`
8. `docs/SECURITY.md` when it exists

Rules:
- [FROM BRIEF] The locked product brief is the source of truth for scope.
- [STANDARD PRACTICE] Use the documents above to understand the approved implementation details.
- [FROM BRIEF] If documents conflict, stop and report the exact conflict. Do not pick a version silently.
- [FROM BRIEF] If a decision is unresolved or marked `[TO VERIFY]`, do not turn it into a permanent behavior without Sanjay's approval.
- [FROM BRIEF] Label substantive claims in project documentation as `[FROM BRIEF]`, `[STANDARD PRACTICE]`, or `[TO VERIFY]` as appropriate.
- [STANDARD PRACTICE] If a file listed above has not yet been created, report that fact and continue only when the current task can be completed without inventing its contents.

## 2. One-Task-at-a-Time Workflow

For every task:

1. Read the exact task in `docs/TODO.md`.
2. Check its dependencies and unresolved decisions.
3. Before implementation, report:
   - Task ID and title.
   - Goal.
   - Files expected to change.
   - Acceptance test.
   - Any blocker.
4. If blocked by a decision or dependency, stop and ask Sanjay. Do not implement dependent behavior.
5. Make the smallest change that completes the task.
6. Run the stated test and any directly relevant existing tests.
7. Inspect the diff for unrelated changes, secrets, scope creep, and inconsistencies.
8. Report files changed, commands run, actual results, and remaining limitations.
9. Mark the task complete only when its acceptance check passes. If testing is blocked, leave it unchecked and explain why.
10. Wait for Sanjay's direction before moving to another TODO task.

Do not implement multiple unchecked TODO tasks in one pass, even if they appear easy or related.

## 3. Scope Lock

### MVP includes

- [FROM BRIEF] Onboarding fields: name, phone number, business name, business type, preferred language.
- [FROM BRIEF] Both CSV upload and an Account Aggregator sandbox ingestion path, feeding one canonical transaction schema.
- [FROM BRIEF] Cleaning and categorization: rent, supplier, salary, sales, utilities, other.
- [FROM BRIEF] A 14-day cash-balance forecast with an uncertainty range.
- [FROM BRIEF] Cash-crunch detection against a user-set safety cushion.
- [FROM BRIEF] Plain-language warning with estimated amount, date, severity, and suggested action.
- [FROM BRIEF] Dashboard with current balance, forecast chart, and warning card.
- [FROM BRIEF] What-If simulator that delays a specific payment by N days and shows the revised forecast.
- [FROM BRIEF] Simple consent/privacy screen.
- [FROM BRIEF] 30-day free trial followed by paid status; billing can be stubbed.

### Must not be added to MVP without explicit approval

- [FROM BRIEF] Voice-note summaries or translation/TTS.
- [FROM BRIEF] WhatsApp alerts or delivery.
- [FROM BRIEF] Phone OTP login.
- [FROM BRIEF] A live payment gateway.
- [FROM BRIEF] Receivables tracking.
- [FROM BRIEF] Anonymous trade-association benchmarks, GST reminders, invoice integration, multi-shop support.
- [FROM BRIEF] Money movement, payments, lending, bank credential storage, LLM-based forecasting, crypto, investments, or personal budgeting.
- [FROM BRIEF] Any feature not listed in the approved scope.

## 4. Technology Constraints

- [FROM BRIEF] Use Python 3.10+.
- [FROM BRIEF] Use Streamlit for the MVP UI.
- [FROM BRIEF] Use pandas for tabular transaction processing.
- [FROM BRIEF] Use Prophet with weekly seasonality and yearly seasonality disabled.
- [FROM BRIEF] Provide a statsmodels exponential-smoothing fallback with the same public function signature as the primary forecast path.
- [FROM BRIEF] Use SQLite for development storage; PostgreSQL is planned for production.
- [FROM BRIEF] Use the approved Account Aggregator sandbox provider only after provider selection and access are confirmed.
- [FROM BRIEF] Use Plotly or Streamlit-native charts.
- [FROM BRIEF] Use Git and GitHub for version control.
- [FROM BRIEF] Prefer free/open-source tooling; no paid services or API keys unless Sanjay approves them.
- [FROM BRIEF] Phase 2 voice dependencies such as deep-translator and gTTS are not needed for MVP tasks unless explicitly approved.

Do not add a new dependency without explaining why it is required for the current task, whether it is free/open-source, and whether it introduces credentials, network access, licensing, or maintenance implications.

## 5. Architecture and Module Boundaries

- [FROM BRIEF] Keep forecasting, risk detection, and What-If logic in `core/`.
- [FROM BRIEF] Keep provider-specific AA code in `aggregator/`.
- [FROM BRIEF] Keep CSV import logic in `aggregator/csv_import.py`.
- [FROM BRIEF] Keep database operations behind `storage/db.py`.
- [FROM BRIEF] Keep UI screens in `ui/`; Streamlit calls belong in `app.py` and `ui/`.
- [FROM BRIEF] Keep `config.py` for non-secret configuration.
- [STANDARD PRACTICE] Avoid circular imports and unnecessary cross-module dependencies.
- [STANDARD PRACTICE] Do not put business rules, forecasting calculations, or risk thresholds directly inside UI rendering code.
- [STANDARD PRACTICE] Do not let provider-specific response formats leak into core forecasting or risk functions.
- [STANDARD PRACTICE] Keep source transaction records unchanged when running a What-If simulation.
- [STANDARD PRACTICE] Use the approved function contracts in `ARCHITECTURE.md`; if a contract is incomplete or contradictory, stop and ask.

## 6. Data and Financial Calculation Rules

- [FROM BRIEF] Represent transaction amount as a positive INR value and use `type` to distinguish `inflow` from `outflow`, as specified by the approved schema.
- [STANDARD PRACTICE] Apply inflow/outflow signs consistently in calculations; do not infer sign from an amount field if the canonical schema already has a transaction type.
- [FROM BRIEF] Forecast approximately six months of daily net cash flow when available and use a 14-day horizon.
- [FROM BRIEF] Use the conservative lower estimate for cash-crunch warnings.
- [TO VERIFY] The exact starting/current-balance source is unresolved. Do not calculate or invent it from transaction history unless Sanjay approves that rule.
- [TO VERIFY] The mapping from model forecast values and uncertainty bounds to projected daily balances must be explicitly decided and tested.
- [TO VERIFY] Minimum acceptable history, missing-day treatment, duplicate detection, severity thresholds, and forecast acceptance metrics must not be guessed.
- [STANDARD PRACTICE] Use deterministic, hand-calculated test cases for core financial arithmetic.
- [STANDARD PRACTICE] Use decimal-safe currency arithmetic where appropriate; document any numeric representation and rounding policy.
- [STANDARD PRACTICE] Do not round intermediate values in a way that changes warning decisions. Round for display according to an approved display rule.
- [STANDARD PRACTICE] If data is insufficient or a calculation fails, show a clear unavailable/error state rather than fabricating a number.

## 7. Forecasting Rules

- [FROM BRIEF] Keep forecasting independent of Streamlit.
- [FROM BRIEF] Use Prophet with weekly seasonality only; yearly seasonality must be disabled because the expected history is around six months.
- [FROM BRIEF] Provide an exponential-smoothing fallback through the same public function signature.
- [STANDARD PRACTICE] Use a fallback only when the input is suitable for it; do not treat fallback output as automatically accurate.
- [STANDARD PRACTICE] Handle model exceptions and unsuitable history explicitly.
- [STANDARD PRACTICE] Do not invent a forecast or silently reuse stale results after a failure.
- [FROM BRIEF] Backtest forecasting behavior and document limitations.
- [TO VERIFY] Do not declare the model validated until Sanjay approves measurable acceptance thresholds and the observed results meet them.

## 8. Security and Privacy Rules

- [FROM BRIEF] Never request, collect, log, or store bank login credentials.
- [FROM BRIEF] Use only read-only, consent-based AA sandbox behavior as approved for the MVP.
- [FROM BRIEF] Store only the approved user details, consent records, and transaction data needed by the product.
- [FROM BRIEF] Support consent revocation and user data deletion.
- [FROM BRIEF] Encrypt stored data as required by the approved security design.
- [TO VERIFY] Exact encryption implementation, key handling, access controls, retention behavior, DPDP Act 2023 obligations, and production AA requirements must be verified before production use.
- [STANDARD PRACTICE] Never commit API keys, access tokens, passwords, private keys, connection strings with credentials, or real financial data.
- [STANDARD PRACTICE] Keep secrets out of logs, error messages, screenshots, and test fixtures.
- [STANDARD PRACTICE] Use environment-based secret configuration only when a verified integration actually requires a secret.
- [STANDARD PRACTICE] Do not claim legal compliance or complete security based solely on implemented controls or a checklist.
- [STANDARD PRACTICE] Use synthetic data for tests and demos unless Sanjay explicitly approves another safe test-data arrangement.

## 9. Input Validation and Error Handling

- [STANDARD PRACTICE] Validate data at system boundaries: CSV uploads, provider responses, user input, and storage operations.
- [STANDARD PRACTICE] Return errors that explain what the user can correct without exposing internal traces or sensitive values.
- [STANDARD PRACTICE] Do not silently drop invalid rows or alter amounts without reporting the behavior.
- [STANDARD PRACTICE] Handle empty data, missing columns, invalid dates, invalid amounts, duplicates, unavailable provider responses, and model failures deliberately.
- [STANDARD PRACTICE] Do not report an import, save, deletion, or consent change as successful until the operation has actually succeeded.
- [STANDARD PRACTICE] Keep detailed debugging output in development logs only when it does not expose secrets or personal/financial data.

## 10. Code Quality

- [STANDARD PRACTICE] Use clear, descriptive names and small functions with one primary responsibility.
- [STANDARD PRACTICE] Add type hints to public function boundaries where practical.
- [STANDARD PRACTICE] Document non-obvious financial calculations and domain assumptions.
- [STANDARD PRACTICE] Avoid unnecessary abstraction, premature optimization, duplicated business rules, and unrelated refactoring.
- [STANDARD PRACTICE] Keep formatting and style consistent with the existing project.
- [STANDARD PRACTICE] Do not add dead code, unused dependencies, placeholder secrets, or fake implementations presented as complete features.
- [STANDARD PRACTICE] Keep sample data clearly labeled as fictional.
- [STANDARD PRACTICE] Prefer explicit errors over broad exception handling that hides failures.

## 11. Testing Rules

For each task:
- [STANDARD PRACTICE] Add or update tests appropriate to the changed behavior.
- [STANDARD PRACTICE] Test both expected input and at least the relevant boundary/error cases.
- [STANDARD PRACTICE] Run the exact test command and report its actual output or a concise factual summary.
- [STANDARD PRACTICE] Do not say “all tests pass” if only a subset was run.
- [STANDARD PRACTICE] If tests cannot run, state the missing dependency, environment issue, or other blocker and leave the task unchecked.
- [STANDARD PRACTICE] Never weaken or delete a test simply to make the suite pass without explaining the behavior change and getting approval when scope or requirements are affected.
- [STANDARD PRACTICE] Do not use live bank data or unapproved external services in routine tests.

## 12. Git and Change Management

- [STANDARD PRACTICE] Inspect repository status before changing files.
- [STANDARD PRACTICE] Do not overwrite unrelated user changes.
- [STANDARD PRACTICE] Do not delete or rename existing files unless the active task requires it and the effect is explained.
- [STANDARD PRACTICE] Keep each change focused on the active TODO task.
- [STANDARD PRACTICE] Do not commit or push unless Sanjay explicitly asks.
- [STANDARD PRACTICE] Before finishing, inspect the diff and report any unexpected changes.

## 13. Required Antigravity Response Format

Before a task:

```text
Task: [TODO ID and title]
Goal: [one sentence]
Files expected to change: [list]
Dependencies/blockers: [list, or none]
Acceptance test: [specific test]
```

After a task:

```text
Task: [TODO ID and title]
Status: COMPLETE / BLOCKED / FAILED
Files changed: [list]
Implementation summary: [brief, factual]
Commands run: [exact commands]
Test results: [actual results]
Known limitations: [list, or none]
TODO update: [checked or left unchecked, with reason]
Next step: Wait for Sanjay's instruction.
```

Do not report COMPLETE unless the task's acceptance check passed.

## 14. Handling Uncertainty

When requirements are missing or conflict:
1. Identify the exact missing decision or conflicting statements.
2. Explain why it blocks the current task.
3. Ask Sanjay no more than three focused questions at a time.
4. Continue only with independent work that does not encode the unresolved decision.
5. Record the approved decision in the relevant documentation when directed.

Do not use internet research to silently decide product scope. For current provider behavior, libraries, legal requirements, or regulatory details, verify authoritative documentation when research is requested or required and record the source in the appropriate document.

## 15. Suggestions (not in scope)

- [STANDARD PRACTICE] Use a consistent test command and document it in the README once the test setup exists.
- [STANDARD PRACTICE] Keep a short decision log for choices Sanjay explicitly approves.
- [STANDARD PRACTICE] Add automated secret scanning if a suitable free tool is approved and its use is justified.
- [FROM BRIEF] Do not implement these suggestions unless they are approved and fit the active task.

## 16. Open Questions / TO VERIFY

1. What exact formatting/linting and test tools will be approved for the repository?
2. What currency representation and display-rounding policy will be used consistently?
3. What encryption and key-management approach will be approved before real financial data is stored?
4. What minimum transaction history is required before generating a forecast?
5. What exact rules determine severity and suggested actions?
6. What forecast accuracy and warning-quality thresholds will be used?
7. Which AA sandbox provider and verified integration contract will be used?
8. What deployment-specific controls are required before any real customer data is processed?
