# CashSight — Product Requirements Document (PRD)

**Purpose:** Define CashSight's users, MVP requirements, phased scope, acceptance criteria, and validation metrics for implementation by Google Antigravity.

**Last updated:** October 2, 2026

## Short Summary

- [FROM BRIEF] CashSight helps small Indian shop owners anticipate cash shortages approximately 14 days ahead.
- [FROM BRIEF] The MVP includes onboarding, consent, two transaction-ingestion paths, categorization, forecasting, warnings, a dashboard, a What-If simulator, and a subscription structure.
- [FROM BRIEF] The forecast uses Prophet with a statsmodels fallback; core business logic must remain independent of Streamlit.
- [TO VERIFY] Forecast accuracy thresholds, current-balance source, production Account Aggregator access, and exact legal obligations remain unresolved.
- [FROM BRIEF] No features outside the Scope Lock may be implemented without founder approval.

## 1. Document Rules and Evidence Labels

Use these labels throughout this document:

- **[FROM BRIEF]** — explicitly stated in the supplied CashSight brief.
- **[STANDARD PRACTICE]** — a general implementation or product-development recommendation, not a confirmed product requirement.
- **[TO VERIFY]** — an unresolved question that must not be treated as fact.

If this document conflicts with another approved project document, stop and report the conflict. Do not silently choose one interpretation.

## 2. Product Overview

### 2.1 Product statement

[FROM BRIEF] CashSight is a subscription tool that forecasts cash flow for small Indian shop owners and warns them about possible cash shortages approximately 14 days in advance.

### 2.2 Problem statement

[FROM BRIEF] Small traders and shop owners often manage money with diaries and intuition. They may not know whether enough cash will be available for rent, salaries, and supplier payments over the next two weeks. Delayed or bounced payments can damage supplier trust and credit relationships.

### 2.3 Core value proposition

[FROM BRIEF] “Know 2 weeks ahead if you will run short of cash, and what to do about it.”

Example message from the brief: “In 12 days you may be short by about Rs 40,000. Consider collecting these 3 pending payments now.”

[TO VERIFY] The example mentions pending customer payments, but receivables tracking is explicitly Phase 2. The MVP must not claim to identify pending receivables unless the required information is available through an approved in-scope input and the behavior is specified.

### 2.4 Product principles

- [FROM BRIEF] Use calm, reassuring language, not alarming language.
- [FROM BRIEF] Keep language simple and minimize financial jargon.
- [FROM BRIEF] Think mobile-first and support the preferred-language field.
- [FROM BRIEF] Every warning must include a suggested action.
- [FROM BRIEF] Address users' fear of sharing bank data clearly.
- [FROM BRIEF] Do not use an LLM for forecasting.
- [STANDARD PRACTICE] Make assumptions and forecast uncertainty visible rather than presenting predictions as guarantees.

## 3. Target Users

| Attribute | Requirement |
|---|---|
| Primary user | [FROM BRIEF] Owner of a small retail or trading shop in a tier-2 or tier-3 Indian city |
| Business size | [FROM BRIEF] 1–10 employees |
| Typical business types | [FROM BRIEF] Hardware, clothing, kirana, wholesale |
| Devices and behavior | [FROM BRIEF] Uses a smartphone and UPI; comfortable with WhatsApp |
| Language | [FROM BRIEF] May prefer a regional language over English |
| Financial expertise | [FROM BRIEF] Not financially technical |
| Buying motivation | [FROM BRIEF] Peace of mind and control, not reports |
| Main trust barrier | [FROM BRIEF] Fear of sharing bank data |

## 4. Scope by Phase

### 4.1 MVP — required

The MVP must include all of the following:

