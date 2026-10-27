# ReguFlow 360 — Evaluator & Judge Walkthrough Guide
## 5-to-7 Minute Guided Regulatory Demonstration & Live Workflow Explorer
**SIH 2026 — AICTE Problem Statement 26262**  
**Working Product Name:** ReguFlow 360  
**Target Environment:** Prototype Sandbox / Local Development (`ENVIRONMENT=development`, `DEMO_MODE=true`)  
**Production Invariant:** All demo persona quick-switches, synthetic scenarios, and state reset triggers fail closed with HTTP 403 Forbidden when `DEMO_MODE=false`.

---

### Executive Overview for Evaluators

ReguFlow 360 is an integrated, enterprise-grade AICTE approval workflow automation, compliance monitoring, deadline enforcement, EVC scheduling, document validity, and alert escalation platform.

To enable hackathon judges and regulatory evaluators to directly inspect the authentic engineering behind the platform—rather than clicking through disconnected prototypes—ReguFlow 360 features a dedicated **Judge Demonstration Centre & Live Workflow Explorer** mounted directly at:
```
/demo/explorer
```
This guided demonstration layer queries genuine backend database records, exercises real state machine transitions, respects role-based regional jurisdictions, and provides deterministic explainability for every regulatory score.

---

### Key Demo Identities & Authorized Personas

| Role | Name | Email | Default Password | Workspace Route | Authorized Jurisdiction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Institution Admin** | Dr. Arvind Kulkarni | `admin@apex.edu.in` | `Password123!` | `/institution/dashboard` | Apex Institute of Technology & Management (Western Region) |
| **Compliance Officer** | Prof. Sunita Rao | `compliance@apex.edu.in` | `Password123!` | `/institution/compliance-workspace` | Apex Institute (Evidence Cures & Continuous Passport) |
| **Regional Officer (RO)** | Shri Suresh Deshmukh | `ro.western@aicte.gov.in` | `Password123!` | `/officer/regional-workspace` | Western Region (Maharashtra, Goa, Gujarat) |
| **Bureau Officer (BO)** | Dr. Meenakshi Raman | `bo.approval@aicte.gov.in` | `Password123!` | `/officer/bureau-workspace` | National Approval Bureau (New Delhi HQ) |
| **EVC Coordinator** | Dr. Vikram Sethi | `evc.coord@aicte.gov.in` | `Password123!` | `/officer/evc-workspace` | Western Region EVC Panel Scheduling & COI Directorate |
| **Committee Member** | Prof. R. C. Mathur | `committee.member@aicte.gov.in` | `Password123!` | `/officer/committee-workspace` | Standing Hearing Committee (SAC/CAC) & Mobile Field Inspection |
| **Competent Authority** | Prof. Rajive Kumar | `member.sec@aicte.gov.in` | `Password123!` | `/officer/authority-workspace` | Member Secretary, AICTE Council (Statutory Decision Exclusivity) |
| **System Admin** | Er. Deepak Verma | `sysadmin@aicte.gov.in` | `Password123!` | `/officer/admin-workspace` | Platform Telemetry, Rule Studio & Distributed Schedulers |

---

### The 5 Curated Regulatory Scenarios

#### Scenario 1: New Technical Institution — Mandatory EVC Inspection Track
- **Target Application:** `AICTE-2026-NEW-44102` (Application ID: 2)
- **Institution:** Apex Institute of Technology & Management (Western Region)
- **Route:** `SCRUTINY_EVC` (`NEW_INSTITUTION`)
- **Starting Stage:** `AWAITING_EVC_SCHEDULE` (Scrutiny completed; EVC required)
- **Recommended Persona:** Dr. Vikram Sethi (`evc.coord@aicte.gov.in` — EVC Coordinator)
- **Deep Link:** `/officer/evc`
- **What Evaluators Observe:**
  1. The application requires mandatory physical on-site verification as a new institution approval prerequisite.
  2. The EVC Coordinator can run an **Explainable Conflict-of-Interest (COI)** check against registered experts.
  3. The COI engine detects parent trusts, alma maters, and the 3-year illustrative cooling-off rule, categorizing conflicts transparently.
  4. Override requires substantive written justification (`Permission.EVC_COI_OVERRIDE`), and logs an immutable audit event.
  5. Only invited experts can accept/decline; mobile field evidence records browser coordinates, SHA-256 hashes, and registered file URLs.

