# CashSight — Architecture Document

**Purpose:** Define CashSight's MVP components, data flow, persistence boundaries, module responsibilities, and proposed function contracts for implementation by Google Antigravity.

**Last updated:** October 2, 2026

## Short Summary

- [FROM BRIEF] CashSight uses Python 3.10+, Streamlit, pandas, Prophet with a statsmodels fallback, and SQLite for development.
- [FROM BRIEF] CSV/statement upload and an Account Aggregator sandbox must feed one common transaction schema.
- [FROM BRIEF] Business logic belongs in `core/`; Streamlit calls belong only in `app.py` and `ui/`.
- [STANDARD PRACTICE] Keep modules small and testable, validate inputs at module boundaries, and make data transformations explicit.
- [TO VERIFY] Current-balance source, detailed provider integration contracts, access control, encryption implementation, and forecast formulas need founder approval or verification.

## 1. Document Rules and Evidence Labels

Use these labels throughout this document:

- **[FROM BRIEF]** — explicitly stated in the supplied CashSight brief.
- **[STANDARD PRACTICE]** — a general engineering recommendation, not a confirmed product requirement.
- **[TO VERIFY]** — unresolved and must not be treated as fact.

If this document conflicts with an approved `README.md` or `PRD.md`, stop and report the conflict. Do not silently change the scope or choose an interpretation.

## 2. Architecture Goals

1. [FROM BRIEF] Keep core business logic independent of Streamlit.
2. [FROM BRIEF] Normalize both financial-data ingestion paths into one transaction schema.
3. [FROM BRIEF] Support a 14-day cash-balance forecast with an uncertainty range.
4. [FROM BRIEF] Support a Prophet implementation and a statsmodels fallback with identical function signatures.
5. [FROM BRIEF] Keep SQLite as the development database; PostgreSQL is planned for production.
6. [STANDARD PRACTICE] Make each component testable without requiring the entire application to run.
7. [FROM BRIEF] Avoid paid services or APIs unless the founder approves them.

## 3. High-Level Component Map

```text
User
 |
 v
Streamlit UI
(app.py and ui/)
 |
 v
Application orchestration
(app.py / UI coordination)
 |
 +-------------------+--------------------+
 |                   |                    |
 v                   v                    v
CSV importer     Account Aggregator    User inputs
aggregator/      sandbox adapter       onboarding,
                 aggregator/           safety cushion,
 |                                    What-If settings
 +-------------------+--------------------+
                     |
                     v
            Common transaction schema
                     |
                     v
            Cleaning and categorization
                     |
                     v
        Core business logic (core/)
        +-----------------------------+
        | forecasting.py              |
        | risk_engine.py              |
        | whatif_simulator.py          |
        +-----------------------------+
                     |
                     v
              Forecast / risk results
                     |
                     v
             Streamlit dashboard
                     |
                     v
          Persistence boundary (storage/)
                     |
                     v
                  SQLite
```

[STANDARD PRACTICE] This is a logical component map, not a claim that every arrow must be a direct function call. Exact call sequences should follow the approved function contracts and TODO task in progress.

## 4. Technology Responsibilities

| Component | Technology | Responsibility |
|---|---|---|
| Application language | Python 3.10+ | Application and business logic |
| UI | Streamlit | Screens, inputs, charts, and display |
| Data processing | pandas | Tabular transaction processing |
| Primary forecasting | Prophet | Forecasting with weekly seasonality enabled and yearly seasonality disabled |
| Fallback forecasting | statsmodels exponential smoothing | Alternative forecasting path |
| Development persistence | SQLite | Local database storage |
| Planned production persistence | PostgreSQL | Future production database |
| CSV ingestion | Python/pandas | Read and map supported uploaded transaction data |
| Account Aggregator ingestion | Setu or Finvu sandbox, provider to be selected | Read-only, consent-based transaction ingestion |
| Charts | Plotly or Streamlit native charts | Display forecast and uncertainty |
| Version control | Git and GitHub | Track code changes |

[TO VERIFY] The exact package versions, supported CSV/statement formats, provider SDK or API details, and hosting constraints must be confirmed during implementation. Do not invent provider endpoints, authentication flows, or library functions.

## 5. Module Boundaries

### 5.1 `app.py`

**Responsibilities**
- [FROM BRIEF] Act as the Streamlit UI entry point.
- [STANDARD PRACTICE] Coordinate the top-level UI flow and call UI modules or application-facing functions.
- [STANDARD PRACTICE] Display clear errors from failed operations without exposing secrets or sensitive transaction data.

