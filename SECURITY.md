# CashSight — SECURITY.md

**Purpose:** Document CashSight's MVP data handling, consent boundaries, security controls, deletion expectations, and legal/regulatory questions that must be verified before production use.

**Last updated:** 2026-10-02

## Summary

- [FROM BRIEF] CashSight processes shop-owner profile information and consented transaction data to estimate cash flow over the next 14 days.
- [FROM BRIEF] The MVP includes CSV upload and an Account Aggregator sandbox path; both must feed the same internal transaction schema.
- [FROM BRIEF] CashSight must not store bank login credentials and must support consent revocation and user data deletion.
- [STANDARD PRACTICE] Use synthetic data for development, validate inputs, keep secrets out of source control, and restrict access to stored data.
- [TO VERIFY] Exact encryption controls, retention periods, DPDP obligations, production AA requirements, and deployment-specific safeguards must be verified before real customer financial data is processed.

## 1. Scope and Security Principles

1. [FROM BRIEF] Protect user profile details, consent records, and transaction data handled by CashSight.
2. [FROM BRIEF] Use only the approved, read-only, consent-based AA sandbox flow for the MVP.
3. [FROM BRIEF] Never collect or store bank login credentials.
4. [FROM BRIEF] Provide a way to revoke consent and request deletion of the user's data.
5. [STANDARD PRACTICE] Minimize the amount of personal and financial information stored.
6. [STANDARD PRACTICE] Use synthetic data in development and demonstrations unless a separate, reviewed arrangement is approved.
7. [STANDARD PRACTICE] Do not claim that CashSight is “fully secure,” “zero risk,” or legally compliant without a verified basis.
8. [TO VERIFY] Complete the security and legal review before using production bank data or onboarding real customers.

## 2. Data Inventory

The following inventory reflects the current product brief and draft data model. Exact fields and retention behavior must be confirmed during implementation.

| Data category | Examples / planned fields | Purpose | Status |
|---|---|---|---|
| User profile | User ID, name, phone, business name, business type, preferred language | Onboarding and associating data with a user | [FROM BRIEF] Planned |
| Current balance | Starting/current balance and its source/reference | Starting point for projected balance | [TO VERIFY] Source unresolved |
| Transactions | Date, description, category, type, amount in INR | Forecasting and cash-crunch detection | [FROM BRIEF] Planned |
| Consent records | User ID, provider, data period, granted time, revoked time | Record the consent state and data scope | [FROM BRIEF] Planned |
| Forecast results | Date, forecast values, uncertainty bounds, projected balance | Dashboard and risk analysis | [FROM BRIEF] Planned |
| Cash-crunch results | Date, days away, estimated shortfall, severity | Warning card and suggested action | [FROM BRIEF] Planned |
| Trial status | Trial/paid-status placeholder | Represent 30-day trial and paid state | [FROM BRIEF] Planned |
| Bank login credentials | Bank passwords, PINs, online banking credentials | No valid CashSight purpose | [FROM BRIEF] Must not be collected or stored |
| Secrets | Provider tokens or deployment secrets, if a verified integration requires them | Provider/deployment access | [TO VERIFY] Store only through an approved secret mechanism; never in source control |

[STANDARD PRACTICE] Store only the fields required for the approved MVP. Do not add analytics identifiers, extra personal details, or unrelated financial data without explicit scope approval and a documented purpose.

## 3. Data Flow and Trust Boundaries

### 3.1 Planned flow

1. The user provides profile details and sees the consent/privacy screen.
2. The user imports a CSV file or uses the approved AA sandbox flow.
3. Incoming data is validated and normalized into the canonical transaction schema.
4. Core forecasting and risk logic processes the normalized data.
5. The dashboard displays the current balance, forecast, and any warning.
6. The storage layer persists only the approved records.
7. The user can revoke consent or request data deletion through the approved flow.

[FROM BRIEF] CSV and AA sandbox ingestion are both in the MVP scope.

[STANDARD PRACTICE] Treat uploaded files and provider responses as untrusted input. Validate content and structure before processing; do not execute uploaded content.

### 3.2 Trust boundaries

