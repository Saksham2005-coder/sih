# Workflow Transition Matrix — ReguFlow 360
## Guarded Regulatory State Machine Specification
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. Illustrative Workflow Routes & Regulatory Stages
Regulatory processing in AICTE varies depending on application type. ReguFlow 360 supports configurable workflow templates:
1. `EOA_ANNUAL`: Standard Extension of Approval (streamlined scrutiny, conditional EVC only if red-flagged).
2. `NEW_INSTITUTION`: Comprehensive scrutiny, mandatory EVC panel inspection, mandatory SAC/CAC committee review, Competent Authority approval.
3. `INTAKE_VARIATION`: Land/Cadre scrutiny, infrastructure check, optional EVC.
4. `CLOSURE_PROGRAM`: Scrutiny of no-objection certificates, student relocation plan, financial liability settlement.

---

### 2. Guarded State Machine Transitions

| From Stage | Allowed To Stage | Permitted Roles | Preconditions & Validation Rules | Side Effects |
|---|---|---|---|---|
| `DRAFT` | `SUBMITTED` | `INSTITUTION_ADMIN` | All mandatory application sections complete; processing fee paid or fee exemption code entered. | Records `SUBMITTED` timeline event; sets scrutiny deadline SLA clock (e.g. 7 days); creates Tier-1 notification for Regional Office. |
| `SUBMITTED` | `UNDER_SCRUTINY` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | Case assigned to designated Scrutiny Officer within the matching region. | Updates stage; assigns `scrutiny_officer_id`; records audit event. |
| `UNDER_SCRUTINY` | `DEFICIENCY_COMMUNICATED` | `REGIONAL_OFFICER` | At least one itemized deficiency must be logged with category, description, and required cure document. | Application status becomes `DEFICIENCY_COMMUNICATED`; sets cure SLA deadline (e.g. 15 days); generates urgent alert to Institution Admin & Compliance Officer. |
| `DEFICIENCY_COMMUNICATED` | `RESUBMITTED` | `INSTITUTION_ADMIN`, `COMPLIANCE_OFFICER` | Every pending deficiency item must have an uploaded cure document or written clarification response attached. | Cancels deficiency overdue alert; resets scrutiny SLA clock; notifies assigned Regional Officer. |
| `RESUBMITTED` | `UNDER_SCRUTINY` | `REGIONAL_OFFICER` | Regional officer acknowledges receipt of resubmitted evidence. | Timeline updated to scrutiny in progress. |
| `UNDER_SCRUTINY` | `SCRUTINY_COMPLETED` | `REGIONAL_OFFICER` | All logged deficiencies marked as "Satisfactorily Resolved" or zero deficiencies initially logged. | Scrutiny sign-off recorded; if route specifies mandatory EVC, transition to `AWAITING_EVC_SCHEDULE` is unlocked. |
| `SCRUTINY_COMPLETED` | `AWAITING_EVC_SCHEDULE` | Workflow Engine / `REGIONAL_OFFICER` | Triggered automatically if application route requires physical/virtual inspection (e.g. `NEW_INSTITUTION`). | Application pushed to EVC Queue; generates scheduling SLA alert for EVC Coordinator. |
| `AWAITING_EVC_SCHEDULE` | `EVC_SCHEDULED` | `EVC_COORDINATOR`, `REGIONAL_OFFICER` | Inspection date in future; at least 2 committee members assigned (1 Convener + 1 Subject Expert). | Generates formal inspection notice to Institution; schedules EVC deadline monitor. |
| `EVC_SCHEDULED` | `EVC_COMPLETED` | `EVC_COORDINATOR`, `COMMITTEE_MEMBER` | Inspection report uploaded, signed, and recommendation recorded (`RECOMMENDED_APPROVAL`, `RECOMMENDED_REJECTION`, `DEFICIENCY_NOTED`). | Inspection report linked to case; timeline updated; unlocks committee review stage. |
| `EVC_COMPLETED` | `AWAITING_SAC_CAC_REVIEW` | `BUREAU_OFFICER`, `REGIONAL_OFFICER` | Scrutiny & EVC reports verified complete. | Enters Standing Scrutiny / Appellate Committee queue. |
| `AWAITING_SAC_CAC_REVIEW` | `AWAITING_COMPETENT_AUTHORITY` | `COMMITTEE_MEMBER`, `BUREAU_OFFICER` | Committee minutes recorded with resolution summary. | Routes to Member Secretary / Chairman for final decision. |
| `AWAITING_COMPETENT_AUTHORITY` | `APPROVED` | `COMPETENT_AUTHORITY` | Final statutory concurrence signed. | Issues digital Approval Order (EoA); triggers congratulations alert to Institution; updates Compliance Passport baseline. |
| `AWAITING_COMPETENT_AUTHORITY` | `REJECTED` | `COMPETENT_AUTHORITY` | Clear statutory justification / non-compliance grounds recorded. | Issues formal Rejection Order with appeal instructions; notifies all stakeholders. |
| Any active stage | `CLOSED` | `SYSTEM_ADMIN`, `COMPETENT_AUTHORITY` | Institution withdraws application or regulatory closure order passed. | All pending reminders closed; immutable case freeze. |

---

### 3. Transition Guard Rules & Prohibitions
1. **No Self-Approval**: An institution user cannot trigger any status beyond `SUBMITTED` or `RESUBMITTED`.
2. **No Deficiency Bypass**: An application cannot transition from `UNDER_SCRUTINY` to `SCRUTINY_COMPLETED` while any deficiency remains in `OPEN` or `DEFICIENT` status.
3. **No Unscheduled EVC Completion**: An application cannot jump to `EVC_COMPLETED` without an existing scheduled visit and verified panel assignment.
4. **No Premature Final Decision**: Competent Authority cannot approve a case unless all required preceding milestones for that specific workflow template are verified.
