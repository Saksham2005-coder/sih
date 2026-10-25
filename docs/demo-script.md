# Demonstration Script — ReguFlow 360
## 5-to-7 Minute Regulatory Walkthrough
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### Demo Personas & Credentials (Development Mode)
- **Institution Admin**: `admin@apex.edu.in` / `Password123!` (Apex Institute, Western Region -> `/institution/dashboard`)
- **Compliance Officer**: `compliance@apex.edu.in` / `Password123!` (Apex Institute, Western Region -> `/institution/compliance-workspace`)
- **Regional Officer (RO)**: `ro.western@aicte.gov.in` / `Password123!` (Western Regional Office -> `/officer/regional-workspace`)
- **Bureau Officer (BO)**: `bo.approval@aicte.gov.in` / `Password123!` (Approval Bureau, New Delhi -> `/officer/bureau-workspace`)
- **Committee Member (SAC/CAC)**: `committee.member@aicte.gov.in` / `Password123!` (Standing Hearing Committee -> `/officer/committee-workspace`)
- **EVC Coordinator**: `evc.coord@aicte.gov.in` / `Password123!` (EVC Directorate, Western Roster -> `/officer/evc-workspace`)
- **Competent Authority (CA)**: `member.sec@aicte.gov.in` / `Password123!` (Member Secretary, Council -> `/officer/authority-workspace`)
- **System Administrator**: `sysadmin@aicte.gov.in` / `Password123!` (Platform Infrastructure -> `/officer/admin-workspace`)

---

### Step-by-Step Walkthrough Flow

#### Step 1: Institution Portal & Action Centre (1:00)
1. Log in as `admin@apex.edu.in` (Apex Institute).
2. Point out the **Civic Precision** design system: Midnight Ink header, Meridian Teal highlights, high information density.
3. Review the **Institution Dashboard**:
   - Application status banner (`DEFICIENCY_COMMUNICATED` on Application `AICTE-2026-EOA-98124`).
   - Action Centre highlights: "Deficiency cure required for Fire Safety NOC & Cadre Ratio".
   - Upcoming undertaking: "Barrier-Free Access Ramps due in 12 days".

#### Step 2: Deficiency Cure & Resubmission (1:15)
1. Open Application Detail for `AICTE-2026-EOA-98124`.
2. Inspect the **Deficiency Memo**:
   - Category: `INFRASTRUCTURE` — "Updated Form B Fire Safety NOC missing building stamp".
3. Click "Submit Cure Document", attach the cure file `Fire_NOC_Updated_Signed.pdf`, provide explanation notes, and submit.
4. Click "Resubmit Application to Regional Officer".
5. Observe the live state transition to `RESUBMITTED` and the new timeline entry.

#### Step 3: Officer Command Centre & Scrutiny Sign-Off (1:15)
1. Switch to Officer Portal as `ro.western@aicte.gov.in`.
2. Show the **Officer Command Centre**:
   - Pendency by stage, application ageing distribution, explainable priority ranking.
3. Open `AICTE-2026-EOA-98124` from the Application Registry.
4. Review the cured deficiency and attached document.
5. Click "Mark Deficiency Resolved" and then click "Sign-off Scrutiny Complete".
6. Observe the workflow progression to `AWAITING_EVC_SCHEDULE`.

#### Step 4: EVC Inspection Queue & Scheduling (1:00)
1. Navigate to the **EVC Queue** (as `evc.coord@aicte.gov.in` or `ro.western@aicte.gov.in`).
2. Notice `AICTE-2026-EOA-98124` is now pending scheduling.
3. Click "Schedule Inspection":
   - Set visit date (e.g. 5 days from today).
   - Mode: `PHYSICAL_ONSITE`.
   - Assign Convener: `Prof. Rajesh Sharma (IIT Bombay)` and Subject Expert: `Dr. Ananya Sen (VJTI)`.
4. Submit schedule. Confirm application moves to `EVC_SCHEDULED` and a notification is dispatched to Apex Institute.

#### Step 5: Compliance Passport & Document Expiry Tracking (1:00)
1. Switch to the **Compliance Passport** view.
2. Demonstrate continuous compliance tracking:
   - Land Lease Deed (33-Year Validity) expiring in 45 days tagged with `EXPIRING_SOON`.
   - Click "Submit Renewal Document": Upload new lease deed, showing automatic version increment (`v1 -> v2`) and SHA-256 hash preservation.
   - Show Officer verification of the renewed version.