1. Onboarding fields: name, phone number, business name, business type, preferred language.
2. CSV/statement upload.
3. Account Aggregator sandbox ingestion.
4. A common internal transaction schema used by both ingestion paths.
5. Transaction cleaning and categorization into rent, supplier, salary, sales, utilities, and other.
6. A 14-day projected daily cash balance with an uncertainty range.
7. Cash-crunch detection against a user-set safety cushion.
8. Plain-language warnings with amount, date, severity, and suggested action.
9. Dashboard with current balance, forecast chart, and warning card.
10. What-If simulation that delays a specific payment by N days and displays the changed forecast.
11. Consent and privacy screen in simple language.
12. Subscription structure: 30-day free trial followed by a paid plan; billing may be stubbed.

### 4.2 Phase 2 — planned, not MVP

- Weekly voice-note summaries in Hindi, Tamil, Telugu, Kannada, and Punjabi, using translation and text-to-speech.
- WhatsApp delivery of alerts and voice notes.
- Phone OTP login.
- Real payment gateway.
- Mobile-friendly frontend or PWA.
- Receivables tracking.

### 4.3 Phase 3 — future ideas only

- Anonymous trade-association benchmarks.
- GST payment reminders.
- Invoice integration.
- Multi-shop support.

### 4.4 Out of scope

Do not implement:

- Money movement, payments, or lending.
- Storage of bank login credentials.
- LLM-based forecasting.
- Crypto, investments, or personal budgeting.
- Any feature not listed in the Scope Lock.

## 5. User Stories

| ID | User story | Priority |
|---|---|---|
| US-001 | As a shop owner, I want to enter my basic business details and preferred language so the product can be configured for me. | Must-have |
| US-002 | As a shop owner, I want to understand and consent to financial-data use before providing data. | Must-have |
| US-003 | As a shop owner, I want to import a CSV/statement so my transactions can be processed. | Must-have |
| US-004 | As a shop owner, I want to connect through the selected Account Aggregator sandbox so supported financial transactions can be ingested with consent. | Must-have |
| US-005 | As a shop owner, I want transactions cleaned and categorized so I can understand cash movement. | Must-have |
| US-006 | As a shop owner, I want to see a 14-day projected balance and uncertainty range so I can plan ahead. | Must-have |
| US-007 | As a shop owner, I want a warning when projected cash falls below my safety cushion so I can take action. | Must-have |
| US-008 | As a shop owner, I want a dashboard showing my current balance, forecast chart, and warning card. | Must-have |
| US-009 | As a shop owner, I want to simulate delaying a specific payment and see how the forecast changes. | Must-have |
| US-010 | As a shop owner, I want to revoke consent and request deletion of my data. | Must-have |
| US-011 | As a shop owner, I want to understand the free-trial and paid-subscription structure. | Must-have |
| US-012 | As a shop owner, I want weekly voice-note summaries in a supported language. | Phase 2 |
| US-013 | As a shop owner, I want alerts delivered through WhatsApp. | Phase 2 |
| US-014 | As a shop owner, I want to track pending customer payments. | Phase 2 |

## 6. Functional Requirements

### FR-001 — Onboarding

**Requirement:** [FROM BRIEF] Collect name, phone number, business name, business type, and preferred language.

**Acceptance criteria:**
- The onboarding interface provides fields for all five items.
- Values are validated before being saved.
- No additional profile fields are introduced without approval.
- [TO VERIFY] Authentication and access-control behavior for the MVP must be defined before real user data is exposed.

### FR-002 — Consent and privacy

**Requirement:** [FROM BRIEF] Present a consent and privacy screen in simple language.

**Acceptance criteria:**
- The screen explains the purpose of financial-data use in understandable language.
- Consent status and the relevant provider/data period can be recorded using the approved data model.
- The user can revoke consent and request deletion.
- Revocation and deletion behavior must be documented and tested.
- [TO VERIFY] Exact legal wording and regulatory obligations require verification.

### FR-003 — CSV/statement ingestion

**Requirement:** [FROM BRIEF] Support CSV/statement upload as one ingestion path.