| Boundary | Security concern | Required approach |
|---|---|---|
| User device → Streamlit app | Invalid or manipulated user input | [STANDARD PRACTICE] Validate input and avoid exposing internal errors |
| CSV file → importer | Malformed, oversized, unexpected, or malicious file content | [STANDARD PRACTICE] Enforce an approved file contract and reject unsupported formats safely |
| AA provider → adapter | Untrusted or malformed provider response; unexpected provider behavior | [STANDARD PRACTICE] Validate provider data and isolate provider-specific parsing |
| UI → core logic | Invalid values or accidental bypass of validation | [STANDARD PRACTICE] Validate at service/module boundaries, not only in UI controls |
| App → database | Unauthorized access, unintended persistence, deletion failures | [STANDARD PRACTICE] Centralize access through the storage layer and test lifecycle operations |
| App → deployment environment | Exposed secrets, logs, configuration, or data | [STANDARD PRACTICE] Review configuration, logs, access, and hosting data-handling behavior |
| User → consent process | User may not understand data use or revocation | [FROM BRIEF] Explain consent and privacy in simple language; [TO VERIFY] verify required legal wording |

## 4. Consent and Revocation

### 4.1 Consent principles

- [FROM BRIEF] Present a consent/privacy screen using simple language.
- [FROM BRIEF] The product uses transaction information to estimate upcoming cash flow.
- [STANDARD PRACTICE] Explain the source of data, the intended use, and the action the user is taking before data is processed.
- [STANDARD PRACTICE] Do not use preselected consent or misleading wording to imply the user agreed.
- [TO VERIFY] Confirm provider-specific consent wording, required notices, purpose limitations, and records needed for the selected AA sandbox and any future production flow.

### 4.2 Revocation

[FROM BRIEF] Users must be able to revoke consent.

Implementation requirements:
- [STANDARD PRACTICE] Record the consent state and the time of revocation where appropriate.
- [STANDARD PRACTICE] After revocation, stop any processing that depends on the revoked consent, according to the approved product and provider flow.
- [STANDARD PRACTICE] Show a clear result only after the revocation operation succeeds.
- [TO VERIFY] Determine whether revocation must also trigger a provider-side action, what data can be retained, and what the applicable requirements are.

## 5. Data Deletion and Retention

### 5.1 Deletion

[FROM BRIEF] CashSight must support user data deletion.

Implementation requirements:
- [STANDARD PRACTICE] Define which records are linked to a user and how related records are found.
- [STANDARD PRACTICE] Test deletion using a dedicated test user and synthetic transactions.
- [STANDARD PRACTICE] Ensure deletion results are accurately reported; do not display success when some required deletion step failed.
- [STANDARD PRACTICE] Consider copies in derived records, temporary files, logs, exports, and backups when defining the deletion behavior.
- [TO VERIFY] Approve the precise deletion scope, backup treatment, exceptions, and confirmation wording before production.

### 5.2 Retention

[TO VERIFY] The product brief does not specify retention periods.

Before production, decide and document:
- How long profile data is retained.
- How long imported and AA-sourced transaction data is retained.
- Whether forecast outputs are retained or recalculated.
- How revoked-consent data is handled.
- Whether any records must be retained for a verified legal or operational reason.
- How temporary files, logs, and backups are handled.

Do not invent a retention period or promise immediate deletion from every backup until the actual system behavior and applicable requirements have been verified.

## 6. Storage and Encryption

### 6.1 Development storage

- [FROM BRIEF] SQLite is planned for development; PostgreSQL is planned for production.
- [STANDARD PRACTICE] Keep database access behind `storage/db.py`.
- [STANDARD PRACTICE] Do not commit a database file containing real personal or financial data.
- [STANDARD PRACTICE] Keep local development databases, exported files, and generated sample data out of source control when they may contain sensitive information.
- [STANDARD PRACTICE] Use fictional records for automated tests and demos.

### 6.2 Encryption

[FROM BRIEF] Stored data must be encrypted.

[TO VERIFY] The exact implementation has not yet been selected. Before real customer data is stored, Sanjay must approve a design that addresses:
- Encryption at rest for the database and relevant files.
- Encryption in transit for deployed app traffic and provider communication.
- Key creation, storage, access, rotation, and recovery.
- Secret handling for any provider integration that requires credentials or tokens.
- Encryption and deletion implications for backups and temporary files.
- Whether the selected hosting tier supports the required controls.

