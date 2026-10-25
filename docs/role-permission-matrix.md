# Role & Permission Matrix — ReguFlow 360
## Fine-Grained Role-Based Access Control (RBAC) Specification
**SIH 2026 Problem Statement 26262**  
**Version:** 2.0.0 (Phase 2 Hardened)

---

### 1. Canonical Role Definitions & Resource Scope Boundaries

ReguFlow 360 enforces an authoritative 8-role model governed centrally by `backend/app/core/rbac.py` and guarded by FastAPI dependency injection (`backend/app/core/dependencies.py`). No client-asserted role or browser payload is trusted.

| Role Identifier | Role Display Name | Scope Boundary | Canonical Responsibilities & Boundaries |
|---|---|---|---|
| `INSTITUTION_ADMIN` | Institution Administrator | Single `institution_id` | Manages regulatory filings, application creation, resubmission cures, primary institutional contacts. Restricted strictly to records where `user.institution_id == resource.institution_id`. |
| `COMPLIANCE_OFFICER` | Institution Compliance Officer | Single `institution_id` | Manages operational compliance, upload of undertakings, document renewals, and deficiency response uploads. Cannot create new applications or approve any case. |
| `REGIONAL_OFFICER` | AICTE Regional Officer (RO) | Assigned `region` | Conducts first-line scrutiny, deficiency issuance/resolution, regional inspection coordination, and compliance/document verification for institutions within authorized regional boundaries (`user.region == institution.region`). |
| `BUREAU_OFFICER` | AICTE Bureau Officer (BO) | National / Bureau-wide | Evaluates national regulatory policy, reviews completed scrutinies, handles L2 escalations, and oversees operational flows. |
| `COMMITTEE_MEMBER` | Committee Member (SAC/CAC) | Assigned Hearing Panels | Reviews complex applications, conducts hearings, uploads inspection reports and recommendations (`RECOMMENDED_APPROVAL`, etc.). Holds advisory/recommending power without executive decision-making. |
| `EVC_COORDINATOR` | EVC Roster Coordinator | Assigned Region / National | Forms expert inspection panels, schedules dates, monitors visit completion. Holds EVC operational capabilities without inheriting application approval powers. |
| `COMPETENT_AUTHORITY` | Competent Authority (Council/Advisor) | National AICTE Scope | Exercises exclusive statutory decision-making authority (`APPROVED` / `REJECTED`) and signs formal Approval Orders (EoA). |
| `SYSTEM_ADMIN` | System Administrator | Platform-wide Infrastructure | Manages platform configuration, rule definitions, user role assignments, and audit exports. **Strict Separation of Duties**: Barred from statutory approvals, scrutinies, and compliance verifications. |

---

### 2. Explicit Domain Permissions

Domain permissions are declared explicitly as constants (`Permission.*` in `backend/app/core/rbac.py`) rather than scattered string checks:

- `application.read`: View application dossiers and timelines.
- `application.create`: Create new regulatory applications.
- `application.submit`: Initial submission of completed application.
- `application.resubmit`: Resubmission after curing communicated deficiencies.
- `application.return`: Return application with itemized deficiency notice (requires mandatory remarks).
- `application.assign`: Assign scrutiny officer to an in-scope application.
- `application.scrutiny_signoff`: Sign off scrutiny as completed (blocked if open deficiencies exist).
- `application.transition`: Advance workflow stages according to authorized matrix.
- `application.record_decision`: Statutory final decision (`APPROVED` / `REJECTED`, Competent Authority only).
- `compliance.read`: View compliance undertakings and evidence.
- `compliance.submit`: Submit compliance evidence and undertaking documentation.
- `compliance.verify`: Officer verification or rejection of compliance evidence.
- `document.read`: View tracked statutory documents and version history.
- `document.upload`: Upload new document records or renewal versions.
- `document.verify`: Officer verification of renewal documents.
- `evc.view`: View EVC queues and inspection rosters.
- `evc.schedule`: Form panels and schedule inspection dates.
- `evc.report`: Upload inspection reports and recommendations.
- `rules.view`: View workflow templates and SLA rule configurations.
- `rules.manage`: Create or update versioned rules (System Admin only).
- `audit.read`: View immutable audit event logs.
- `reports.read`: View and export aggregate operational reports.
- `users.manage`: Manage accounts and role assignments.

