# CashSight — DESIGN.md

**Purpose:** Define the MVP user experience, visual hierarchy, interaction patterns, and warning language for CashSight so the app feels clear and trustworthy to small-shop owners.

**Last updated:** 2026-10-02

## Summary

- [FROM BRIEF] CashSight helps a small shop owner understand whether cash may run short in the next 14 days and what action they could consider.
- [FROM BRIEF] The main MVP experience includes onboarding, a consent/privacy screen, a dashboard, forecast visualization, cash-crunch warning, and payment-delay What-If simulation.
- [STANDARD PRACTICE] Use plain language, visible uncertainty, readable layouts, and actionable errors rather than technical jargon.
- [FROM BRIEF] Preferred language is collected during onboarding; Phase 2 voice notes and WhatsApp delivery are not MVP features.
- [TO VERIFY] Validate the wording, language needs, and dashboard comprehension with 5–10 shop owners.

## 1. Design Goals

1. [FROM BRIEF] Help users see their current balance and the next 14 days of projected cash position.
2. [FROM BRIEF] Make potential cash shortages visible before the expected date, with an estimated amount and suggested action.
3. [FROM BRIEF] Explain data collection and consent in simple language.
4. [STANDARD PRACTICE] Make uncertainty clear: a forecast is an estimate, not a guarantee.
5. [STANDARD PRACTICE] Prioritize the information a shop owner needs to act; avoid financial jargon and unnecessary charts.
6. [STANDARD PRACTICE] Make common states understandable on a smartphone-sized screen even though the MVP uses Streamlit.
7. [FROM BRIEF] Do not design UI for out-of-scope features as if they are committed MVP functionality.

## 2. Target User and Context

[FROM BRIEF] Primary user: owner of a small shop in an Indian tier-2 or tier-3 city, typically with 1–10 employees, uses a smartphone and UPI, is comfortable with WhatsApp, may prefer a regional language, and may not be financially technical.

Design implications:
- [STANDARD PRACTICE] Use short sentences and familiar words such as “cash available,” “money coming in,” “payments going out,” and “possible shortfall.”
- [STANDARD PRACTICE] Avoid unexplained terms such as “confidence interval,” “time series,” “model residual,” or “liquidity exposure” in the primary UI.
- [STANDARD PRACTICE] Show dates and INR amounts in a consistent, readable format.
- [STANDARD PRACTICE] Do not assume every user has connected a bank account; CSV import is also an MVP path.
- [STANDARD PRACTICE] Never imply that CashSight can move money, pay suppliers, or guarantee that a shortage will occur or be avoided.

## 3. Information Architecture

| Screen / area | Purpose | MVP status |
|---|---|---|
| Onboarding | Collect name, phone number, business name, business type, and preferred language | [FROM BRIEF] MVP |
| Consent and privacy | Explain data use and obtain the agreed consent before relevant data processing | [FROM BRIEF] MVP |
| Data input | Allow CSV upload and the approved AA sandbox flow | [FROM BRIEF] MVP |
| Starting balance | Collect or obtain the current balance through the method Sanjay approves | [TO VERIFY] MVP dependency |
| Dashboard | Present current balance, forecast chart, and warning card | [FROM BRIEF] MVP |
| What-If simulator | Show the effect of delaying a specific payment by N days | [FROM BRIEF] MVP |
| Trial/billing status | Represent 30-day trial and paid status; billing may be stubbed | [FROM BRIEF] MVP |
| Voice-note settings and WhatsApp alerts | Not part of the MVP interface | [FROM BRIEF] Phase 2 |
| Receivables management | Not part of the MVP interface | [FROM BRIEF] Phase 2 |

## 4. Dashboard Layout

### 4.1 Recommended content order

1. **Current balance**
   - [FROM BRIEF] Display the current balance prominently.
   - [STANDARD PRACTICE] Show the date/time or data reference associated with the balance when that information is available and reliable.
   - [TO VERIFY] Do not invent a timestamp if the source does not provide one.

2. **Cash outlook for the next 14 days**
   - [FROM BRIEF] Display a chart of projected daily balance and an uncertainty range.
   - [STANDARD PRACTICE] Label the chart with dates, INR, and a short explanation of what the line and range represent.
   - [STANDARD PRACTICE] Avoid visual precision that suggests the forecast is guaranteed.

3. **Potential cash-crunch warning**
   - [FROM BRIEF] Show the estimated shortfall amount, expected date, severity, and suggested action.
   - [STANDARD PRACTICE] If no shortage is detected, say that no shortage was detected by the current forecast; do not promise that the user will have enough cash.
   - [STANDARD PRACTICE] If the forecast cannot be generated, show that the outlook is unavailable rather than showing stale or fabricated results.