#### Step 6: Deadline Engine & Automated Escalations (0:45)
1. Navigate to the **Escalations** console (`/officer/escalations`):
   - Review the **Deadline Engine Health** status card displaying scheduler status (`RUNNING`), 300s polling interval, lifetime scans, and last run telemetry.
   - Show an application or compliance undertaking whose cure SLA was breached:
     - Multi-tier escalation level: `ESCALATION_L1_RO`, `ESCALATION_L2_BO`, or `ESCALATION_L3_MEMBER_SEC`.
     - Recipient Role and regional scoping (`Western Region`).
     - SHA-256 idempotency key displayed to prove zero duplicate alerts across repeated runs.
2. Click **Acknowledge Escalation**: Provide official follow-up remarks in the modal and record acknowledgment, observing the status badge update and audit trail entry.
3. Switch to Institution Portal **Notifications Center** (`/institution/notifications`):
   - Filter by unread and severity (`INFO`, `WARNING`, `CRITICAL`).
   - Demonstrate clicking deep action links (e.g., "View Application" or "View Passport") taking the user directly to the affected record.
4. Demonstrate clicking "Run Deadline Scan" which idempotently executes a multi-vector pass with persistent telemetry logging.

#### Step 7: AICTE Operational Command Centre & Explainable Priority (1:00)
1. Navigate to **Officer Command Centre** (`/officer/dashboard`):
   - Review live operational overview: Applications in flight, overdue cases, unscheduled EVC inspections, and unverified document backlogs.
   - Inspect **Queue Bottlenecks**: Stage pendency ageing, EVC turnaround, and compliance verification backlogs.
   - Explore **Priority Action Queue**:
     - Note explainable priority scores (e.g. `85/100 • Critical`).
     - Click **View factors**: Open the Explainable Priority Factor Modal displaying exact point contributions (e.g. stage ageing +20 pts, uncured deficiencies +20 pts, active escalation +20 pts) and the next recommended regulatory action.
     - Demonstrate that clicking any queue row or action button navigates directly to the case dossier.
2. Open Application Detail (`/officer/applications/1`):
   - View the **Explainable Case Brief Assistant** card.
   - Review structured chronological briefing: Executive summary, deficiency resolution history, compliance passport status, and EVC inspection findings.
   - Highlight the **Suggested Administrative Draft** and explicit factual citations grounded in stored database events.
   - Point out the mandatory statutory disclaimer: Informational synthesis only; does not replace human scrutiny or statutory authority.

#### Step 8: Versioned Rule Studio & Unified Audit Explorer (0:45)
1. Navigate to **Rule Studio** (`/officer/rules`):
   - Highlight version lifecycle badges (`PUBLISHED`, `VALIDATED`, `DRAFT`) and clear illustrative demonstration labels.
   - Open **Dry-Run Simulation Sandbox**: Select a rule (e.g. `RULE_SCRUTINY_SLA`), adjust SLA thresholds, and execute simulation. Show that the simulated outcome displays SLA adherence without mutating database records or dispatching notifications.
   - Click **Publish New Version**: Enter a change reason and publish, demonstrating that the version increments and the prior configuration is archived in the immutable **Version History Ledger**.
2. Navigate to **Audit Explorer** (`/officer/audit`):
   - Search and filter by entity type, action, actor role, and free text across server-side paginated audit logs.
   - Click **Inspect**: View formatted JSON state deltas and regional/institution tenancy tags.
   - Click **Export CSV**: Download sanitized audit logs, showing that cells with formula operators (`=`, `+`, `-`, `@`) are safely escaped with single quotes to prevent CSV formula injection (DDE) attacks.

#### Step 9: APH Route Combinations & Dual Theme Accessibility (0:45)
1. **APH Workflow Route Demonstration**:
   - File application as Institution Admin: show selection among all 4 canonical APH routes:
     - `Extension of Approval (EoA) [Route: Only Scrutiny]` -> proves fast-track direct movement to Competent Authority.
     - `Establishment of New Program [Route: Scrutiny + EVC]` -> proves strict EVC completion prerequisite guard.
     - `Intake Expansion [Route: EVC + SAC/SHC Hearing]` -> proves Standing Hearing Committee deficiency return and resumption.
     - `Campus Relocation / Verification [Route: Only EVC]` -> proves direct entry from `SUBMITTED` into `AWAITING_EVC_SCHEDULE`.
2. **Civic Precision Dual-Theme (Light & Dark Mode)**:
   - Click the theme toggle icon in the navigation bar to switch between Light, Dark, and System modes.
   - Show that all 8 role dashboards, tables, dialogs, charts, and status badges preserve WCAG 2.1 AA contrast without page reload, form state loss, or wrong-theme flicker.