#### Scenario 2: Annual Extension of Approval (EOA) — Scrutiny-Only Track
- **Target Application:** `AICTE-2026-EOA-55910` (Application ID: 3)
- **Institution:** Northern Institute of Engineering & Research (Northern Region)
- **Route:** `ONLY_SCRUTINY` (`EOA_ANNUAL`)
- **Starting Stage:** `UNDER_SCRUTINY`
- **Recommended Persona:** Shri Suresh Deshmukh (`ro.western@aicte.gov.in`)
- **Deep Link:** `/officer/applications/3`
- **What Evaluators Observe:**
  1. In the **Guided Lifecycle Stepper**, physical EVC stages are visibly tagged as **`NOT APPLICABLE`**.
  2. The system displays the statutory justification: *"Statutory Exemption under AICTE APH Chapter II, Section 2.4 — Regular annual EOA renewal does not require physical EVC inspection"*.
  3. Scrutiny sign-off with zero open deficiencies advances directly to `AWAITING_COMPETENT_AUTHORITY` without an EVC loop.
  4. Regional Officer access to other regions fails closed (attempting to mutate Northern records with Western RO is strictly forbidden).

#### Scenario 3: Deficiency Communication, Institutional Cure & Resubmission Return Loop
- **Target Application:** `AICTE-2026-EOA-98124` (Application ID: 1)
- **Institution:** Apex Institute of Technology & Management (Western Region)
- **Route:** `EOA_ANNUAL`
- **Starting Stage:** `DEFICIENCY_COMMUNICATED` (Priority Score: 75/100)
- **Recommended Persona:** Dr. Arvind Kulkarni (`admin@apex.edu.in` — Institution Admin)
- **Deep Link:** `/institution/applications/1`
- **What Evaluators Observe:**
  1. 2 active deficiency items: Form B Fire Safety NOC missing municipal fire brigade stamp, and Computer Engineering Cadre Ratio at 1:2.4.
  2. Institution Admin opens the application, submits documentary cures and affidavits, and clicks **"Resubmit Application"**.
  3. The status machine advances to `RESUBMITTED` and routes the case back to Regional Scrutiny without resetting the whole workflow.
  4. Click **"Safe Reset Scenario"** in the Demo Centre to restore the initial `DEFICIENCY_COMMUNICATED` state with open deficiencies, while preserving the entire audit trail.

#### Scenario 4: Continuous Compliance Passport & Multi-Tier SLA Deadline Escalation
- **Target Application:** `AICTE-2026-EOA-98124` / Document Record #1
- **Institution:** Apex Institute of Technology & Management
- **Target Document:** 33-Year Registered Land Lease Deed (Khasra No. 412/1)
- **Starting State:** Valid for 33 years, expiring in 45 days (`EXPIRING_SOON`)
- **Recommended Persona:** Prof. Sunita Rao (`compliance@apex.edu.in` — Compliance Officer)
- **Deep Link:** `/officer/escalations`
- **What Evaluators Observe:**
  1. Continuous compliance monitoring continues even after statutory approval.
  2. The background deadline engine scans document validity and compliance undertakings every 60 seconds (coordinated via `scheduler_leases` database locks).
  3. When an SLA or validity window breaches, the engine generates an escalation (`ESCALATION_L1_RO` -> `ESCALATION_L2_BO` -> `ESCALATION_L3_MEMBER_SEC`).
  4. Every alert uses a database idempotency key (`APP:1:SLA_OVERDUE:15:ESCALATION_L1_RO`) ensuring zero duplicate alerts across repeated runs.
  5. The institution uploads a renewal document: version increments (`v1 -> v2`), previous version is preserved, and SHA-256 hash is computed.