**Restrictions**
- Do not put forecasting algorithms, categorization rules, risk formulas, or database queries directly in `app.py`.
- Do not implement provider integration logic in `app.py`.

### 5.2 `config.py`

**Responsibilities**
- [FROM BRIEF] Hold thresholds, languages, and constants.
- [STANDARD PRACTICE] Keep configuration values in one location rather than duplicating them across modules.

**TO VERIFY**
- The exact severity thresholds, supported MVP language behavior, and other numeric constants require approval or definition in later documents.

### 5.3 `data/`

**Responsibilities**
- [FROM BRIEF] Hold sample data, sample-data generation, and `data_loader.py`.
- [STANDARD PRACTICE] Provide repeatable test data for local development and backtesting.

**Restrictions**
- Sample data must be clearly identified as sample data.
- Do not represent sample data as actual customer or bank data.

### 5.4 `aggregator/csv_import.py`

**Responsibilities**
- Accept a supported CSV/statement input.
- Validate and map supported records to the common transaction schema.
- Return normalized transaction data or a clear validation error.

**TO VERIFY**
- Supported file formats, required column mappings, date formats, currency handling, duplicate detection, and ambiguous-record behavior need definition before implementation.

### 5.5 `aggregator/setu_sandbox.py`

**Responsibilities**
- Encapsulate the selected Account Aggregator sandbox integration.
- Respect read-only and consent-based requirements.
- Normalize supported returned transaction data into the common transaction schema.

**Restrictions**
- Do not store bank login credentials.
- Do not invent APIs, endpoints, SDKs, payloads, or provider requirements.
- Do not implement production access before its requirements have been verified.

**TO VERIFY**
- Whether Setu or Finvu is selected first, sandbox credentials/setup, integration contract, consent flow, and production access route.

### 5.6 Common transaction schema

[FROM BRIEF] Both ingestion paths must produce a common internal schema.

| Field | Meaning | Required handling |
|---|---|---|
| `date` | Transaction date | [TO VERIFY] Exact accepted input formats and timezone/date policy |
| `description` | Transaction description | Preserve an appropriate description; avoid logging sensitive raw data unnecessarily |
| `category` | rent, supplier, salary, sales, utilities, or other | Use only the approved categories |
| `type` | inflow or outflow | Must be one of the two values |
| `amount` | Transaction amount in INR | Positive amount; direction comes from `type` |

[STANDARD PRACTICE] Validate normalized records at ingestion boundaries so downstream core modules do not need to support arbitrary provider-specific shapes.

[TO VERIFY] Rules for transfers, reversals, refunds, duplicates, missing descriptions, and ambiguous categories are not yet specified.

### 5.7 `core/forecasting.py`

**Responsibilities**
- Accept validated historical cash-flow data and the approved current-balance input.
- Produce a 14-day forecast and uncertainty information.
- Support the primary Prophet method and statsmodels fallback.
- Keep the public function signature identical for both implementations.

**Restrictions**
- Do not import Streamlit or call UI functions.
- Do not use an LLM for forecasting.
- Use weekly seasonality only and disable yearly seasonality for the specified Prophet configuration.
- Do not claim that forecasts are accurate without backtesting evidence.

**Proposed function contract — signature details to verify**

The following names describe the intended interface, not verified library APIs:

```python
forecast_cash_balance(
    historical_net_cash_flow,
    current_balance,
    horizon_days=14,
    method="prophet",
)
```

Expected result: a structured forecast containing the forecast date (`ds`), predicted value (`yhat`), lower and upper uncertainty estimates (`yhat_lower`, `yhat_upper`), and projected balance.

[TO VERIFY] Confirm whether the returned `yhat` fields represent net cash flow or balance. Define the transformation from daily net cash-flow predictions into projected balances and uncertainty bands before implementation. The interface above is provisional and must be finalized consistently in `TODO.md`.

### 5.8 `core/risk_engine.py`

**Responsibilities**
- Compare the approved conservative forecast measure against the user's safety cushion.
- Produce cash-crunch results containing crunch date, days away, shortfall, and severity.
- Provide the information needed for a plain-language warning.

**Restrictions**
- Do not render Streamlit components.
- Do not make payments or move money.
- Do not infer receivables that are not available in approved input data.

**Proposed function contract — signature details to verify**