[STANDARD PRACTICE] Do not treat a database file, a hosting platform, or a network connection as secure solely because it is in use. Verify the actual configuration and its limits.

## 7. Access Control and Secrets

- [STANDARD PRACTICE] Grant access only to people and services that need it.
- [STANDARD PRACTICE] Do not expose database files, environment configuration, or secret values through the UI.
- [STANDARD PRACTICE] Keep secrets out of Git, screenshots, issue reports, test fixtures, and logs.
- [STANDARD PRACTICE] Use an approved environment or secret-management mechanism when a verified integration requires secrets.
- [STANDARD PRACTICE] Never place API keys or tokens directly into source files or documentation.
- [TO VERIFY] Confirm authentication and authorization requirements for production. Phone OTP login is Phase 2 and is not an MVP feature.
- [TO VERIFY] Review whether the chosen hosting platform's access and secret-management controls meet the intended deployment requirements.

## 8. Logging and Error Messages

- [STANDARD PRACTICE] Logs should help diagnose failures without containing full transaction descriptions, phone numbers, bank account details, access tokens, or other unnecessary personal/financial data.
- [STANDARD PRACTICE] Avoid logging entire CSV rows or raw provider responses by default.
- [STANDARD PRACTICE] Error messages shown to users should explain the next safe action without exposing stack traces, file paths, secrets, or internal implementation details.
- [STANDARD PRACTICE] Development diagnostics may include technical details only when sensitive values are excluded.
- [STANDARD PRACTICE] Do not log consent tokens, provider access tokens, or secret configuration values.

## 9. CSV and Provider Input Safety

### 9.1 CSV files

- [STANDARD PRACTICE] Accept only the approved file format and columns.
- [STANDARD PRACTICE] Validate dates, amounts, transaction types, and required fields before forecasting.
- [STANDARD PRACTICE] Set file-size and row-count limits after the deployment constraints are known.
- [STANDARD PRACTICE] Do not execute formulas, macros, scripts, or embedded content from uploaded files.
- [STANDARD PRACTICE] Handle unexpected encodings, malformed rows, and empty files without crashing.
- [TO VERIFY] Exact upload limits and duplicate-row behavior remain to be decided.

### 9.2 AA sandbox responses

- [FROM BRIEF] Use a read-only, consent-based sandbox flow.
- [STANDARD PRACTICE] Verify response structure and required fields before normalizing transactions.
- [STANDARD PRACTICE] Handle timeouts, rejected requests, expired consent, and malformed responses without fabricating transactions or balances.
- [TO VERIFY] Provider-specific authentication, token handling, consent lifecycle, response fields, and production requirements must come from verified provider documentation.
- [STANDARD PRACTICE] Do not assume sandbox credentials or behavior can be used in production.

## 10. Forecast and Warning Integrity

- [FROM BRIEF] Forecasting must not use an LLM.
- [FROM BRIEF] The forecast horizon is 14 days and the output includes an uncertainty range.
- [FROM BRIEF] Cash-crunch detection uses the conservative lower estimate and compares it with the user's safety cushion.
- [STANDARD PRACTICE] Clearly label forecasts as estimates and show when data is insufficient or the forecast failed.
- [STANDARD PRACTICE] Do not show fabricated, stale, or silently substituted values as current results.
- [STANDARD PRACTICE] Keep What-If results separate from the original forecast and source transactions.
- [TO VERIFY] Define the starting-balance source, uncertainty propagation, warning thresholds, and minimum history before considering warning behavior production-ready.

## 11. Compliance and Regulatory Verification

This section is a verification checklist, not a legal conclusion.

### 11.1 India DPDP Act 2023

[FROM BRIEF] The brief identifies India's Digital Personal Data Protection Act, 2023 as relevant and marks exact obligations `[TO VERIFY]`.