#### Scenario 5: Apex Competent Authority — Statutory Order Decision Desk
- **Target Application:** `AICTE-2026-DEC-33019` (Application ID: 6)
- **Institution:** Apex Institute of Technology & Management
- **Route:** `INTAKE_VARIATION`
- **Starting Stage:** `AWAITING_COMPETENT_AUTHORITY` (Priority Score: 90/100)
- **Recommended Persona:** Prof. Rajive Kumar (`member.sec@aicte.gov.in` — Competent Authority)
- **Deep Link:** `/officer/authority-workspace`
- **What Evaluators Observe:**
  1. **Statutory Decision Exclusivity Invariant**: Only the Competent Authority role has legal authority to issue binding Approval or Rejection orders.
  2. Attempting to approve as Regional Officer or System Admin fails with HTTP 403 Forbidden.
  3. Clicking **"Issue Statutory Approval Order"** generates a tamper-evident digital order with:
     - Prototype digital signature state
     - Indian IT Act 2000 Section 65B legal disclosure
     - Cryptographic SHA-256 artifact hash
     - Public verification token and QR code URL (`/verify-order/:token`)
  4. Evaluators can scan or click the verification link to inspect third-party unauthenticated proof of authenticity.

---

### Step-by-Step 5-to-7 Minute Presentation Script

#### Minute 0:00 – 1:00 | System Architecture & Civic Precision Design
1. Open the browser to `http://localhost:5173/demo/explorer`.
2. Introduce the **Civic Precision** theme: Midnight Ink header, Meridian Teal operational accents, Cool Porcelain canvas, high information density.
3. Toggle one-click **Dark Mode** via the sun/moon icon in the header, showing high-contrast obsidian canvas and accessible WCAG-compliant slate tokens.
4. Point out the **Distributed System Telemetry** strip: background scheduler state (`RUNNING`, 60s scan interval), last deadline scan execution time, and transactional notification transport.

#### Minute 1:00 – 2:30 | Live Regulatory Lifecycle & Statutory Differentiation (Scenario 1 & 2)
1. Select **Track #1 (New Institution with Mandatory EVC)**:
   - Point out in the **Guided Lifecycle Stepper** that EVC scheduling is mandatory.
   - Switch to **Track #2 (Annual EOA Scrutiny-Only Track)**:
   - Highlight the **`NOT APPLICABLE`** badge on EVC stages with the statutory citation: *AICTE APH Chapter II, Section 2.4*.
   - Explain: *"ReguFlow 360 models statutory differentiation in code. It does not treat every application identically, avoiding redundant inspections for low-risk annual renewals while enforcing physical checks on new campuses."*
2. Switch to the **Live Interactive Workflow Map** tab:
   - Inspect the visual state graph.
   - Click on the active node to inspect SLA ceilings and permitted actor roles.
   - Point out the **Deficiency Return Loop** connecting Scrutiny Memo → Institutional Cure → Scrutiny Verification.

#### Minute 2:30 – 4:00 | Deficiency Cure & Deterministic Priority Engine (Scenario 3)
1. Select **Track #3 (Deficiency Cure Loop)** on `AICTE-2026-EOA-98124`.
2. Open the **Explainability Panel**:
   - Show the **Deterministic Priority Score (75/100)**: Point out the line-by-line additive attribution (`+20 Stage pendency`, `+25 Unresolved deficiencies`, `+15 Deficiency window`).
   - Highlight the explicit invariant: *"This is a deterministic mathematical triage score, not an AI hallucination, and it never mutates statutory approval status."*
