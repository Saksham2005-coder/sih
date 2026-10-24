# Role & Permission Matrix — ReguFlow 360
## Fine-Grained Role-Based Access Control (RBAC) Specification
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. Role Definitions & Scopes

| Role Identifier | Role Display Name | Scope Boundary | Description |
|---|---|---|---|
| `INSTITUTION_ADMIN` | Institution Administrator | Single `institution_id` | Manages regulatory filings, primary contacts, and institutional profile. |
| `COMPLIANCE_OFFICER` | Institution Compliance Officer | Single `institution_id` | Manages operational compliance, upload of undertakings and document renewals. |
| `REGIONAL_OFFICER` | AICTE Regional Officer (RO) | Assigned `region` (e.g. Northern, Western) | Conducts first-line scrutiny, deficiency issuance, regional inspection coordination. |
| `BUREAU_OFFICER` | AICTE Bureau Officer (BO) | National / Bureau-wide | Evaluates regulatory policy, reviews completed scrutinies, handles L2 escalations. |
| `COMMITTEE_MEMBER` | Committee Member (SAC/CAC) | Assigned Hearing Panels | Reviews complex applications, hears institutional appeals, assesses EVC reports. |
| `EVC_COORDINATOR` | EVC Roster Coordinator | Assigned Region / National | Forms expert inspection panels, schedules dates, monitors visit completion. |
| `COMPETENT_AUTHORITY` | Competent Authority (Council/Advisor)| National AICTE Scope | Issues final statutory approval or rejection orders, signs Approval Letters (EoA). |
| `SYSTEM_ADMIN` | System Administrator | Platform-wide | Manages system accounts, Rule Studio templates, system audits, and engine configurations. |

---

### 2. Comprehensive Permissions Grid

| Resource Action | Inst Admin | Compliance Off. | Regional Off. | Bureau Off. | Committee Mem. | EVC Coord. | Competent Auth. | System Admin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Applications** | | | | | | | | |
| Create New Application | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY | DENY |
| View Own Institution Apps | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| View Applications in Region | DENY | DENY | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Assign Scrutiny Officer | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | **ALLOW** |
| Issue Deficiency Notice | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY |
| Submit Deficiency Cure | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| Sign-off Scrutiny Complete | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY |
| Final Statutory Approval | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** | DENY |
| Final Statutory Rejection | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** | DENY |
| **Compliance Passport** | | | | | | | | |
| View Institution Undertakings | **ALLOW** | **ALLOW** | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Submit Undertaking Evidence | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| Verify Compliance Evidence | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY |
| Reject Compliance Evidence | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY |
| **Documents & Expiries** | | | | | | | | |
| View Document History | **ALLOW** | **ALLOW** | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Upload Renewal Document | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY | DENY | DENY |
| Verify Document Renewal | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | DENY | DENY |
| **EVC Management** | | | | | | | | |
| View EVC Schedule | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** (Assigned)| **ALLOW** | **ALLOW** | **ALLOW** |
| Assign Inspection Panel | DENY | DENY | **ALLOW** | **ALLOW** | DENY | **ALLOW** | DENY | **ALLOW** |
| Set Inspection Date | DENY | DENY | **ALLOW** | **ALLOW** | DENY | **ALLOW** | DENY | **ALLOW** |
| Upload Visit Report & Rec. | DENY | DENY | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY |
| **Alerts & Deadlines** | | | | | | | | |
| View Scoped Alerts | **ALLOW** (Own) | **ALLOW** (Own) | **ALLOW** (Reg) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Trigger Manual Deadline Scan| DENY | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** |
| Acknowledge Escalation | DENY | DENY | **ALLOW** | **ALLOW** | DENY | DENY | **ALLOW** | **ALLOW** |
| **Rule Studio & System** | | | | | | | | |
| View Active Rules | DENY | DENY | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Create/Edit Rule Version | DENY | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** |
| View Full Audit Trail | DENY | DENY | DENY | DENY | DENY | DENY | **ALLOW** | **ALLOW** |
| Export Authorized Reports | **ALLOW** (Own) | DENY | **ALLOW** (Reg) | **ALLOW** | DENY | DENY | **ALLOW** | **ALLOW** |

---

### 3. Backend Authorization Enforcement Policy
- Built using FastAPI dependency injection (`get_current_active_user`, `require_roles([...])`, `require_institution_access(institution_id)`).
- Every mutation checks:
  1. Authenticated user validity & active token.
  2. Role membership in authorized set.
  3. Resource tenant matching: `user.institution_id == target.institution_id` for institutional users, and `user.region == target.region` for Regional Officers.
- Violations raise immediate `HTTP 403 Forbidden` and log a security audit event.