**Acceptance criteria:**
- Imported records are mapped into the common transaction schema.
- Invalid or unsupported records are handled without silently treating them as valid transactions.
- Import validation results are made understandable to the user.
- Duplicate handling and supported file formats must be defined in `ARCHITECTURE.md` or an approved implementation task; do not guess silently.

### FR-004 — Account Aggregator sandbox ingestion

**Requirement:** [FROM BRIEF] Support a read-only, consent-based Account Aggregator sandbox integration.

**Acceptance criteria:**
- Imported transaction data maps into the same internal transaction schema as CSV data.
- The implementation does not store bank login credentials.
- The integration uses only verified provider documentation and approved access.
- [TO VERIFY] Provider selection, sandbox setup, APIs, authentication details, and production access route must be confirmed before implementation.

### FR-005 — Transaction cleaning and categorization

**Requirement:** [FROM BRIEF] Clean transactions and categorize them as rent, supplier, salary, sales, utilities, or other.

**Acceptance criteria:**
- Each accepted transaction has a date, description, category, type, and positive INR amount.
- `type` distinguishes inflow from outflow.
- Transactions that cannot be categorized confidently must not be silently assigned a misleading category.
- [TO VERIFY] Exact categorization rules, manual correction behavior, transfer handling, and duplicate rules require definition.

### FR-006 — Current cash balance

**Requirement:** [FROM BRIEF] The dashboard and forecast use a current cash balance.

**Acceptance criteria:**
- The application must have a defined source for the opening/current balance before calculating the forecast.
- [TO VERIFY] The source and reconciliation approach are unresolved. Do not invent a balance source or claim a calculated balance is accurate until the founder approves the rule.

### FR-007 — Fourteen-day forecast

**Requirement:** [FROM BRIEF] Forecast daily cash balance for 14 days with an uncertainty range, starting from the current cash balance.

**Acceptance criteria:**
- Forecast horizon is 14 days.
- The output includes `ds`, `yhat`, `yhat_lower`, `yhat_upper`, and `projected_balance` as applicable to the approved architecture.
- Prophet uses weekly seasonality only and yearly seasonality is disabled.
- A statsmodels exponential-smoothing fallback is available with the same function signature.
- The warning engine uses the conservative lower estimate.
- No LLM is used for forecasting.
- Forecast output is clearly presented as an estimate.
- [TO VERIFY] Minimum history, sparse-data behavior, interval propagation to balance, accuracy thresholds, and backtesting criteria must be specified before reliability claims are made.

### FR-008 — Cash-crunch detection

**Requirement:** [FROM BRIEF] Detect potential cash shortages against a user-set safety cushion.

**Acceptance criteria:**
- The detection logic compares the approved conservative forecast measure with the user's safety cushion.
- A detected crunch includes crunch date, days away, shortfall, and severity.
- Severity is communicated calmly and consistently.
- [TO VERIFY] Exact severity bands, comparison formula, multiple-crunch handling, and shortfall calculation require definition in the architecture.

### FR-009 — Warning and suggested action

**Requirement:** [FROM BRIEF] Every warning includes amount, date, severity, and a suggested action.

**Acceptance criteria:**
- The warning includes all four required elements.
- Wording is plain-language and non-alarming.
- The warning does not imply certainty.
- Suggested actions must be grounded in available information and must not imply that CashSight can move money, make payments, lend, or access out-of-scope receivables data.

### FR-010 — Dashboard

**Requirement:** [FROM BRIEF] Show current balance, forecast chart, and warning card.

**Acceptance criteria:**
- All three elements are available in the MVP dashboard.
- The chart shows the 14-day forecast and uncertainty range.
- A warning card displays the relevant crunch details and suggested action when a crunch is detected.
- [TO VERIFY] Exact layout and empty-state behavior will be defined in `DESIGN.md`.

### FR-011 — What-If simulator

**Requirement:** [FROM BRIEF] Let the user delay a specific payment by N days and inspect the changed forecast.

