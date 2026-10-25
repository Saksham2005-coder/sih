# Product Specification — ReguFlow 360
## Integrated AICTE Approval Workflow Automation, Compliance Monitoring, and Alert Management System
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0 (Phase 1 Baseline)  
**Classification:** Prototype Technical Architecture & Design Document

---

### 1. Executive Summary & Regulatory Context
Every academic cycle, the All India Council for Technical Education (AICTE) processes tens of thousands of regulatory applications across technical institutes in India. These include:
- Establishment of New Technical Institutions (EoA New)
- Extension of Approval (EoA Annual)
- Increase / Reduction in Intake
- Introduction of New Courses / Emerging Areas (AI/ML, Data Science, Green Tech)
- Closure of Programs or Institutions
- Mandatory Compliance Undertakings (land lease renewals, faculty cadre ratio, safety certificates, building occupancy, laboratory equipment, barrier-free access).

**The Challenge (PS 26262):**
Regulatory operations historically face administrative bottlenecks:
1. Fragmented application tracking across regional offices and headquarters.
2. Manual scrutiny causing opaque deficiency communication and prolonged return-resubmit cycles.
3. Lack of a unified "Compliance Passport" for time-bound undertakings and multi-year document validity (e.g. 33-year land lease or fire NOC renewals).
4. Scheduling delays and non-standardized reporting in Expert Visit Committees (EVC).
5. Absence of proactive, deterministic deadline monitoring and multi-tiered automated escalations.

**The Solution — ReguFlow 360:**
ReguFlow 360 is an integrated, role-based regulatory operations platform featuring:
- **Two major synchronized portal experiences**: Institution Portal & AICTE Officer Command Center.
- **Guarded Workflow State Machine**: Configurable routes with strict role-gated state transitions, deficiency cure loops, and immutable audit logging.
- **Institutional Compliance Passport**: Continuous compliance tracking across time-bound undertakings, evidence verification, and document expiry management.
- **EVC Queue & Inspection Lifecycle**: Transparent committee assignment, inspection scheduling, deficiency reporting, and statutory recommendations.
- **Deterministic Deadline & Escalation Engine**: Timezone-aware (Asia/Kolkata), idempotent alert scanner triggering progressive escalations (Regional Officer → Bureau Officer → Member Secretary).
- **Explainable Deadline Intelligence**: Prioritization scoring grounded in quantifiable operational urgency, time overdue, and dependency blocks.
- **Rule Studio**: Visual, versioned configuration of stage transitions, SLA thresholds, and escalation rules without code modification.

---

### 2. User Personas & Workspaces

| Persona | Portal | Workspace Scope | Key Responsibilities |
|---|---|---|---|
| **Institution Administrator** | Institution | Single Institution (`institution_id`) | Submits applications, manages institution profile, cures deficiencies, resubmits files. |
| **Compliance Officer** | Institution | Single Institution (`institution_id`) | Uploads compliance evidence for undertakings, tracks document expiries, initiates renewals. |
| **Regional Officer (RO)** | AICTE Officer | Regional Office Scope (e.g., Northern, Western) | Conducts initial scrutiny, issues formal deficiency memos, schedules regional EVC visits, reviews resubmissions. |
| **Bureau Officer (BO)** | AICTE Officer | All Regional Offices / Bureau Scope | Evaluates policy conformity, reviews scrutiny completions, handles Tier-2 escalations, manages approvals. |
| **Committee Member (SAC/CAC)** | AICTE Officer | Standing Appellate / Scrutiny Committee | Reviews complex cases, hears appeals, assesses EVC reports, delivers formal recommendations. |
| **EVC Coordinator** | AICTE Officer | Regional & National EVC Rosters | Forms inspection panels, coordinates visit logistics, monitors inspection deadlines, verifies EVC reports. |
| **Competent Authority (CA)** | AICTE Officer | Apex Regulatory Scope (Council/Advisor) | Final statutory approval, rejection, or issuance of formal Approval Letters (EoA). |
| **System Administrator** | AICTE Officer | Global System Scope | Manages users, assigns roles, configures Rule Studio templates, monitors system audit trail. |

---

### 3. Core Functional Modules

#### 3.1 Dual-Portal Unified Core
- Single backend API and single database instance.
- Frontend delivers contextual role-driven workspaces:
  - **Institution Portal**: My Applications, Action Centre, Compliance Passport, Documents & Renewals, Notifications, Submission History.
  - **Officer Portal**: Command Centre, Application Registry, EVC Queue, Compliance Verification, Escalations, Reports, Rule Studio, Audit Trail.