4. **What-If simulator**
   - [FROM BRIEF] Allow the user to select a specific payment and delay it by N days.
   - [STANDARD PRACTICE] Clearly distinguish the simulated result from the original forecast.
   - [STANDARD PRACTICE] State that the simulator does not make or reschedule a real payment.

5. **Data status and next step**
   - [STANDARD PRACTICE] Make it clear whether the data came from CSV or the approved AA sandbox, and explain any import or data-quality issue.
   - [STANDARD PRACTICE] Offer a clear path to correct input errors or retry a failed import.

## 5. Warning Language and Tone

### 5.1 Principles

- [FROM BRIEF] Warnings must include amount, date, severity, and a suggested action.
- [STANDARD PRACTICE] Use calm, direct language. Avoid panic-inducing phrases, blame, or shame.
- [STANDARD PRACTICE] Use “may,” “estimated,” or “based on the available data” when describing forecast outcomes.
- [STANDARD PRACTICE] Distinguish an estimate from a confirmed bank balance or a guaranteed future event.
- [TO VERIFY] Final warning thresholds and severity labels must be approved by Sanjay.

### 5.2 Example copy — illustrative only

These examples demonstrate tone and are not a finalized risk policy.

**Potential shortfall**

> **Possible cash shortage on [date]**  
> Based on the transactions available, your projected cash may fall about ₹[amount] below your safety cushion.  
> **You could consider:** reviewing whether a planned payment can be rescheduled or following up on money expected to arrive.  
> This is an estimate, not a guarantee.

**No shortage detected**

> **No cash shortage detected in this forecast**  
> The current estimate stays at or above your safety cushion for the next 14 days. Actual cash flow may differ.

**Forecast unavailable**

> **We couldn't prepare your cash outlook yet**  
> Check that your transaction dates and amounts are correct, and that enough history is available. Your existing data has not been changed.

**Data needs attention**

> **Please check your imported transactions**  
> Some rows could not be read. Review the highlighted issues and upload a corrected file.

**What-If result**

> **Simulated result: payment delayed by [N] days**  
> This view shows how the forecast changes if the selected payment happens later. It does not change the actual payment or your original transaction records.

## 6. Consent and Privacy Screen

[FROM BRIEF] The app must explain consent and privacy in simple language. Exact legal wording and applicable obligations are `[TO VERIFY]`.

Recommended content structure:
- What information the user is about to share.
- Why CashSight needs transaction information to estimate future cash flow.
- Which source is being used: CSV upload or the approved AA sandbox flow.
- A clear consent action before relevant data processing.
- A way to revoke consent.
- A clear explanation of the available data-deletion process.
- A reminder that bank login credentials are not requested or stored by CashSight.
- [TO VERIFY] Provider-specific wording, retention details, and legal disclosures must be confirmed before production use.

Do not use copy such as “100% secure,” “zero risk,” or “fully compliant” unless an appropriate, verified basis supports the exact claim.

## 7. Onboarding and Input Behavior

### 7.1 Required onboarding fields

[FROM BRIEF] Collect:
- Name
- Phone number
- Business name
- Business type
- Preferred language

[STANDARD PRACTICE] Explain why a field is needed if the reason is not obvious. Validate formats and show errors beside the relevant field.

### 7.2 Current balance

[TO VERIFY] The source and entry flow for current balance have not been decided. Design this area only after Sanjay approves the method. Do not silently infer a starting balance from imported transactions.

### 7.3 CSV import

[STANDARD PRACTICE] The upload flow should:
- Explain the required file format before upload.
- Show a preview or summary of the imported rows before relying on them.
- Identify rows that failed validation and why.
- Distinguish accepted rows from rejected rows.
- Avoid claiming a successful import if validation or storage failed.

[TO VERIFY] The exact CSV columns, file limits, duplicate-handling rules, and preview behavior must be settled in the data contract.

### 7.4 Account Aggregator sandbox

[FROM BRIEF] The MVP includes an AA sandbox path, subject to the selected provider and access being confirmed.

[STANDARD PRACTICE] Explain the next step and current connection state clearly. Do not ask users to type bank passwords into CashSight. Do not imply production access exists when only a sandbox has been tested.

## 8. What-If Simulator

Required behavior:
- [FROM BRIEF] User selects a specific payment and a delay of N days.
- [FROM BRIEF] The app recalculates and displays the revised forecast.
- [STANDARD PRACTICE] Keep the original forecast visible or provide a clear way to compare original and simulated results.
- [STANDARD PRACTICE] Label the result as a simulation.
- [STANDARD PRACTICE] Do not mutate source transaction records.
- [STANDARD PRACTICE] Do not initiate, cancel, or reschedule any real payment.