**Acceptance criteria:**
- The user can select a specific payment and specify a delay in days.
- The simulator produces a changed forecast without silently modifying the original transaction history.
- The user can distinguish the simulated forecast from the baseline forecast.
- [TO VERIFY] Eligible payment rules, valid delay range, and handling of payments outside the 14-day horizon must be defined before implementation.

### FR-012 — Subscription structure

**Requirement:** [FROM BRIEF] Define a 30-day free trial followed by a paid subscription. Billing integration may be stubbed.

**Acceptance criteria:**
- Trial duration is represented as 30 days.
- The proposed monthly and annual prices are treated as hypotheses, not validated facts.
- No real payment gateway is added to the MVP.
- [TO VERIFY] Trial start/end behavior, subscription-state transitions, and feature access rules require definition.

### FR-013 — Data revocation and deletion

**Requirement:** [FROM BRIEF] Users can revoke consent and delete their data.

**Acceptance criteria:**
- The application provides an understandable path to revoke consent and request deletion.
- The system's behavior after revocation is explicit.
- Deletion behavior is tested and does not falsely claim removal if data remains.
- [TO VERIFY] Deletion scope, backup handling, retention obligations, and verification evidence require definition in `SECURITY.md`.

## 7. Non-Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| NFR-001 | Core business logic must remain independent of Streamlit. | [FROM BRIEF] |
| NFR-002 | Forecasting implementations must use identical function signatures. | [FROM BRIEF] |
| NFR-003 | Stored data must be encrypted. | [FROM BRIEF] |
| NFR-004 | The system must not store bank login credentials. | [FROM BRIEF] |
| NFR-005 | User-facing language must be simple, calm, and reassuring. | [FROM BRIEF] |
| NFR-006 | Prefer free or very low-cost tools; no paid dependency without founder approval. | [FROM BRIEF] |
| NFR-007 | Forecasting must be backtested before performance is treated as reliable. | [FROM BRIEF] |
| NFR-008 | Dependency and hosting compatibility must be tested in the target environment. | [STANDARD PRACTICE] |
| NFR-009 | [TO VERIFY] No latency, availability, throughput, or uptime target has been provided. Do not invent numeric service-level objectives. | [TO VERIFY] |

## 8. Success Metrics and Validation

### 8.1 Product validation

| Metric | Definition or target |
|---|---|
| Customer interviews | [FROM BRIEF] Interview 5–10 shop owners to validate the problem and pricing. |
| Pilot participation | [FROM BRIEF] Planned pilot with 3–5 real shops. |
| Willingness to pay | [TO VERIFY] Validate proposed pricing through interviews. |
| Forecast accuracy | [TO VERIFY] Define acceptable metrics and thresholds using representative data. |
| False alarms | [FROM BRIEF] Must be considered because they harm trust; exact acceptable rate is [TO VERIFY]. |
| Missed alarms | [FROM BRIEF] Must be considered because they harm trust; exact acceptable rate is [TO VERIFY]. |

### 8.2 Backtesting requirements

- [FROM BRIEF] Backtest the forecast.
- [STANDARD PRACTICE] Keep a record of the evaluation data, forecast horizon, metrics, and observed errors so results can be reviewed.
- [TO VERIFY] The precise metrics, thresholds, dataset requirements, and acceptance decision must be approved before making forecast-performance claims.

## 9. Acceptance Criteria for MVP Completion

The MVP is not complete until the following are demonstrated:

- [ ] Onboarding collects the five required fields.
- [ ] Consent and privacy information is presented in simple language.
- [ ] CSV/statement upload maps supported records into the common transaction schema.
- [ ] The selected Account Aggregator sandbox integration maps supported records into the same schema.
- [ ] Transaction cleaning and the six required categories work on representative test data.
- [ ] Current-balance source and calculation rules are approved and implemented.
- [ ] The 14-day forecast produces daily projected balances and an uncertainty range.
- [ ] The primary forecasting implementation and fallback share the same function signature.
- [ ] Cash-crunch detection uses the conservative estimate and configured safety cushion.
- [ ] Warnings include amount, date, severity, and a suggested action.
- [ ] Dashboard shows current balance, forecast chart, and warning card.
- [ ] What-If simulation delays a specific payment and shows a changed forecast without modifying baseline data.
- [ ] The subscription structure supports a 30-day trial model without a real payment gateway.
- [ ] Consent revocation and data-deletion behavior are implemented and tested.
- [ ] Backtesting has been performed, and unresolved accuracy limitations are documented.
- [ ] Required security controls have been reviewed before real financial data is used.
- [ ] Setup and test instructions are documented and verified in the target environment.