---

### 3. Comprehensive Permissions Grid

| Permission Identifier | Inst Admin | Compliance Off. | Regional Off. | Bureau Off. | Committee Mem. | EVC Coord. | Competent Auth. | System Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `application.read` | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `application.create` | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| `application.submit` | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| `application.resubmit` | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| `application.return` | DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | DENY | DENY |
| `application.assign` | DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | DENY | DENY |
| `application.scrutiny_signoff`| DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | DENY | DENY |
| `application.transition` | **ALLOW** (Sub) | **ALLOW** (Resub)| **ALLOW** (Reg) | **ALLOW** | **ALLOW** (Recom)| **ALLOW** (EVC)| **ALLOW** (Dec) | DENY* |
| `application.record_decision`| DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** | DENY |
| `compliance.read` | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `compliance.submit` | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| `compliance.verify` | DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | DENY | DENY |
| `document.read` | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `document.upload` | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| `document.verify` | DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | DENY | DENY |
| `evc.view` | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `evc.schedule` | DENY | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | **ALLOW** | DENY | DENY |
| `evc.report` | DENY | DENY | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY |
| `rules.view` | DENY | DENY | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| `rules.manage` | DENY | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** |
| `audit.read` | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** | **ALLOW** |
| `reports.read` | **ALLOW** (Own) | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | **ALLOW** | **ALLOW** |
| `users.manage` | DENY | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** |

*\*Note: `SYSTEM_ADMIN` is barred from regulatory state mutations (`SCRUTINY_COMPLETED`, `APPROVED`, `REJECTED`, deficiency cure/resolution) under strict separation of duties, but retains administrative case closure powers for legal withdrawals.*

---

### 4. Authoritative Resource Scoping Rules

1. **Institution Tenant Scoping**:
   - `check_institution_scope(user, target_institution_id)` asserts that institutional users can never query or mutate applications, compliance undertakings, or document records belonging to other institutions.
   - Cross-tenant requests immediately abort with `HTTP 403 Forbidden` (`FORBIDDEN_INSTITUTION_ACCESS`).

2. **Regional Boundary Scoping**:
   - `check_regional_scope(user, target_region)` restricts Regional Officers to institutions located within their assigned jurisdiction (e.g. `Western`, `Northern`).
   - Any attempt by a Regional Officer to issue deficiencies, resolve deficiencies, sign off scrutiny, schedule EVC inspections, or verify compliance outside their assigned region is denied with `HTTP 403 Forbidden` (`FORBIDDEN_REGIONAL_ACCESS`).

3. **Separation of Duties & Self-Approval Prevention**:
   - Institution users can never trigger transitions beyond `SUBMITTED` or `RESUBMITTED`.
   - Regional Officers cannot issue final statutory approvals (`APPROVED` / `REJECTED`).
   - System Administrators cannot perform statutory scrutiny sign-offs or approvals.
   - Final approval/rejection is exclusively reserved for `COMPETENT_AUTHORITY`.

---

### 5. Phase 5 Command Centre Role Capabilities

