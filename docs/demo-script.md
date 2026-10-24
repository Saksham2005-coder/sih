# Demonstration Script — ReguFlow 360
## 5-to-7 Minute Regulatory Walkthrough
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### Demo Personas & Credentials (Development Mode)
- **Institution Admin**: `admin@apex.edu.in` / `Password123!` (Apex Institute of Technology, Mumbai — Western Region)
- **Regional Officer (RO)**: `ro.western@aicte.gov.in` / `Password123!` (Western Regional Office, Bhopal/Mumbai)
- **EVC Coordinator**: `evc.coord@aicte.gov.in` / `Password123!` (AICTE HQ / Western Roster)
- **Bureau Officer (BO)**: `bo.approval@aicte.gov.in` / `Password123!` (Approval Bureau, New Delhi)
- **Competent Authority (CA)**: `member.sec@aicte.gov.in` / `Password123!` (Member Secretary, AICTE Apex)

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
1. Navigate to the **Escalations** console.
2. Show an application whose cure SLA was breached:
   - Trigger level: `ESCALATION_L2_BO`.
   - Recipient: Bureau Officer.
   - Idempotency key displayed to prove non-duplication.
3. Demonstrate clicking "Run Deadline Scan" which re-evaluates all SLA clocks idempotently.

#### Step 7: Rule Studio & Audit Trail (0:45)
1. Visit **Rule Studio**: Show configurable SLA thresholds, stage progression rules, and version control.
2. Visit **Audit Trail**: Show immutable, filterable audit log capturing every single action from Steps 1–6 with actor names, roles, timestamps, and state changes.