Before production:
- [TO VERIFY] Verify which provisions, rules, commencement dates, and obligations apply to the planned service at launch.
- [TO VERIFY] Verify notice and consent requirements, user rights, data handling, retention/deletion, security safeguards, grievance or contact requirements, and any other applicable obligations.
- [TO VERIFY] Confirm whether any additional rules or sector-specific obligations apply to the selected data flows.
- [STANDARD PRACTICE] Use current authoritative government sources and, where needed, qualified legal advice.
- [STANDARD PRACTICE] Record the source, date checked, applicability conclusion, owner, and remaining action for each item.

### 11.2 Account Aggregator requirements

[FROM BRIEF] Production AA regulatory requirements are unresolved.

Before production:
- [TO VERIFY] Confirm the chosen provider's sandbox access conditions and the difference between sandbox and production access.
- [TO VERIFY] Confirm what role CashSight would hold in the production AA ecosystem and what approvals, agreements, security controls, consent flows, or technical requirements apply.
- [TO VERIFY] Verify whether the planned product can legally and operationally access the intended data through the chosen route.
- [STANDARD PRACTICE] Use current official provider and regulatory documentation; do not infer production permission from successful sandbox tests.

### 11.3 Deployment review

- [TO VERIFY] Review the selected host's data location, logs, backups, access control, encryption, secret management, and incident-response capabilities.
- [TO VERIFY] Determine what security incident handling and user communication procedures are required.
- [STANDARD PRACTICE] Do not claim compliance or production readiness until the relevant checks have been completed and documented.

## 12. Security Test Checklist

- [ ] [STANDARD PRACTICE] No bank login credentials are requested, logged, or stored.
- [ ] [STANDARD PRACTICE] No real personal or financial data is committed to the repository.
- [ ] [STANDARD PRACTICE] Secrets are absent from source files, logs, and error messages.
- [ ] [STANDARD PRACTICE] CSV input is validated and unsupported files are rejected safely.
- [ ] [STANDARD PRACTICE] Provider responses are validated before processing.
- [ ] [STANDARD PRACTICE] Storage access is centralized behind the storage module.
- [ ] [FROM BRIEF] Consent revocation is implemented and tested.
- [ ] [FROM BRIEF] User data deletion is implemented and tested.
- [ ] [TO VERIFY] Approved encryption controls are implemented and tested before real data is used.
- [ ] [STANDARD PRACTICE] Errors do not expose stack traces or sensitive values to end users.
- [ ] [STANDARD PRACTICE] What-If simulation does not mutate original transaction data.
- [ ] [TO VERIFY] Deployment-specific security review is complete before production use.
- [ ] [TO VERIFY] Applicable DPDP and production AA obligations have been verified and documented.

## 13. Incident and Recovery Planning

[TO VERIFY] A production incident-response plan has not been defined in the brief.

Before production, document:
- How suspected unauthorized access or data exposure is reported internally.
- Who is responsible for triage and decisions.
- How access or affected integrations can be disabled safely.
- How logs and evidence are preserved without spreading sensitive data.
- How recovery is performed and verified.
- What notification obligations and timelines apply, based on verified requirements.

[STANDARD PRACTICE] Do not promise that an incident can be fully prevented. Define a practical way to detect, contain, investigate, and respond to problems.

## 14. Suggestions (not in scope)

- [STANDARD PRACTICE] Add a dependency vulnerability review to the release checklist using an approved free tool.
- [STANDARD PRACTICE] Add a documented backup/restore test before production data is stored.
- [STANDARD PRACTICE] Keep a dated security decision log and record links to authoritative sources.
- [FROM BRIEF] Do not implement additional security tooling or services without confirming it fits the approved stack and scope.

## 15. Open Questions / TO VERIFY

1. What is the approved current-balance source and how will it be protected?
2. Which AA sandbox provider is selected, and what exact sandbox and production access conditions apply?
3. What encryption-at-rest, encryption-in-transit, and key-management approach will be approved?
4. What authentication and authorization controls are required for the MVP deployment?
5. What are the approved retention periods and deletion semantics, including backups and logs?
6. What exact DPDP Act 2023 provisions and rules apply at the planned launch date?
7. What production AA role, approvals, agreements, and security requirements apply?
8. Which host will be used, and what are its data-handling and access-control properties?
9. What are the approved CSV file-size, row-count, and duplicate-handling rules?
10. What incident-response and recovery process is required before production?