[TO VERIFY] Payment identification, valid delay range, and handling of payments that cannot be uniquely identified need an approved rule before implementation.

## 9. Language and Accessibility

- [FROM BRIEF] Collect preferred language during onboarding.
- [FROM BRIEF] Phase 2 voice-note summaries are planned for Hindi, Tamil, Telugu, Kannada, and Punjabi; these are not MVP voice features.
- [STANDARD PRACTICE] Keep MVP text simple and use a consistent terminology glossary so later translations can be accurate.
- [STANDARD PRACTICE] Do not show a language selector as proof that every screen is translated unless translations are actually implemented.
- [STANDARD PRACTICE] Use readable text, clear labels, keyboard-accessible controls where supported, and more than color alone to communicate warning severity.
- [TO VERIFY] Confirm which MVP interface languages will actually be supported at launch.

## 10. Visual System

[TO VERIFY] The brand palette, typeface, and detailed visual style have not been approved in the brief. Do not invent brand specifications and treat them as locked.

Until the visual system is approved:
- [STANDARD PRACTICE] Prefer a restrained, high-contrast interface with consistent spacing and clear hierarchy.
- [STANDARD PRACTICE] Use semantic visual states consistently for normal, attention-needed, and error states.
- [STANDARD PRACTICE] Do not rely on color alone to communicate risk; pair visual treatment with text and labels.
- [STANDARD PRACTICE] Avoid decorative dashboards, excessive cards, unnecessary animation, and dense financial charts.
- [STANDARD PRACTICE] Use INR consistently and avoid unexplained abbreviations.

## 11. Loading, Empty, and Error States

| Situation | Expected behavior |
|---|---|
| No transactions uploaded | [STANDARD PRACTICE] Explain how to add CSV data or use the approved AA sandbox path |
| Insufficient history | [STANDARD PRACTICE] Explain that the forecast cannot be trusted or generated yet; do not fabricate values |
| Invalid CSV | [STANDARD PRACTICE] Identify actionable row/column errors and allow correction |
| AA sandbox unavailable | [STANDARD PRACTICE] Explain that the connection failed and offer a safe retry path |
| Forecast method fails | [FROM BRIEF] Try the approved fallback where suitable; otherwise show a clear unavailable state |
| No cash crunch detected | [STANDARD PRACTICE] State only what the current forecast indicates; do not guarantee future sufficiency |
| Storage operation fails | [STANDARD PRACTICE] Do not show success until the operation succeeds; explain that the action could not be completed |
| Consent revoked | [FROM BRIEF] Stop processing data that requires that consent, according to the approved flow |
| User requests deletion | [FROM BRIEF] Provide the approved deletion flow and communicate its result accurately |

## 12. UX Acceptance Checklist

- [ ] [FROM BRIEF] Onboarding collects all five required fields.
- [ ] [FROM BRIEF] A plain-language consent/privacy screen is present.
- [ ] [FROM BRIEF] Both CSV and the selected AA sandbox path can feed the common pipeline.
- [ ] [FROM BRIEF] Dashboard shows current balance, 14-day forecast chart, and warning card.
- [ ] [FROM BRIEF] A warning includes estimated amount, date, severity, and suggested action.
- [ ] [FROM BRIEF] What-If simulation delays a selected payment by N days and does not change actual records.
- [ ] [STANDARD PRACTICE] Unavailable or invalid data is explained rather than replaced with fabricated results.
- [ ] [STANDARD PRACTICE] Forecast uncertainty is communicated clearly.
- [ ] [STANDARD PRACTICE] Color is not the only indicator of status or severity.
- [ ] [TO VERIFY] Shop-owner usability checks confirm that users understand the dashboard and warning copy.

## 13. Suggestions (not in scope)

- [STANDARD PRACTICE] Create a small glossary of approved financial terms before translating the UI.
- [STANDARD PRACTICE] Use synthetic example transactions in screenshots and demos.
- [FROM BRIEF] Do not implement WhatsApp delivery, voice-note playback, receivables tracking, or other Phase 2 features in the MVP.

## 14. Open Questions / TO VERIFY

1. What source or interaction will supply the current balance?
2. Which MVP interface languages will be fully supported?
3. What are the approved warning severity thresholds and exact action-selection rules?
4. What is the final CSV contract and import-preview behavior?
5. Which AA sandbox provider and connection flow will be used?
6. What exact legal/privacy copy and retention disclosures are required for production?
7. What visual palette, typography, and brand style should be treated as approved?
8. What minimum history is needed before showing a forecast, and how should the UI explain insufficient history?
9. What payment identifiers and delay range will the What-If simulator support?
10. What usability results from 5–10 shop-owner interviews should trigger design changes?