3. Click **"Open in Operational Workspace"** (`/institution/applications/1`):
   - Review the deficiency memo (Fire Safety NOC Form B seal, Cadre ratio).
   - Enter cure remarks, upload cure document, and submit resubmission.
   - Watch the application advance to `RESUBMITTED`.
4. Return to `/demo/explorer` and click **"Safe Reset Scenario"**:
   - The application returns to `DEFICIENCY_COMMUNICATED` with open deficiencies restored.
   - Point out that the immutable audit ledger retained all cure and reset events without data loss.

#### Minute 4:00 – 5:30 | EVC Conflict-of-Interest & Geotagged Field Evidence (Scenario 1)
1. In the Demo Persona switcher, quick-switch to **Dr. Vikram Sethi (EVC Coordinator)**.
2. Navigate to `/officer/evc`:
   - Open inspection scheduling for `AICTE-2026-NEW-44102`.
   - Run the **Explainable Conflict-of-Interest (COI)** check against candidate experts.
   - Show the COI assessment modal: explainable rule breakdown (Parent trust conflict, Alma mater conflict, Cooling-off period).
   - Propose an expert with conflict override: note mandatory justification requirement and audit logging.
3. Switch persona to **Prof. R. C. Mathur (Committee Member / Expert)**:
   - Open `/officer/evc/field/1`:
   - Demonstrate geolocation check-in (browser GPS with accuracy radius, or authorized manual fallback).
   - Show field evidence capture with SHA-256 integrity hashing.

#### Minute 5:30 – 7:00 | Apex Competent Authority Statutory Order & Public Verification (Scenario 5)
1. Quick-switch to **Prof. Rajive Kumar (Competent Authority)**.
2. Navigate to `/officer/authority-workspace`:
   - Open application `AICTE-2026-DEC-33019` waiting for statutory decision.
   - Review the complete dossier, EVC report recommendation, and scrutiny findings.
   - Click **"Issue Statutory Approval Order"**.
3. View the generated digital order:
   - Legal notice: *Indian Information Technology Act 2000 Section 65B compliance*.
   - Tamper-evident cryptographic SHA-256 checksum.
   - Public QR verification token.
4. Click **"Verify Order Authenticity"** (navigates to `/verify-order/:token`):
   - Proves unauthenticated third parties, state higher education departments, and affiliating universities can independently verify validity without an AICTE login.
5. Conclude: *"ReguFlow 360 delivers an end-to-end, privacy-hardened, explainable, and multi-tenant regulatory system that eliminates administrative bottlenecks while maintaining statutory integrity."*

---

### Failure Recovery & Troubleshooting Procedures

| Symptom | Root Cause | Immediate Recovery Action |
| :--- | :--- | :--- |
| **Scenario data was modified during previous trial** | An evaluator advanced the workflow stage during interactive testing. | Click the **"Safe Reset Scenario"** button in `/demo/explorer`. This restores the target application to its starting stage without deleting other institutional data or audit trails. |
| **"Demo persona switcher is disabled" (HTTP 403)** | `DEMO_MODE=false` in environment configuration. | Verify `.env` has `DEMO_MODE=true` and `ENVIRONMENT=development`. In production, this fails closed by security design. |
| **"Session expired or unauthorized" (HTTP 401)** | Token expiration or persona session mismatch. | Click the Demo Persona dropdown in the header and re-select the persona for your current scenario. |
| **Background deadline scan shows "Simulated Sandbox"** | CDAC SMS Gateway or real SMTP credentials not configured. | This is truthful runtime reporting. In development, emails are written to the transactional outbox and simulated in the sandbox. |
| **EVC Geolocation prompt denied in browser** | Browser location permissions blocked for localhost. | Use the built-in **"Manual Officer Override"** button on the Mobile Field Inspection page, providing the mandatory audit reason. |
| **Complete database re-initialization needed** | Accidental local database corruption. | Restart backend with development seed: `python -c "from app.core.database import Base, engine; from app.seed.seed_data import seed_database; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); seed_database()"` |