```python
detect_cash_crunches(
    forecast,
    safety_cushion,
)
```

Expected result: zero or more structured crunch results.

[TO VERIFY] Define the exact shortfall formula, severity thresholds, treatment of multiple dates, and how lower uncertainty estimates are propagated into projected balance.

### 5.9 `core/whatif_simulator.py`

**Responsibilities**
- Simulate delaying a specific payment by a specified number of days.
- Produce a changed forecast for comparison with the baseline.
- Keep the original transaction history unchanged.

**Proposed function contract — signature details to verify**

```python
simulate_payment_delay(
    transactions,
    payment_reference,
    delay_days,
    current_balance,
)
```

Expected result: a simulation result containing the changed forecast and enough information to compare it with the baseline.

[TO VERIFY] Define payment identification, valid delay range, behavior for payments outside the forecast horizon, and whether the simulator operates on a copy of normalized transaction data.

### 5.10 `storage/db.py`

**Responsibilities**
- Encapsulate SQLite persistence for development.
- Store approved user, consent, and transaction data, along with any additional persistence explicitly approved in the architecture.
- Provide operations used by the UI and core orchestration without exposing raw SQL throughout the project.

**Restrictions**
- Do not store bank login credentials.
- Do not make Streamlit calls.
- Do not claim encryption requirements are satisfied merely because SQLite is used.

**TO VERIFY**
- Exact schema, migrations, database location, transaction boundaries, encryption implementation, deletion behavior, and production PostgreSQL migration strategy.

### 5.11 `ui/onboarding.py` and `ui/dashboard.py`

**Responsibilities**
- [FROM BRIEF] Provide onboarding and dashboard UI modules.
- The onboarding UI collects name, phone, business name, business type, and preferred language.
- The dashboard presents current balance, forecast chart, and warning card.
- [FROM BRIEF] Present consent and privacy information in simple language.

**Restrictions**
- Keep forecasting, risk calculations, and database query logic out of UI modules.
- Do not add OTP login or a separate mobile frontend to the MVP.

## 6. Data Flow

### 6.1 CSV/statement path

1. User selects a supported file.
2. CSV importer validates the input.
3. The importer maps supported records to the common transaction schema.
4. The application reports invalid or rejected records clearly.
5. Valid transactions are passed to approved cleaning and categorization logic.
6. Approved data is persisted through `storage/db.py` when persistence is required.
7. Historical cash flow and an approved current balance are passed to the forecasting module.
8. Forecast output is passed to the risk engine.
9. The UI displays the current balance, forecast chart, uncertainty range, and any warning.

[TO VERIFY] Supported file formats, import preview behavior, duplicate handling, and whether imports replace or append data must be defined before implementation.

### 6.2 Account Aggregator sandbox path

1. The user is shown the relevant consent information.
2. The selected sandbox integration follows its verified consent-based, read-only flow.
3. Returned supported transaction data is normalized to the common transaction schema.
4. The same downstream cleaning, categorization, persistence, forecasting, risk, and UI path is used as for CSV data.

[TO VERIFY] Provider-specific flow and API details must come from verified provider documentation and approved access. Do not fabricate them.

### 6.3 Forecast and warning path

1. Load validated historical net cash-flow data.
2. Obtain the approved current cash balance.
3. Generate the 14-day forecast and uncertainty range.
4. Convert forecast output into projected daily balances using the approved formula.
5. Evaluate the conservative balance against the user's safety cushion.
6. Produce structured crunch results.
7. Render a plain-language warning with amount, date, severity, and suggested action.

[TO VERIFY] The precise conversion and uncertainty-propagation formulas are unresolved.

### 6.4 What-If path

1. Load the baseline normalized transaction data.
2. Identify the selected payment using the approved identification rule.
3. Apply the requested delay to a simulation copy only.
4. Recalculate the forecast using the same forecasting contract.
5. Display the simulated result separately from the baseline.

The simulation must not silently rewrite the user's original transaction history.

## 7. Data Persistence Model

The draft entities are:

| Entity | Fields from brief |
|---|---|
| Transaction | `date`, `description`, `category`, `type`, `amount` |
| User | `id`, `name`, `phone`, `business_name`, `business_type`, `language`, `safety_cushion` |
| Consent | `user_id`, `provider`, `data_period`, `granted_at`, `revoked_at` |
| Forecast row | `ds`, `yhat`, `yhat_lower`, `yhat_upper`, `projected_balance` |
| Crunch result | `crunch_date`, `days_away`, `shortfall`, `severity` |