[TO VERIFY] The MVP cannot be declared ready for real-world financial-data processing or production deployment solely because these functional checks pass. Applicable access, security, and compliance requirements must also be verified.

## 10. Dependencies and Risks

| Risk or dependency | Impact | Required handling |
|---|---|---|
| Current balance is unknown | Forecast may start from an incorrect balance. | [TO VERIFY] Approve the source and reconciliation rule. |
| Account Aggregator access is unresolved | Integration may be blocked. | [TO VERIFY] Confirm provider and sandbox access before implementing integration details. |
| Transaction history may be incomplete | Forecast quality may be poor. | [TO VERIFY] Define data-quality checks and insufficient-history behavior. |
| Forecast uncertainty may be misinterpreted | Users may lose trust. | [FROM BRIEF] Show uncertainty and use the conservative estimate for warnings. |
| False alarms or missed alarms | Trust and usefulness may suffer. | [FROM BRIEF] Backtest and document handling; thresholds are [TO VERIFY]. |
| Pricing is unvalidated | Subscription model may not be commercially viable. | [FROM BRIEF] Interview 5–10 shop owners. |
| Legal/security requirements are unresolved | Real financial-data processing or production deployment may be inappropriate. | [TO VERIFY] Verify applicable requirements before proceeding. |
| Paid dependency is introduced | Conflicts with founder's cost constraint. | [FROM BRIEF] Obtain founder approval before adding paid tools or APIs. |

## 11. Suggestions (not in scope)

These are process suggestions, not new product features:

- [STANDARD PRACTICE] Use synthetic or otherwise approved test data to validate ingestion and forecasting before processing real shop-owner data.
- [STANDARD PRACTICE] Keep a small, repeatable backtesting dataset and record results across changes to forecasting logic.
- [STANDARD PRACTICE] Review every warning with a shop owner during the pilot to understand whether the wording is understandable and actionable.

These suggestions do not authorize adding functionality beyond the Scope Lock.

## 12. Open Questions / TO VERIFY

1. What is the approved source of the current cash balance, and how should it be reconciled with imported transactions?
2. Which Account Aggregator sandbox (Setu or Finvu) should be implemented first?
3. What sandbox access, integration details, and production access route are available?
4. What exact obligations under India's DPDP Act apply to this product?
5. What minimum history and data-quality conditions are required to generate a forecast?
6. Which backtesting metrics and accuracy thresholds are acceptable?
7. How should forecast uncertainty be translated into the projected balance interval?
8. What formula determines shortfall amount and severity?
9. How should false alarms and missed alarms be measured and handled?
10. How should ambiguous transactions, transfers, and duplicate imports be handled?
11. Which payments are eligible for the What-If simulator, and what delay range is valid?
12. What access-control approach is appropriate for the MVP before phone OTP exists?
13. What exact encryption, deletion, and backup-handling controls will be implemented?
14. What trial-state behavior is required when the 30-day period ends?
15. What deployment limits and dependency versions must be supported?

## Document Status

**Status:** Draft — awaiting founder approval.

This PRD defines product requirements and acceptance criteria. Detailed module boundaries and function contracts belong in `ARCHITECTURE.md`; milestone sequencing belongs in `ROADMAP.md`; implementation tasks belong in `TODO.md`; interface details belong in `DESIGN.md`; coding constraints belong in `RULES.md`; and security controls belong in `SECURITY.md`.
