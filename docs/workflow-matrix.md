# Workflow Transition Matrix — ReguFlow 360
## Guarded Regulatory State Machine Specification
**SIH 2026 Problem Statement 26262**  
**Version:** 2.0.0 (Phase 2 Hardened)

---

### 1. Illustrative Workflow Routes & Regulatory Stages
Regulatory processing in AICTE varies depending on application type. ReguFlow 360 supports configurable workflow templates:
1. `EOA_ANNUAL`: Standard Extension of Approval (streamlined scrutiny, conditional EVC only if red-flagged).
2. `NEW_INSTITUTION`: Comprehensive scrutiny, mandatory EVC panel inspection, mandatory SAC/CAC committee review, Competent Authority approval.
3. `INTAKE_VARIATION`: Land/Cadre scrutiny, infrastructure check, optional EVC.
4. `CLOSURE_PROGRAM`: Scrutiny of no-objection certificates, student relocation plan, financial liability settlement.

---

### 2. Guarded State Machine Transitions & Concurrency Guards

All transitions are strictly mediated by `WorkflowEngine.transition()` (`backend/app/services/workflow_engine.py`) within an atomic database transaction.

| From Stage | Allowed To Stage | Permitted Roles | Preconditions & Validation Rules | Side Effects |
|---|---|---|---|---|
| `DRAFT` | `SUBMITTED` | `INSTITUTION_ADMIN` | All mandatory application sections complete; fee verified. | Records `SUBMITTED` timeline event; sets scrutiny SLA clock (7 days); triggers Tier-1 notification for Regional Office. |
| `SUBMITTED` | `UNDER_SCRUTINY` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | Case assigned to designated Scrutiny Officer within matching region (`verify_regional_access`). | Updates stage; assigns `scrutiny_officer_id`; records audit event. |
| `UNDER_SCRUTINY` | `DEFICIENCY_COMMUNICATED` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | **Mandatory Remarks**: Non-empty return reason required. Itemized deficiency must be logged. | Sets cure SLA deadline (15 days); generates urgent alert to Institution Admin & Compliance Officer. |
| `DEFICIENCY_COMMUNICATED` | `RESUBMITTED` | `INSTITUTION_ADMIN`, `COMPLIANCE_OFFICER` | **Deficiency Guard**: All open deficiencies must have uploaded cure documents and remarks. | Resets scrutiny SLA clock; notifies assigned Regional Officer; records timeline event. |
| `RESUBMITTED` | `UNDER_SCRUTINY` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | Regional officer acknowledges receipt of resubmitted evidence in authorized region. | Timeline updated to scrutiny in progress. |
| `UNDER_SCRUTINY` | `SCRUTINY_COMPLETED` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | **Zero Open Deficiencies**: All logged deficiencies must be marked `"CURED"` or `"WAIVED"`. | Scrutiny sign-off recorded; if route specifies mandatory EVC, unlocks `AWAITING_EVC_SCHEDULE`. |
| `SCRUTINY_COMPLETED` | `AWAITING_EVC_SCHEDULE` | `REGIONAL_OFFICER`, `BUREAU_OFFICER` | Triggered when route requires physical/virtual inspection (e.g. `NEW_INSTITUTION`). | Application pushed to EVC Queue; generates scheduling SLA alert for EVC Coordinator. |
| `AWAITING_EVC_SCHEDULE` | `EVC_SCHEDULED` | `EVC_COORDINATOR`, `REGIONAL_OFFICER` | Inspection date set in future; panel convener and expert assigned. | Generates formal inspection notice to Institution; schedules EVC deadline monitor. |
| `EVC_SCHEDULED` | `EVC_COMPLETED` | `EVC_COORDINATOR`, `COMMITTEE_MEMBER` | Inspection report uploaded, signed, and formal recommendation recorded. | Inspection report linked to case; unlocks committee review stage. |
| `EVC_COMPLETED` | `AWAITING_SAC_CAC_REVIEW` | `BUREAU_OFFICER`, `REGIONAL_OFFICER` | Scrutiny & EVC reports verified complete. | Enters Standing Scrutiny / Appellate Committee queue. |
| `AWAITING_SAC_CAC_REVIEW` | `AWAITING_COMPETENT_AUTHORITY` | `COMMITTEE_MEMBER`, `BUREAU_OFFICER` | Committee minutes recorded with resolution summary. | Routes to Member Secretary / Chairman for final statutory decision. |
| `AWAITING_COMPETENT_AUTHORITY` | `APPROVED` | `COMPETENT_AUTHORITY` | Final statutory concurrence signed. Preceding scrutiny and review verified. | Issues digital Approval Order (EoA); triggers congratulations alert; updates Compliance Passport baseline. |
| `AWAITING_COMPETENT_AUTHORITY` | `REJECTED` | `COMPETENT_AUTHORITY` | **Mandatory Remarks**: Clear statutory justification and non-compliance grounds recorded. | Issues formal Rejection Order with appeal instructions; notifies all stakeholders. |
| Any active stage | `CLOSED` | `COMPETENT_AUTHORITY`, `SYSTEM_ADMIN` | **Mandatory Remarks**: Formal closure grounds recorded (e.g., institutional withdrawal). | All pending reminders closed; immutable case freeze. |

---

### 3. State Machine Invariants & Hardened Guards

1. **Optimistic Concurrency Control**:
   - `applications.version` integer column is incremented monotonically with each transition.
   - Callers submit `expected_version`. If a concurrent modification occurred, `HTTP 409 Conflict` is returned with code `STALE_STATE_CONFLICT`, preventing race conditions and silent state overrides.
2. **Atomic Audit Trail & Notification Dispatch**:
   - The workflow transition, application version increment, timeline stage record, audit event, and notification are committed within the same database transaction.
   - If audit creation fails, the entire transition rolls back safely.
3. **Strict Separation of Duties**:
   - Institution users are strictly barred from advancing applications beyond `SUBMITTED` or `RESUBMITTED`.
   - `SYSTEM_ADMIN` is barred from statutory scrutiny sign-offs, deficiency issuance, and approval decisions.
   - `COMPETENT_AUTHORITY` alone holds approval authority.
4. **Mandatory Deficiency Gate**:
   - An application cannot transition from `UNDER_SCRUTINY` to `SCRUTINY_COMPLETED` while any deficiency remains in `"OPEN"` status (`OPEN_DEFICIENCIES_EXIST`).
   - An application cannot transition from `DEFICIENCY_COMMUNICATED` to `RESUBMITTED` while deficiencies remain uncured (`UNCURED_DEFICIENCIES_REMAIN`).
5. **Mandatory Justification for Adverse Decisions**:
   - Transitions to `DEFICIENCY_COMMUNICATED`, `REJECTED`, or `CLOSED` require a non-empty `remarks` payload (`REMARKS_REQUIRED`).
6. **Mandatory EVC Completion Gate**:
   - For applications requiring an inspection (`workflow_template_code == 'NEW_INSTITUTION'` or `evc_required=True`), the guarded transition engine blocks progression to review or final decision stages (`AWAITING_SAC_CAC_REVIEW`, `AWAITING_COMPETENT_AUTHORITY`, `APPROVED`) until an official inspection report has been submitted and the application stage has reached `EVC_COMPLETED`.