[STANDARD PRACTICE] Use consistent date and numeric representations, validate records before persistence, and keep database access behind `storage/db.py`.

[TO VERIFY] Primary keys, foreign keys, indexes, database constraints, persistence of forecast results, audit records, retention, and migration mechanics are not specified in the brief and must be decided before implementation.

## 8. Error Handling and Observability

[STANDARD PRACTICE] Components should return clear validation failures for expected bad input and should not silently convert invalid financial data into valid-looking records.

Required implementation behavior:

- Invalid import records must not silently enter the forecasting dataset.
- A provider connection failure must be reported without exposing secrets.
- A forecasting failure must not be presented as a valid forecast.
- Missing or insufficient data must not be disguised as a reliable prediction.
- The UI should present a clear, calm message to the user.
- Developer diagnostics should avoid logging credentials or unnecessary raw financial descriptions.

[TO VERIFY] The exact error types, logging configuration, retention of logs, and insufficient-history behavior need definition in `RULES.md`, `SECURITY.md`, and implementation tasks.

## 9. Testing Boundaries

[STANDARD PRACTICE] Test each component independently and then test the full flow with representative sample data.

| Component | Minimum test focus |
|---|---|
| CSV importer | Valid rows, invalid rows, schema mapping |
| Account Aggregator adapter | Normalization using verified sandbox responses or approved fixtures |
| Cleaning/categorization | Required categories, inflow/outflow, invalid values |
| Forecasting | Output shape, 14-day horizon, fallback contract, failure handling |
| Risk engine | Above/below cushion cases, shortfall fields, severity contract |
| What-If simulator | Delay changes simulation; baseline remains unchanged |
| Storage | Save/load approved records, deletion behavior |
| UI | Required fields and dashboard elements render correctly |
| Integrated flow | Ingestion to forecast to warning using sample data |

[TO VERIFY] Numerical accuracy thresholds and backtesting acceptance criteria must be set before forecast accuracy can be accepted.

## 10. Dependency Direction Rules

The intended dependency direction is:

- `app.py` and `ui/` may call approved application-facing functions.
- `aggregator/` converts external inputs into the common transaction schema.
- `core/` contains business logic and must not depend on Streamlit.
- `storage/` owns persistence operations.
- `config.py` contains approved shared constants.
- Tests may exercise modules independently.

[STANDARD PRACTICE] Avoid circular imports. Keep provider-specific data shapes out of core forecasting and risk logic.

## 11. Suggestions (not in scope)

These are engineering-process suggestions, not new product features:

- [STANDARD PRACTICE] Use synthetic fixtures for provider and forecasting tests when real data is not needed.
- [STANDARD PRACTICE] Keep provider integration isolated so its implementation can change without rewriting the core forecasting logic.
- [STANDARD PRACTICE] Record the exact assumptions used in backtesting so forecast changes can be compared.

These suggestions do not authorize adding features beyond the Scope Lock.

## 12. Open Questions / TO VERIFY

1. What is the approved source of the current cash balance?
2. How should imported transactions be reconciled with that balance?
3. Which Account Aggregator sandbox should be implemented first: Setu or Finvu?
4. What verified sandbox setup, API contracts, and authentication requirements apply?
5. What are the supported CSV/statement formats and required columns?
6. How are duplicate imports, transfers, reversals, refunds, and ambiguous categories handled?
7. Does `yhat` represent predicted net cash flow or projected balance, and what is the exact balance/uncertainty calculation?
8. What minimum history and data-quality rules are required for forecasting?
9. What shortfall formula and severity thresholds should the risk engine use?
10. How are payment references identified and what delay range is allowed in What-If simulation?
11. What is the approved database schema, including keys and relationships?
12. How will encryption, access control, revocation, and deletion be implemented?
13. What is the MVP access-control approach before OTP login exists?
14. What dependency versions and hosting limits must be supported?
15. What backtesting metrics and acceptance thresholds will be used?

## Document Status

**Status:** Draft — awaiting founder approval.

This document defines component responsibilities, data flow, and provisional function contracts. Do not treat proposed function signatures or unresolved formulas as verified library APIs or final decisions. `ROADMAP.md` defines milestones; `TODO.md` defines implementation tasks; `DESIGN.md` defines user-interface behavior; `RULES.md` defines coding-agent constraints; and `SECURITY.md` defines security controls.