#### 3.2 Guarded Workflow Engine
- Supports distinct regulatory application categories:
  - `EOA_ANNUAL`: Extension of Approval (Fast-track scrutiny).
  - `NEW_INSTITUTION`: Comprehensive scrutiny, mandatory EVC, SAC/CAC committee hearing.
  - `INTAKE_VARIATION`: Scrutiny of infrastructure norms, cadre ratio, and lab facilities.
  - `CLOSURE_PROGRAM`: Scrutiny of student migration, faculty reallocations, and land release.
- Deterministic transitions guarded by role authorization, required deficiency checks, and mandatory document validation.

#### 3.3 Institutional Compliance Passport
- Continuous compliance management decoupled from application filing deadlines.
- Tracks:
  - **Time-bound Undertakings**: E.g., "Installation of specialized Robotics Lab by Oct 31", "Fire NOC renewal compliance by Nov 15".
  - **Prescribed Documents**: Land Title / 33-Year Lease Deed, Building Plan Approval, Structural Stability Certificate, Pollution Control NOC, AICTE-approved Affiliation.
  - **Document Versioning**: SHA-256 hash calculation, version incrementing, metadata tagging, and verification audit trail.

#### 3.4 EVC Management System
- Manages Expert Visit Committee inspection queues.
- Panel assignment (Convener, Subject Expert, Architect/Finance Member).
- Visit date scheduling with automatic conflict checks.
- On-site / Virtual verification report submission with photo/document upload references.
- Transparent recommendation outcomes: Recommended Approval, Recommended with Deficiency, Recommended Rejection.

#### 3.5 Deterministic Deadline & Escalation Engine
- Timestamps stored in UTC, evaluated and displayed in `Asia/Kolkata`.
- Idempotent background scan evaluating:
  - Application Scrutiny SLA (e.g., 7 days)
  - Deficiency Cure SLA (e.g., 15 days)
  - EVC Scheduling & Report Submission SLA (e.g., 10 days)
  - Undertaking Due Dates & Document Expiry Warning Windows (e.g., 30, 15, 7 days prior).
- Multi-tier Escalation:
  - Tier 1: Warning notification to Institution & RO.
  - Tier 2: Escalation to Bureau Officer when SLA breached by > 3 days.
  - Tier 3: Critical alert to Member Secretary / Competent Authority when SLA breached by > 7 days.

#### 3.6 AICTE Operational Command Centre & Role Dashboards
- Unified, role-scoped command center answering operational urgency, bottleneck, and queue ageing questions.
- Role-specific filtering: Regional Officers are scoped to their assigned regional jurisdiction; Institution users are scoped to their institution; Bureau Officers and System Admins access national aggregates.
- Live bottleneck analytics: Average stage ageing, unscheduled EVC inspections, unverified document backlogs, and repeated return cycles.
- Real-time operational activity stream capturing recent workflow transitions, deficiency cures, compliance verifications, and alert acknowledgments.

#### 3.7 Explainable Priority Intelligence
- Computes a deterministic operational urgency score (0–100) combining:
  - Stage pendency and configured SLA ageing.
  - Open, uncured deficiencies awaiting institutional action.
  - Criticality tier of the current workflow stage (e.g. Competent Authority milestone).
  - Institutional compliance breaches (overdue undertakings and expiring statutory documents).
  - Active Level 2 / Level 3 alert escalations and repeated deficiency return cycles.
- Displays full plain-language factor breakdown modal with points contribution and next recommended regulatory action.
- Invariant: Operational priority index prioritizes officer review queues and never mutates statutory application decisions.

#### 3.8 Robust Rule Studio & Policy Simulation
- Versioned rule lifecycle: `DRAFT`, `VALIDATED`, `PUBLISHED`, `RETIRED`.
- Multi-field validator checking schema syntax, positive integer SLAs, canonical roles, and threshold ordering.
- Dry-run simulation sandbox evaluating hypothetical scenarios or case IDs without database mutation or alert dispatch.
- Immutable publication ledger (`rule_version_history`) archiving previous configuration snapshots with change reasons.

#### 3.9 Unified Audit Explorer & Operational Analytics
- Server-side filterable audit trail supporting entity, action, actor role, and free-text search across paginated datasets.
- Formula-injection safe CSV export mitigating DDE risks by prepending `'` to sensitive operator characters.
- Comprehensive operational reports: Stage SLA adherence turnaround percentages and EVC inspection mode/recommendation analytics.
- Evidence-grounded Case Brief Assistant: Deterministic synthesis of case dossiers with source citations and strict regulatory non-mutation disclaimers.