| Role | Permitted Operational Scope | Command Centre Views & Actions |
|---|---|---|
| `INSTITUTION_ADMIN` / `COMPLIANCE_OFFICER` | Institution Tenancy (`institution_id`) | Own filings, required cure actions, upcoming undertaking deadlines, document validity countdowns, action center alerts. |
| `REGIONAL_OFFICER` | Regional Jurisdiction (`user.region == institution.region`) | Regional application queues, pending scrutiny dossiers, deficiency cures, EVC scheduling, regional bottlenecks and L1 escalations. |
| `BUREAU_OFFICER` | National / Inter-Regional Scope | Cross-region pendency comparisons, accumulating backlogs, regional workload imbalances, L2 escalations. |
| `COMMITTEE_MEMBER` | Assigned Hearing Panels | Cases awaiting SAC/CAC hearings, expert observation recording, formal panel recommendations. |
| `EVC_COORDINATOR` | Regional / National EVC Scope | Eligible EVC inspection queues, roster panel assignments (convener + expert), overdue visit reports. |
| `COMPETENT_AUTHORITY` | National Statutory Scope | Cases awaiting final statutory decision (`AWAITING_COMPETENT_AUTHORITY`), verified case brief evidence, Approval Order sign-off. |
| `SYSTEM_ADMIN` | Platform Infrastructure | Telemetry, distributed scheduler lease health (`SchedulerLease`), Rule Studio version publishing, formula-safe audit CSV exports. **Strictly barred from statutory approvals or compliance sign-offs.** |

---

### 6. Dedicated Role Workspaces & Navigation Mapping (Critical Remediation 1)

In Critical Remediation 1, ReguFlow 360 replaced generic dashboard views with dedicated operational workspaces for all 8 canonical roles:

| Canonical Role | Workspace Route | Primary Information Architecture & Queues | Permitted Operational Actions |
|---|---|---|---|
| `INSTITUTION_ADMIN` | `/institution/dashboard` | Institution Filings, Deficiency Return Memos, Renewal countdowns, Application timeline | Create applications, edit application info, submit cure responses, upload renewals |
| `COMPLIANCE_OFFICER` | `/institution/compliance-workspace` | Statutory Compliance Covenants Desk, SHA-256 evidence submissions, Expiring leases & NOCs | Submit compliance evidence, request lease/document renewal, track verification status |
| `REGIONAL_OFFICER` | `/officer/regional-workspace` | Regional Priority Queue (scoped to `Western`), Regional Scrutiny Dossiers, Undertaking Verifications | Conduct scrutiny, issue deficiency notices, resolve cured deficiencies, verify undertakings |
| `BUREAU_OFFICER` | `/officer/bureau-workspace` | National Filing Metrics, Cross-Regional Workload Table, Active Tier-2 Bureau Escalations | Trigger National SLA Scan, acknowledge Bureau-level escalations, analyze SLA trends |
| `COMMITTEE_MEMBER` | `/officer/committee-workspace` | Standing Committee (SAC/CAC) Hearing Queue, Assigned EVC Panels, Observation Docket | Review hearing dossiers, record committee observations, recommend approval/rejection |
| `EVC_COORDINATOR` | `/officer/evc-workspace` | Eligible Applications Awaiting EVC, Scheduled Field Visits, Completed Inspections Roster | Form inspection panels, assign Conveners & Expert panelists, schedule visit dates |
| `COMPETENT_AUTHORITY` | `/officer/authority-workspace` | Statutory Decision Queue (`AWAITING_COMPETENT_AUTHORITY`), Verified Prerequisite Audits | Issue statutory Approval Orders (EoA) or Rejection Orders with official gazette remarks |
| `SYSTEM_ADMIN` | `/officer/admin-workspace` | Live DB Ping Latency, Distributed Scheduler Leases, Rule Studio Lifecycle, Immutable Audit Log | Trigger on-demand deadline scans, publish validated rules, export formula-safe CSVs |

#### Query Cache Isolation
To prevent cross-persona data leakage in browser sessions:
1. `AuthContext.tsx` invokes `queryClient.clear()` immediately upon `login()`, `logout()`, and `switchActiveRole()`.
2. All React Query cached state is wiped before the authenticated identity transitions.
3. Every API query and mutation strictly enforces backend multi-tenant and regional scoping (`verify_institution_access`, `verify_regional_access`, `check_case_assignment`).


