# ReguFlow 360 (आवेदनसेतु | AvedanSetu)

### Integrated AICTE Approval Workflow Automation, Compliance Monitoring, Document Validity & Alert Management System

ReguFlow 360 (branded as **आवेदनसेतु | AvedanSetu**) is an integrated, enterprise-grade regulatory workflow automation and continuous compliance monitoring platform engineered for the **All India Council for Technical Education (AICTE)**. Built around the mandate of **SIH 2026 Problem Statement 26262**, the platform unites the entire technical education regulatory lifecycle—spanning application routing, route-aware scrutiny, deficiency cure loops, Expert Visiting Committee (EVC) panel formation with automated Conflict-of-Interest (COI) checks, mobile-first geotagged field inspections, multi-year Document Vault validity tracking (33-year land leases, fire NOCs, building stability certificates), time-bound compliance undertakings, automated multi-tier deadline escalations, and cryptographically verifiable statutory decision orders—into a single, highly auditable, role-governed digital command ecosystem.

---

## Project & Team Information

| Field | Submission Details |
|---|---|
| **Problem Statement ID** | **26262** |
| **Problem Statement Title** | **Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System** |
| **Organisation** | **All India Council for Technical Education (AICTE)** |
| **Department / Bureau** | **Approval Bureau & Regulation Bureau** |
| **Theme** | **Smart Automation** |
| **Category** | **Software** |
| **Project Name** | **ReguFlow 360 (आवेदनसेतु \| AvedanSetu)** |
| **Team Name** | **TechTitans 2.0** |
| **Team ID** | **197859** |
| **Institute** | **KIET Deemed to be University, Delhi-NCR, Ghaziabad** |
| **Team Members** | 1. **Ayush Soni** (Team Leader)<br>2. **Saksham Gupta**<br>3. **Ankit Kumar**<br>4. **Pranjali Sehrawat**<br>5. **Diya Kataria**<br>6. **Diksha Verma** |
| **Project Repository** | [https://github.com/Saksham2005-coder/sih](https://github.com/Saksham2005-coder/sih) |
| **Live Web Portal (Vercel)** | [https://avedansetu.vercel.app](https://avedansetu.vercel.app) |
| **Production API & OpenAPI Docs (Render)** | [https://reguflow-backend.onrender.com/docs](https://reguflow-backend.onrender.com/docs) |
| **Live Telemetry & Diagnostics Probe** | [https://reguflow-backend.onrender.com/api/health](https://reguflow-backend.onrender.com/api/health) |
| **Demonstration Video** | [https://github.com/Saksham2005-coder/sih#demonstration-video](https://github.com/Saksham2005-coder/sih#demonstration-video) |
| **Document Version** | **Version 1.0 (Final SIH Technical Dossier)** |
| **Submission Date** | **27 October 2026** |

> **Prototype & Statutory Disclosure:** ReguFlow 360 (*आवेदनसेतु*) is an advanced, hardened technical prototype developed by Team TechTitans 2.0 for the Smart India Hackathon (SIH 2026). It demonstrates a fully working, explainable, and multi-tenant operational layer. Demo data, simulated institutional profiles, and statutory SLA thresholds are illustrative and configurable. Formal statutory authority remains exclusively with authorized AICTE officials, and generated decision orders carry verifiable cryptographic provenance marked as prototype demonstration records.

---

## Table of Contents

### Part I: Mandate, System Foundations & Technical Architecture
1. [Executive Summary](#01-executive-summary)
2. [Project Snapshot](#02-project-snapshot)
3. [Problem Context and Operational Challenge](#03-problem-context-and-operational-challenge)
4. [Problem Statement: Requirement Decomposition](#04-problem-statement-requirement-decomposition)
5. [Objectives, Scope and Core Engineering Principles](#05-objectives-scope-and-core-engineering-principles)
6. [Stakeholders & Eight Dedicated Role Workspaces](#06-stakeholders--eight-dedicated-role-workspaces)
7. [Requirement Pillar A: End-to-End Workflow Automation](#07-requirement-pillar-a-end-to-end-workflow-automation)
8. [Requirement Pillar B: Pendency, Ageing & Workload Monitoring](#08-requirement-pillar-b-pendency-ageing--workload-monitoring)
9. [Requirement Pillars C & D: EVC Coordination & Undertakings](#09-requirement-pillars-c--d-evc-coordination--undertakings)
10. [Requirement Pillars E & F: Document Validity, Alerts & Reporting](#10-requirement-pillars-e--f-document-validity-alerts--reporting)
11. [Proposed Solution Blueprint](#11-proposed-solution-blueprint)
12. [System Architecture and Trust Boundaries](#12-system-architecture-and-trust-boundaries)
13. [Technology Stack and Engineering Choices](#13-technology-stack-and-engineering-choices)
14. [Data Architecture and Authoritative Domain Models](#14-data-architecture-and-authoritative-domain-models)
15. [Workflow Routes and Automated Route Determination](#15-workflow-routes-and-automated-route-determination)
16. [Workflow Safeguards, State Invariants & Optimistic Locking](#16-workflow-safeguards-state-invariants--optimistic-locking)
17. [Compliance Passport & Multi-Year Document Vault](#17-compliance-passport--multi-year-document-vault)
18. [Document Intelligence, Semantic Verification & Human Review](#18-document-intelligence-semantic-verification--human-review)
19. [EVC Expert Registry & Automated Conflict-of-Interest (COI) Engine](#19-evc-expert-registry--automated-conflict-of-interest-coi-engine)
20. [Mobile-First Field Inspection & Geotagged Evidence Sealing](#20-mobile-first-field-inspection--geotagged-evidence-sealing)
21. [Multi-Vector Deadline Engine & Hierarchical Escalations](#21-multi-vector-deadline-engine--hierarchical-escalations)

### Part II: Operations, Security, Evidence & Roadmap
22. [Transactional Notification Outbox & Reliable Dispatch](#22-transactional-notification-outbox--reliable-dispatch)
23. [Real-Time SSE Streaming & Resilient Polling Fallback](#23-real-time-sse-streaming--resilient-polling-fallback)
24. [Formal Statutory Decision Orders & Dynamic QR Verification](#24-formal-statutory-decision-orders--dynamic-qr-verification)
25. [Executive Command Centre & Seven Database-Backed Analytics Suites](#25-executive-command-centre--seven-database-backed-analytics-suites)
26. [Rule Studio, Priority Attribution & Explainable Case Briefs](#26-rule-studio-priority-attribution--explainable-case-briefs)
27. [Security Architecture & Defense-in-Depth Implementation](#27-security-architecture--defense-in-depth-implementation)
28. [Privacy, Data Governance & Tamper-Evident Auditability](#28-privacy-data-governance--tamper-evident-auditability)
29. [Civic Precision UI Design System & Universal Light/Dark Theme](#29-civic-precision-ui-design-system--universal-lightdark-theme)
30. [Interactive Judge Demonstration Explorer](#30-interactive-judge-demonstration-explorer)
31. [Step-by-Step End-to-End Evaluation Walkthrough](#31-step-by-step-end-to-end-evaluation-walkthrough)
32. [API Surface, Schema Validation & Integration Boundaries](#32-api-surface-schema-validation--integration-boundaries)
33. [Deployment Architecture, Docker Orchestration & Multi-Stage Release](#33-deployment-architecture-docker-orchestration--multi-stage-release)
34. [Operational Readiness, Release Engineering & Observability](#34-operational-readiness-release-engineering--observability)
35. [Comprehensive Testing Strategy & Verified Quality Evidence](#35-comprehensive-testing-strategy--verified-quality-evidence)
36. [Government Adoption Model & AICTE Operating Blueprint](#36-government-adoption-model--aicte-operating-blueprint)
37. [Impact Framework, Efficiency Metrics & Measurable Outcomes](#37-impact-framework-efficiency-metrics--measurable-outcomes)
38. [Strategic Roadmap & National Integration Horizons](#38-strategic-roadmap--national-integration-horizons)
39. [Risk Matrix, Operational Limitations & Technical Mitigations](#39-risk-matrix-operational-limitations--technical-mitigations)
40. [Recommended Pilot Implementation & Phased Rollout Plan](#40-recommended-pilot-implementation--phased-rollout-plan)
41. [Glossary of Regulatory & Engineering Terms](#41-glossary-of-regulatory--engineering-terms)
42. [Acronyms, Regulatory Standards & Bibliographic Citations](#42-acronyms-regulatory-standards--bibliographic-citations)
43. [Conclusion: Building a Transparent, Accountable Regulatory Future](#43-conclusion-building-a-transparent-accountable-regulatory-future)

---

# 01 Executive Summary

ReguFlow 360 (आवेदनसेतु | AvedanSetu), conceived and engineered by **Team TechTitans 2.0** from **KIET Deemed to be University**, is a production-grade, state-machine-driven regulatory platform engineered specifically for **AICTE Problem Statement 26262**: *"Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System."*

Technical education approval in India governs thousands of engineering, management, pharmacy, and polytechnic institutions annually. Historically, approval workflows have faced significant operational hurdles: fragmented data silos across regional offices and apex committees, manual tracking of multi-year validity certificates (such as 33-year land lease deeds and municipal fire NOCs), unmonitored post-approval compliance undertakings, delayed Expert Visiting Committee (EVC) panel formation, and the absence of an automated, deduplicated escalation engine for breached statutory deadlines.

ReguFlow 360 solves these systemic challenges by introducing a unified, rule-driven, and highly observable operational layer. Operating across a single unified PostgreSQL relational core, the system delivers:
- **Eight Distinct Role Workspaces**: Eliminates generic dashboards by providing strictly scoped environments for Institution Admins, Compliance Officers, Regional Officers (RO), Bureau Officers (BO), Standing Hearing Committee (SHC/SAC) Members, EVC Coordinators, Competent Authorities (Chairman/Member Secretary), and System Administrators.
- **Controlled Automation with Human Sovereignty**: Automated routing, deadline calculations, and priority scoring triage and accelerate administrative throughput, while preserving non-negotiable statutory human accountability. Only the authorized Competent Authority can issue formal approval or rejection orders.
- **Explainable Conflict-of-Interest (COI) Engine**: Automatically evaluates proposed EVC panels against parent-trust affiliations, prior institutional employment, cooling-off intervals, and declared conflicts, preventing compromised inspections.
- **Continuous Compliance Passport & Multi-Year Document Vault**: Transforms compliance from an annual, episodic event into a real-time, continuous monitoring register with SHA-256 tamper-evident evidence versioning.
- **Transactional Outbox & Multi-Tier Escalations**: Guarantees zero duplicate alerts across background scans via database-level idempotency, maintaining persistent delivery logs with SSE streaming and automatic polling fallback.
- **Accessible Dual-Theme Civic Precision UI**: Delivers a WCAG-compliant design system with universal Light/Dark modes, full mobile responsiveness, and an interactive Judge Demonstration Explorer.

---

# 02 Project Snapshot

| System Attribute | Technical Implementation Details |
|---|---|
| **Product Names** | ReguFlow 360 / आवेदनसेतु (AvedanSetu) |
| **Target Problem Statement** | SIH 2026 Problem Statement 26262 |
| **Team Name & ID** | TechTitans 2.0 • Team ID: 197859 |
| **Institution** | KIET Deemed to be University, Ghaziabad, Uttar Pradesh |
| **Core Architecture** | Decoupled Client-Server Micro-Modular Architecture with State Machine Guards |
| **Backend Framework** | Python 3.12+, FastAPI, SQLAlchemy 2.0 (Async/Sync), Pydantic v2 |
| **Frontend Framework** | React 18.3+, TypeScript (strict mode), Vite 5.4+, Tailwind CSS |
| **Database & Migrations** | PostgreSQL 16 (production) / SQLite with WAL (local testing), Alembic |
| **UI Design System** | Civic Precision (Midnight Ink `#152536`, Meridian Teal `#0E746B`, Cool Porcelain `#F4F6F8`) |
| **Testing & Quality Evidence** | **236 Backend Tests (Pytest)**, **42 Frontend Tests (Vitest)**, 100% build & typecheck clean |
| **Deployment Targets** | Web: Vercel ([avedansetu.vercel.app](https://avedansetu.vercel.app)) • API: Render Cloud ([reguflow-backend.onrender.com](https://reguflow-backend.onrender.com)) |
| **Production Defense** | Loopback-bound database, non-root containers, zero unversioned overwrites, fail-closed production boots |

---

# 03 Problem Context and Operational Challenge

Approval processing in technical education is an intricate, multi-actor administrative journey governed by the **AICTE Approval Process Handbook (APH)**. Each annual cycle entails thousands of institutional applications across multiple regulatory categories:
1. Setting up new technical institutions.
2. Annual Extension of Approval (EOA).
3. Increase/decrease in student intake or closure of courses.
4. Introduction of supernumerary seats (OCI, FN, PMSSS).
5. Conversion of existing institutions into Co-ed or specialized universities.

### The Operational Challenge
In traditional, partially fragmented operations, administrative friction manifests in five core vulnerabilities:
1. **Opaque Stage Pendency & Sliced Communication**: When deficiencies are found during scrutiny, communicating them via ad-hoc emails or postal mail creates friction. Institutions lose visibility into cure windows, while Regional Officers struggle to track whether resubmitted evidence actually addresses the deficiency.
2. **Delayed EVC Scheduling & COI Vulnerabilities**: Identifying cases needing on-site verification, finding qualified senior academicians without conflicts of interest (such as alumni affiliations or joint trusts), and tracking field visits leads to significant scheduling bottlenecks.
3. **The "Post-Approval Compliance Blindspot"**: Approvals are frequently granted subject to conditions (e.g., establishing disabled-accessible tactile paths, setting up specialized AI laboratories within 6 months, or renewing a expiring municipal Fire NOC). Once an approval order is issued, tracking these time-bound covenants historically falls through administrative cracks.
4. **Document Validity & Multi-Year Expiry Risks**: Mandatory regulatory records—notably 33-year land lease deeds, municipal occupancy certificates, and annual fire safety NOCs—carry independent, asynchronous validity timelines completely disconnected from the annual academic approval window.
5. **Alert Fatigue & Unreliable Follow-ups**: Generic blast reminders often produce alert fatigue, while unmonitored deadline breaches fail to escalate systematically to Regional and Bureau directors.

ReguFlow 360 directly resolves these challenges by modeling the entire operational lifecycle as an interconnected, observable state machine.

---

# 04 Problem Statement: Requirement Decomposition

The requirements specified in SIH Problem Statement 26262 decompose into six foundational pillars:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│              SIH 2026 PROBLEM STATEMENT 26262 — FUNCTIONAL PILLARS              │
├─────────────────────┬─────────────────────┬─────────────────────────────────────┤
│ PILLAR A            │ PILLAR B            │ PILLAR C                            │
│ End-to-End Workflow │ Pendency, Ageing    │ EVC Coordination &                  │
│ Automation          │ & Workload Monitor  │ Conflict-of-Interest Checks         │
├─────────────────────┼─────────────────────┼─────────────────────────────────────┤
│ PILLAR D            │ PILLAR E            │ PILLAR F                            │
│ Continuous Compli-  │ Document Validity   │ Transactional Alerts,               │
│ ance Passport       │ & Multi-Year Vault  │ Multi-Tier Escalations & Reporting  │
└─────────────────────┴─────────────────────┴─────────────────────────────────────┘
```

1. **Pillar A: End-to-End Workflow Automation**: Automated routing of applications through configurable pathways (`ONLY_SCRUTINY`, `SCRUTINY_EVC`, `EVC_SAC_SHC`, `ONLY_EVC`). Guarded state transitions, mandatory recorded remarks, deficiency cure loops, and irrevocable Competent Authority determinations.
2. **Pillar B: Pendency, Ageing & Workload Monitoring**: Real-time queues showing stage ageing, regional distribution, bottleneck indicators, and deterministic operational priority triage scores.
3. **Pillar C: EVC Panel Scheduling & Field Integrity**: Eligibility queues, automated Conflict-of-Interest checks, invitation acceptance lifecycles, mobile-first field inspection with browser geotagging, checklist scoring, and recommendation logging.
4. **Pillar D: Continuous Compliance Passport**: Post-approval tracking of time-bound undertakings, versioned digital proof submission, Regional Officer verification desks, and deficiency remediation.
5. **Pillar E: Document Validity & Expiry Engine**: Multi-year validity tracking for 33-year lease deeds, fire safety NOCs, and building certificates with local digital PDF text intelligence, SHA-256 tamper-sealing, and renewal queues.
6. **Pillar F: Alerts, Multi-Tier Escalations & Executive Reporting**: Deduplicated background scans, transactional outbox dispatch, progressive multi-tier escalations (`REMINDER_L1` to `ESCALATION_L3_MEMBER_SEC`), SSE real-time updates, sanitized CSV exports, and formal decision order generation with dynamic QR verification.

---

# 05 Objectives, Scope and Core Engineering Principles

### Core Objectives
- Unify pre-approval scrutiny, on-site inspection, post-approval undertakings, and multi-year document renewals under a single, highly auditable platform.
- Strictly enforce role and regional data isolation, guaranteeing that institutional actors see only their own tenancy and officers operate strictly within their assigned jurisdiction.
- Eliminate duplicate notifications and alert fatigue via database-level composite idempotency keys.
- Preserve complete evidence continuity by computing SHA-256 checksums and preventing unversioned overwrites.
- Ensure 100% test reproducibility, zero-secret commits, and universal cross-device responsiveness.

### Immutable Engineering Principles
1. **Single Source of Truth**: Backend state machines and relational constraints govern all state transitions, role authorizations, and deadline calculations. No client-side bypass is possible.
2. **Controlled Automation with Human Sovereignty**: AI and algorithmic heuristics act exclusively as triage and assistive tools (e.g., candidate field extraction, queue priority scoring). The system strictly prohibits automated approval, rejection, or compliance sign-off.
3. **No Unversioned Overwrites**: Submitting a document renewal, deficiency cure, or compliance proof creates an immutable versioned record with SHA-256 cryptographic sealing.
4. **Idempotent Background Operations**: All deadline evaluations, reminder dispatches, and escalation promotions utilize database-level composite uniqueness keys (`obligation_id + trigger_type + threshold_days + escalation_level`), guaranteeing zero duplicate alerts.
5. **Zero-Secret Commits & Fail-Closed Startup**: All sensitive parameters are injected via `.env`. In production (`ENVIRONMENT=production`), the application immediately aborts startup if keys are weak or debug/demo flags are active.

---

# 06 Stakeholders & Eight Dedicated Role Workspaces

To prevent the common pitfall of collapsing all administrative users into a single generic dashboard, ReguFlow 360 provides eight dedicated, role-tailored operational workspaces:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      REGUFLOW 360 ROLE WORKSPACE TAXONOMY                       │
├──────────────────────────┬──────────────────────────────────────────────────────┤
│ 1. INSTITUTION_ADMIN     │ Application filing, deficiency cure desk, order vault│
│ 2. COMPLIANCE_OFFICER    │ Compliance undertakings, document validity renewals  │
│ 3. REGIONAL_OFFICER (RO) │ Regional scrutiny, deficiency memos, cure sign-off   │
│ 4. BUREAU_OFFICER (BO)   │ National workload oversight, cross-regional SLA desk │
│ 5. COMMITTEE_MEMBER      │ SAC/SHC hearing dockets, EVC panel review findings   │
│ 6. EVC_COORDINATOR       │ Panel appointment, COI evaluations, field roster     │
│ 7. COMPETENT_AUTHORITY   │ Final statutory determination (Approved / Rejected)  │
│ 8. SYSTEM_ADMIN          │ Rule Studio, distributed scheduler telemetry, audit  │
└──────────────────────────┴──────────────────────────────────────────────────────┘
```

1. **Institution Admin**: Scoped strictly to the applicant institution. Manages new filings, views real-time application tracking, responds to itemized deficiency memos with explanatory remarks and document uploads, and accesses formal statutory approval orders.
2. **Compliance Officer**: Scoped to institutional post-approval compliance. Monitors the **Compliance Passport**, tracks time-bound undertakings, reviews expiring land leases and municipal certificates, and submits renewal evidence.
3. **Regional Officer (RO)**: Scoped strictly to their designated geographic region (e.g., Western Region). Conducts formal scrutiny of applications, issues itemized deficiency notices, verifies institutional cures, signs off on scrutiny completion, and inspects local escalations.
4. **Bureau Officer (BO)**: Operates at the AICTE Apex Headquarters. Supervises cross-regional pendency, tracks regional SLA compliance, reviews Tier-2 escalations, and coordinates national regulatory balancing.
5. **Committee Member (SAC/CAC/SHC)**: Accesses assigned hearing dockets, reviews scrutiny records, evaluates EVC panel reports, and records formal committee recommendations.
6. **EVC Coordinator**: Regional Directorate role responsible for identifying inspection-eligible applications, forming expert visiting panels, running automated conflict-of-interest assessments, issuing digital invitations, and supervising mobile field inspection progress.
7. **Competent Authority (CA)**: The exclusive statutory decision-maker (Chairman / Member Secretary / Designated Bureau Head). Reviews the complete, consolidated evidence docket—scrutiny sign-off, EVC panel recommendations, and committee findings—and executes the irrevocable final statutory order (`APPROVED` or `REJECTED`).
8. **System Administrator**: Non-statutory operational controller. Manages user provisioning, configures regulatory rule templates in **Rule Studio**, monitors distributed scheduler leases, inspects the transactional notification outbox, and exports sanitized immutable audit trails.

---

# 07 Requirement Pillar A: End-to-End Workflow Automation

ReguFlow 360 enforces a deterministic, guarded state machine governing the entire application lifecycle. An application cannot leapfrog intermediate statutory stages, and stale client views cannot execute out-of-sequence mutations.

### Canonical Application Statuses
- `DRAFT`: Initial institutional data entry and draft document assembly.
- `SUBMITTED`: Formal fee payment and cryptographic dossier submission.
- `UNDER_SCRUTINY`: Active technical verification by assigned Regional Officers.
- `DEFICIENCY_COMMUNICATED`: Itemized deficiency memo issued; institutional cure clock running.
- `RESUBMITTED`: Institution has cured all open deficiencies with remarks and supporting files.
- `SCRUTINY_COMPLETED`: Scrutiny successfully passed with zero remaining deficiencies.
- `AWAITING_EVC_SCHEDULE`: Application queued for Expert Visiting Committee panel appointment.
- `EVC_SCHEDULED`: Expert panel appointed and field inspection visit date confirmed.
- `EVC_COMPLETED`: Field visit concluded and comprehensive inspection report filed.
- `AWAITING_SAC_CAC_REVIEW`: Docket under review by Standing Hearing / Appellate Committee.
- `AWAITING_COMPETENT_AUTHORITY`: All prerequisites satisfied; awaiting final statutory determination.
- `APPROVED`: Final statutory Extension of Approval / New Institution order granted.
- `REJECTED`: Final statutory rejection order issued with detailed legal grounds.
- `CLOSED`: Administrative closure or application withdrawal recorded.

### Guarded Transition Engine
- **Optimistic Concurrency Control**: Every application record carries an integer `version` field. State transitions require matching `expected_version`. If another officer updates the record concurrently, the lagging request fails with HTTP 409 Conflict, preventing lost updates.
- **Mandatory Justification**: High-consequence transitions (issuing deficiencies, rejecting an application, or granting statutory approval) mandate non-empty narrative remarks that are immutably logged to the audit ledger.
- **Deficiency Cure Locking**: An application in `DEFICIENCY_COMMUNICATED` status cannot be resubmitted until **every** open deficiency item has been provided with specific cure remarks and uploaded evidence.

---

# 08 Requirement Pillar B: Pendency, Ageing & Workload Monitoring

Operational transparency is maintained through real-time queue metrics and explainable queue prioritization:

1. **Stage Ageing Analysis**: The engine continuously computes the exact elapsed calendar days an application has spent in its active stage against configured SLA thresholds (e.g., Scrutiny SLA: 14 days; Deficiency Cure Window: 10 days; EVC Scheduling Window: 7 days).
2. **Bottleneck Indicators**: Automatically highlights applications with multiple deficiency return cycles (return loops >= 2), prolonged EVC report submission delays, or pending committee hearings.
3. **Deterministic Operational Priority Scoring (0–100)**: A transparent, formulaic triage aid designed to assist Regional Officers in prioritizing daily queues:
   $$\text{Priority Score} = \min(100, (\text{Stage Ageing Days} \times 2.5) + (\text{Open Deficiencies} \times 12) + (\text{Active Escalation Level Weight}))$$
   *Strict Statutory Invariant:* The priority score is strictly an operational triage aid. It never alters application statutory status, grants automated approval, or infers institutional non-compliance.

---

# 09 Requirement Pillars C & D: EVC Coordination & Undertakings

### Pillar C: EVC Coordination & Expert Conflict-of-Interest Engine
Inspection planning requires strict objectivity. ReguFlow 360 models expert profiles with verified academic domains, institutional affiliations, regional locations, and parent trust associations.

- **Automated Conflict-of-Interest (COI) Checks**: Before an expert can be assigned to an institution, the engine executes four automated cross-checks:
  1. *Affiliation Conflict*: Blocks assignment if the expert is currently employed by or affiliated with the applicant institution.
  2. *Parent Trust Conflict*: Blocks assignment if the expert belongs to another institution operated by the identical parent educational trust or society.
  3. *Cooling-Off Period*: Enforces a mandatory cooling-off window (demonstration default: 3 years), preventing the same expert from inspecting an institution repeatedly.
  4. *Declared Conflict*: Blocks assignment if either the institution or expert has logged an active dispute or personal conflict.
- **Justified Conflict Overrides**: In specialized disciplines with acute expert scarcity, an EVC Coordinator may execute an override only by recording a substantive, mandatory justification that is permanently captured in the audit ledger.
- **Invitation Lifecycle**: Expert panel assignments progress through explicit states: `PROPOSED` $\rightarrow$ `INVITED` $\rightarrow$ `ACCEPTED` (or `DECLINED` / `CONFLICT_DETECTED` $\rightarrow$ `REASSIGNED`).

### Pillar D: Continuous Compliance Passport
Post-approval institutional governance is tracked through the **Compliance Passport**:
- **Covenants & Conditions**: Approvals frequently mandate time-bound conditions (e.g., establishing sewage treatment plants, barrier-free access ramps, or faculty cadre ratios within 180 days).
- **Evidence Verification Desk**: Institutions submit digital proof dossiers. Regional Officers review the evidence, marking items as `VERIFIED`, `CORRECTION_REQUIRED`, or `DEFICIENT`.
- **Zero Evidence Loss**: Submitting revised evidence increments the version counter (`v1` $\rightarrow$ `v2`) while preserving previous files and review remarks.

---

# 10 Requirement Pillars E & F: Document Validity, Alerts & Reporting

### Pillar E: Document Vault & Multi-Year Expiry Engine
Technical institutions are governed by documents whose validity periods span decades:
- **Tracked Regulatory Instruments**: Registered 33-year land lease deeds, municipal building completion certificates, structural stability certificates, and annual fire safety NOCs.
- **Dynamic Expiry Statuses**: Documents are classified in real time as `ACTIVE`, `EXPIRING_SOON` (within 60/90 days), `RENEWAL_SUBMITTED`, `VERIFIED`, or `EXPIRED`.
- **Local Document Intelligence**: Extracts candidate text, issuing authorities, and expiry dates from uploaded digital PDFs, cross-checking candidate dates against entered metadata to alert officers of discrepancies.

### Pillar F: Transactional Outbox, Multi-Tier Escalations & Reporting
- **Transactional Outbox**: Business mutations and notification events commit in the exact same database transaction. A decoupled worker processes the queue, preventing lost notifications or open SMTP transaction locks.
- **Progressive Multi-Tier Escalations**: Breached deadlines trigger automated, deduplicated escalation ladders:
  1. `REMINDER_L1`: Initial warning sent to Institution Admin (T-7 days).
  2. `REMINDER_L2`: Urgent reminder sent to Institution Admin & Compliance Officer (T-2 days).
  3. `ESCALATION_L1_RO`: SLA breach escalated to Regional Officer (T+1 day overdue).
  4. `ESCALATION_L2_BO`: Unresolved breach escalated to AICTE Apex Bureau Officer (T+7 days overdue).
  5. `ESCALATION_L3_MEMBER_SEC`: Critical breach escalated to Member Secretary / Council (T+14 days overdue).

---

# 11 Proposed Solution Blueprint

ReguFlow 360 acts as a cohesive regulatory operating system bridging institutions, regional directorates, inspection panels, and apex authorities over a single unified data architecture:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    REGUFLOW 360 COMPREHENSIVE ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  USER EXPERIENCE LAYER (React 18 + TypeScript + Vite + Tailwind CSS)            │
│  ├── Institution Portal (Applications, Deficiency Cure, Compliance Passport)    │
│  ├── Regional Directorate Command (Scrutiny, Cure Sign-Off, Local Escalations)  │
│  ├── Apex Bureau Operations (National Workload, Cross-Regional SLA Balancing)   │
│  ├── Committee Review Desk (SAC/SHC Hearing Dockets, EVC Review Findings)       │
│  ├── EVC Inspection Studio (COI Evaluations, Field App, Geotagged Evidence)     │
│  ├── Competent Authority Desk (Statutory Determination, Irrevocable Orders)     │
│  └── System Admin & Rule Studio (Policy Life Cycle, Telemetry, Audit Logs)      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  APPLICATION API & SECURITY GATEWAY (FastAPI + Pydantic v2 + Python 3.12)       │
│  ├── JWT Token Authentication & Database-Backed Session Revocation              │
│  ├── Strict RBAC & Tenant/Regional Isolation Interceptors                       │
│  ├── Guarded State Machine Engine & Optimistic Concurrency Locking              │
│  ├── Server-Sent Events (SSE) Live Stream Broker & Polling Fallback             │
│  └── CSV Formula Injection Sanitization Filter                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  DOMAIN SERVICES & LOGIC ENGINES                                                │
│  ├── Workflow Automation Engine       ├── Document Intelligence (pypdf)         │
│  ├── EVC Panel & COI Engine          ├── Formal Statutory Order Generator (PDF) │
│  ├── Multi-Vector Deadline Engine    ├── Transactional Outbox Dispatcher        │
│  └── Case Brief Synthesizer          ├── Deterministic Priority Triage Service  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  PERSISTENCE & STORAGE TIER (PostgreSQL 16 Relational Core + Alembic Migrations)│
│  ├── Applications & Versioned Memos   ├── Document Vault & SHA-256 Checksums    │
│  ├── Compliance Obligations & Proofs ├── EVC Inspections & Geotagged Evidence  │
│  ├── Transactional Notification Queue ├── Immutable Relational Audit Ledger     │
│  └── Distributed Scheduler Leases    └── Rule Version History Tables            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# 12 System Architecture and Trust Boundaries

The system enforces four distinct trust boundaries:
1. **Client $\leftrightarrow$ API Gateway Boundary**: All incoming requests pass through JWT Bearer authentication. Tokens encode user identity, role assignments, and tenant/regional scope. Stale tokens revoked via logout are blocked by the database-backed token blacklist.
2. **Multi-Tenant & Regional Isolation Boundary**:
   - Institutional users can query and mutate records scoped *exclusively* to their own `institution_id`.
   - Regional Officers can query and mutate records scoped *exclusively* to their designated `region` (e.g., Western Region). Cross-regional access attempts return HTTP 403 Forbidden.
   - Competent Authority and Bureau Officers operate under national scope, governed by strict action permissions.
3. **Application $\leftrightarrow$ Database Boundary**: Interacted with via SQLAlchemy parameterized queries, preventing SQL injection vulnerabilities. Write operations execute within explicit database transactions.
4. **Local Document Storage Boundary**: All uploaded files are stored using unguessable UUID-based filenames and registered in the database alongside their SHA-256 digests. Direct filesystem traversal is blocked; non-administrative downloads of unindexed disk paths fail closed with HTTP 404.

---

# 13 Technology Stack and Engineering Choices

| Layer | Component | Chosen Technology | Justification & Architectural Benefit |
|---|---|---|---|
| **Frontend** | Core Framework | **React 18.3+ with TypeScript** | Type-safe enterprise UI, component reusability, zero `any` types. |
| | Build Tool | **Vite 5.4+** | Sub-second hot module replacement, optimized production tree-shaking. |
| | Styling & Tokens | **Tailwind CSS + CSS Variables** | Civic Precision design tokens, seamless instant light/dark theme switching. |
| | Icons & Visuals | **Lucide React** | Lightweight, clean, accessible SVG iconography. |
| | Server State | **Axios + Custom Resilient Cache** | Automatic query cache clearing upon persona switch, zero stale data leaks. |
| **Backend** | Framework | **FastAPI (Python 3.12+)** | Native async concurrency, automatic OpenAPI schemas, high throughput. |
| | Data Validation | **Pydantic v2** | Strict schema validation, lightning-fast C-extension serialization. |
| | ORM & DB Access | **SQLAlchemy 2.0** | Enterprise relational mapping, transaction safety, explicit joins. |
| | DB Migrations | **Alembic** | Version-controlled, reproducible, reversible database schema evolution. |
| | PDF Processing | **ReportLab & pypdf** | Native server-side PDF generation with dynamic QR codes; zero cloud reliance. |
| **Database** | Production Database| **PostgreSQL 16** | Robust ACID transactions, JSONB querying, row-level locking (`SKIP LOCKED`). |
| | Local Testing | **SQLite with WAL Mode** | Lightweight, zero-setup local test execution with immediate teardown. |
| **DevOps** | Containerization | **Docker & Docker Compose** | Reproducible multi-stage builds, non-root execution, port isolation. |
| | Hosting | **Vercel (UI) + Render (API)** | Global CDN edge caching for UI; scalable containerized backend services. |

---

# 14 Data Architecture and Authoritative Domain Models

The relational database architecture guarantees referential integrity, optimistic concurrency, and auditability across all operational entities:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      CORE ENTITY-RELATIONSHIP ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────┐                 ┌───────────────────────────┐         │
│   │     Institution     │ 1             * │        Application        │         │
│   │ ─────────────────── │─────────────────│ ───────────────────────── │         │
│   │ id (PK)             │                 │ id (PK)                   │         │
│   │ name, code, region  │                 │ institution_id (FK)       │         │
│   │ trust_society_name  │                 │ application_number (UQ)   │         │
│   └─────────────────────┘                 │ application_type, route   │         │
│              │ 1                          │ current_stage, version    │         │
│              │                            └───────────────────────────┘         │
│              │ *                                        │ 1                     │
│   ┌─────────────────────┐                               ├─────────────────────┐ │
│   │   DocumentRecord    │ 1                           * │                     │ │
│   │ ─────────────────── │──┐           ┌────────────────────┐   ┌───────────┐ │ │
│   │ id (PK), doc_type   │  │           │  AppDeficiencyItem │   │EVCInspect.│ │ │
│   │ valid_to, status    │  │           │ ────────────────── │   │───────────│ │ │
│   └─────────────────────┘  │           │ id (PK), code      │   │id (PK)    │ │ │
│              │ 1           │           │ deficiency_text    │   │status     │ │ │
│              │ *           │           │ cure_remarks       │   │convener   │ │ │
│   ┌─────────────────────┐  │           │ status (OPEN/CURED)│   │recommend. │ │ │
│   │   DocumentVersion   │  │           └────────────────────┘   └───────────┘ │ │
│   │ ─────────────────── │  │                                                  │ │
│   │ id (PK), version    │  │                                                  │ │
│   │ sha256_checksum     │  │ 1                                                │ │
│   └─────────────────────┘  ├────────────────────────────┐                     │ │
│                            │ *                          │ *                   │ │
│                 ┌─────────────────────┐      ┌────────────────────────┐       │ │
│                 │ComplianceUndertaking│      │   NotificationOutbox   │       │ │
│                 │ ─────────────────── │      │ ────────────────────── │       │ │
│                 │ id (PK), title      │      │ id (PK), event_type    │       │ │
│                 │ due_date, status    │      │ idempotency_key (UQ)   │       │ │
│                 │ verified_at         │      │ delivery_status        │       │ │
│                 └─────────────────────┘      └────────────────────────┘       │ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# 15 Workflow Routes and Automated Route Determination

The regulatory route dictates the mandatory sequence of review stages an application must undergo. ReguFlow 360 models four canonical routes derived from the AICTE Approval Process Handbook:

| Route Code | Regulatory Description | Prescribed Workflow Sequence | Governing Use Case |
|---|---|---|---|
| `ONLY_SCRUTINY` | Standard Annual Extension of Approval (EOA) | `SUBMITTED` $\rightarrow$ `UNDER_SCRUTINY` $\rightarrow$ `SCRUTINY_COMPLETED` $\rightarrow$ `AWAITING_COMPETENT_AUTHORITY` $\rightarrow$ `APPROVED / REJECTED` | Routine renewals with zero infrastructure or course changes. Bypasses physical EVC. |
| `SCRUTINY_EVC` | Setting Up New Technical Institution / Significant Expansion | `SUBMITTED` $\rightarrow$ `UNDER_SCRUTINY` $\rightarrow$ `AWAITING_EVC_SCHEDULE` $\rightarrow$ `EVC_SCHEDULED` $\rightarrow$ `EVC_COMPLETED` $\rightarrow$ `AWAITING_COMPETENT_AUTHORITY` $\rightarrow$ `APPROVED / REJECTED` | New engineering colleges or intake increases requiring physical verification. |
| `EVC_SAC_SHC` | Disputed Cases / Land Deficiency Appeal / Complex Expansion | `SUBMITTED` $\rightarrow$ `UNDER_SCRUTINY` $\rightarrow$ `EVC_SCHEDULED` $\rightarrow$ `EVC_COMPLETED` $\rightarrow$ `AWAITING_SAC_CAC_REVIEW` $\rightarrow$ `AWAITING_COMPETENT_AUTHORITY` | Applications requiring Expert Committee review and Standing Hearing Committee hearings. |
| `ONLY_EVC` | Surprise Inspection / Complaint-Triggered Re-Verification | `SUBMITTED` $\rightarrow$ `AWAITING_EVC_SCHEDULE` $\rightarrow$ `EVC_SCHEDULED` $\rightarrow$ `EVC_COMPLETED` $\rightarrow$ `AWAITING_COMPETENT_AUTHORITY` | Special targeted inspections dispatched without pre-scrutiny documentation loops. |

*Statutory Invariant:* Bypassing EVC in the `ONLY_SCRUTINY` route does **not** grant automated approval. All routes converge strictly at the Competent Authority desk for an authorized statutory order.

---

# 16 Workflow Safeguards, State Invariants & Optimistic Locking

The state machine implements five layers of deterministic safeguards:
1. **Valid State Transitions**: Only predefined directional transitions are permitted. A request to move from `SUBMITTED` directly to `APPROVED` fails immediately with HTTP 400 Bad Request.
2. **Deficiency Resolution Precondition**: An application cannot advance from `UNDER_SCRUTINY` to `SCRUTINY_COMPLETED` if any linked deficiency item remains in `OPEN` status.
3. **Resubmission Completeness Check**: When an institution cures deficiencies, every open item must have non-empty `cure_remarks` and uploaded evidence before the system permits state transition to `RESUBMITTED`.
4. **Optimistic Concurrency Control**: All mutation endpoints accept an `expected_version` integer parameter. If the database record's `version` differs, the write is aborted with HTTP 409 Conflict, returning the latest state to the caller.
5. **Irrevocable Final Determinations**: Once an application reaches `APPROVED` or `REJECTED`, the state machine enters a terminal state. No officer or administrator can alter its status without formal legal appeal reopening.

---

# 17 Compliance Passport & Multi-Year Document Vault

### Compliance Passport: Continuous Post-Approval Governance
Traditional regulation suffers from the "post-approval blindspot." ReguFlow 360's Compliance Passport establishes continuous monitoring:
- **Mandatory Covenants**: Seeded with core AICTE undertakings (e.g., establishing anti-ragging committees, barrier-free access, 24/7 CCTV surveillance, and faculty cadre ratio compliance).
- **Time-Bound Due Dates**: Each covenant carries an explicit due date (e.g., T+60 or T+180 days post-approval).
- **Verification Workflow**: Submissions enter `PENDING_VERIFICATION`. Regional Officers review the proof and record determinations (`VERIFIED`, `CORRECTION_REQUIRED`, `DEFICIENT`).
- **Correction Loop**: Items marked `CORRECTION_REQUIRED` provide detailed reviewer remarks and open a 15-day cure window for the institution without overwriting prior evidence files.

### Multi-Year Document Vault
- **Tracked Instruments**: 33-year registered land lease deeds, municipal building stability certificates, and annual fire department safety NOCs.
- **Asynchronous Expiry Engine**: Background scans evaluate document validity daily, flagging records reaching T-90, T-60, and T-30 days before expiry.
- **Renewal Verification**: When an institution uploads a renewed certificate, it is placed in `RENEWAL_SUBMITTED` status. Upon officer sign-off, the new certificate becomes active, while all previous version records remain permanently archived.

---

# 18 Document Intelligence, Semantic Verification & Human Review

To assist officers in reviewing dense legal records, ReguFlow 360 integrates a lightweight, deterministic document intelligence pipeline powered by `pypdf`:
1. **Local Text Extraction**: Digital PDFs are parsed locally on the server without sending confidential institutional files to third-party cloud APIs.
2. **Entity & Metadata Cross-Checks**:
   - Compares extracted document numbers against entered institutional records.
   - Parses candidate issue and expiry dates, flagging already expired documents.
   - Evaluates land lease terms, checking for statutory 33-year duration clauses.
3. **Source Excerpt Grounding**: Findings display exact page numbers and verbatim text snippets from the PDF, allowing officers to verify discrepancies instantly.
4. **Strict Human Sovereignty**: Document intelligence outputs are strictly advisory findings (`EXPIRY_DATE_MATCH`, `EXPIRY_DATE_MISMATCH`, `CERTIFICATE_ALREADY_EXPIRED`). The engine never autonomously alters document validity or status.

---

# 19 EVC Expert Registry & Automated Conflict-of-Interest (COI) Engine

The Expert Visiting Committee (EVC) module guarantees uncompromised field verifications:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│               AUTOMATED CONFLICT-OF-INTEREST (COI) EVALUATION                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   Candidate Expert Profile           Target Institution Application             │
│   ├── Current Affiliation: Inst. X   ├── Applicant: Inst. Y (Pune)              │
│   ├── Parent Trust: Trust A          ├── Parent Trust: Trust B                  │
│   ├── Prior Inspections: 2023        ├── Regional Directorate: Western          │
│   └── Declared Conflicts: None       └── Inspection Discipline: Computer Sci.   │
│                 │                                  │                            │
│                 └─────────────────┬────────────────┘                            │
│                                   ▼                                             │
│               EVC Conflict-of-Interest Evaluation Rules                         │
│               ├── Check 1: Institution Affiliation Match?   ──> [PASS]          │
│               ├── Check 2: Shared Parent Trust / Society?   ──> [PASS]          │
│               ├── Check 3: 3-Year Cooling-Off Observed?     ──> [PASS]          │
│               └── Check 4: Declared Personal Conflicts?     ──> [PASS]          │
│                                   │                                             │
│                                   ▼                                             │
│         Determination: NO_CONFLICT_DETECTED (Eligible for Invitation)           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Structured Expert Registry**: Tracks senior academicians, professional specializations, institutional affiliations, parent trusts, and inspection histories.
2. **Automated Conflict Evaluation**: Evaluates proposed panels in real time against four non-negotiable conflict rules:
   - *Current Affiliation Match*: Rejects experts employed at the applicant institution.
   - *Shared Parent Trust*: Rejects experts affiliated with another college operated by the same educational trust.
   - *3-Year Cooling-Off Rule*: Enforces a mandatory 3-year gap before an expert can re-inspect the same institution.
   - *Declared Personal Conflicts*: Flags mutual conflicts or active grievances.
3. **Invitation & Reassignment Lifecycle**: Experts receive digital invitations. Upon declining or if an unavoidable conflict arises, the slot is marked `REASSIGNMENT_REQUIRED` and the coordinator appoints an eligible replacement.

---

# 20 Mobile-First Field Inspection & Geotagged Evidence Sealing

Inspections must be conducted with verifiable field evidence. ReguFlow 360 features a dedicated mobile web application (`/officer/evc/field/:id`):
- **Browser Geolocation Verification**: Captures the inspector's real-time latitude, longitude, and coordinate accuracy radius at the time of check-in, verifying physical presence on the institutional campus.
- **5-Point APH Core Inspection Checklist**:
  1. *Land & Built-up Carpet Area*: Verifies contiguous land possession, FSI compliance, and instructional area norms.
  2. *Computing Infrastructure & AI Labs*: Verifies operational workstations, licensed/open-source software stacks, and LAN connectivity.
  3. *Central Library & Digital Bandwidth*: Verifies book volumes, national digital library subscriptions, and >100 Mbps Wi-Fi.
  4. *Barrier-Free Campus & Operational Lifts*: Verifies tactile paving, disability-accessible washrooms, ramps, and operational lifts.
  5. *Fire Safety & Emergency Exits*: Verifies municipal fire certificates, pressurized hose reels, and disaster evacuation plans.
- **Geotagged Photographic Proof**: Inspectors upload real-time photographs across checklist points. Files are hashed with SHA-256 and immutably sealed into the inspection dossier.
- **Formal Panel Recommendation**: Convener logs final panel findings (`RECOMMENDED_APPROVAL`, `DEFICIENCY_NOTED`, `RECOMMENDED_REJECTION`) with mandatory inspection notes.

---

# 21 Multi-Vector Deadline Engine & Hierarchical Escalations

Deadline enforcement is governed by an automated background engine evaluating four distinct regulatory vectors:

| Deadline Vector | Trigger Criterion | Grace Period / Threshold | Automated Regulatory Action |
|---|---|---|---|
| **Stage Scrutiny SLA** | Application in `UNDER_SCRUTINY` | 14 calendar days | Daily reminders; escalates to Regional Officer at T+1 day, Bureau Officer at T+7 days. |
| **Deficiency Cure Window**| Memo in `DEFICIENCY_COMMUNICATED` | 10 calendar days | T-3 day urgent reminder; breaches trigger institutional cure forfeiture warnings. |
| **Compliance Undertakings**| Covenant in `NOT_YET_DUE` | Explicit due date (e.g. T+60d)| T-15 day advance alert; T+1 day escalates to RO; T+14 days escalates to Member Secretary. |
| **Document Validity Expiry**| Document reaching expiry date | T-90, T-60, T-30 days | Automated renewal alert; mark as `EXPIRED` at T+0 with escalation to RO. |

### Deduplicated Multi-Tier Escalation Architecture
To prevent duplicate alerts during recurring scans, every generated alert computes an idempotency key:
$$\text{Idempotency Key} = \text{MD5}(\text{obligation\_id} + \text{trigger\_type} + \text{threshold\_days} + \text{escalation\_level})$$
Database uniqueness constraints guarantee that an escalation level is triggered **exactly once** per obligation cycle.

---

# 22 Transactional Notification Outbox & Reliable Dispatch

External messaging failures must never compromise business transactions. ReguFlow 360 implements the **Transactional Outbox Pattern**:
1. **Atomic Local Commit**: When a workflow event occurs (e.g., deficiency issued or escalation raised), the business record and an outbox message record are committed in the same database transaction.
2. **Decoupled Worker Processing**: A background worker polls the outbox using PostgreSQL row-level locks (`SELECT ... FOR UPDATE SKIP LOCKED`), ensuring multi-worker concurrency without duplicate dispatches.
3. **Channel Telemetry & State Tracking**: Tracks delivery state across channels:
   - `IN_APP`: Persisted immediately to the user's notification tray.
   - `EMAIL`: Dispatched via configured SMTP adapter with automatic retry on transient failure.
   - `SMS`: Dispatched via carrier integration boundary (or simulated in local demo environments).
4. **Dead-Letter Handling & Manual Retry**: Failed messages undergo exponential backoff (up to 3 retries). Exhausted messages enter `DEAD_LETTER` status, where administrators can inspect error logs and trigger manual retries.

---

# 23 Real-Time SSE Streaming & Resilient Polling Fallback

Operational synchronization between officers and institutions is maintained via real-time updates:
- **Server-Sent Events (SSE)**: When logged in, the client connects to `/api/notifications/stream`. The server pushes real-time event updates (e.g., deficiency cured, report filed, escalation triggered).
- **Short-Lived Stream Tickets**: To prevent leaking long-lived JWTs in browser EventSource URLs, the frontend requests a single-use 60-second ticket via `/api/notifications/stream-ticket`, binding the stream to the authenticated session.
- **Resilient Polling Fallback**: If SSE connections are severed by proxies or mobile network interruptions, the frontend seamlessly falls back to 15-second background polling, ensuring zero lost notifications.

---

# 24 Formal Statutory Decision Orders & Dynamic QR Verification

The final approval or rejection of an institution requires formal, verifiable documentation:
1. **Irrevocable Order Generation**: Executed only after the Competent Authority records a statutory determination. The system compiles application metadata, academic years, approved intakes, and covenants into an official PDF dossier via ReportLab.
2. **Two-Pass Numbered Canvas**: Generates dynamic page counts (`Page X of Y`), official AICTE emblems, signature blocks, and legal disclaimers.
3. **Dynamic QR Code Verification**: Every generated order embeds a scannable QR code linking directly to `/verify/order?token=...`. Scanning the QR code displays:
   - Persisted application number and institution name.
   - Exact statutory determination (`APPROVED` or `REJECTED`).
   - Issuing authority, timestamp, and academic cycle.
   - SHA-256 cryptographic document checksum, verifying that the physical or digital document has not been altered.

---

# 25 Executive Command Centre & Seven Database-Backed Analytics Suites

The Executive Command Centre aggregates seven live, database-backed analytical reporting suites:
1. **Executive Pipeline & Stage Breakdown**: Real-time distribution of all active applications across scrutiny, EVC, committee review, and decision stages.
2. **SLA Turnaround & Ageing Analysis**: Stage-by-stage average processing durations, identifying compliance percentages and backlog bottlenecks.
3. **EVC Inspection Coordination Analytics**: Scheduled vs. completed inspections, virtual inspection ratios, and panel recommendation distributions.
4. **Compliance Passport Fulfilment Metrics**: Fulfilment rates across post-approval undertakings, overdue covenant breakdowns, and verification rates.
5. **Document Vault Expiry Risk Register**: Classifies institutions by document risk (e.g., expiring fire NOCs vs. valid 33-year leases).
6. **Multi-Tier Escalation Heatmap**: Tracks active escalations across RO, BO, and Member Secretary tiers, measuring mean resolution times.
7. **Comparative Regional Performance**: Benchmark matrix comparing regional directorates on processing speed, SLA adherence, and pending caseloads.

*Export Security:* All analytical views provide one-click CSV exports equipped with formula-injection sanitization (automatically prefixing cells starting with `=`, `+`, `-`, or `@` with single quotes).

---

# 26 Rule Studio, Priority Attribution & Explainable Case Briefs

### Regulatory Rule Studio
Enables authorized Bureau Officers and System Administrators to manage regulatory policies without modifying application code:
- **Policy Lifecycle**: Governs rule progression through `DRAFT` $\rightarrow$ `VALIDATED` $\rightarrow$ `PUBLISHED` $\rightarrow$ `RETIRED`.
- **Dry-Run Simulation**: Allows administrators to simulate rule changes (e.g., adjusting scrutiny SLA from 14 to 10 days) against active database records to project workload impacts before publishing.
- **Immutable Version History**: Publishing a new rule archives prior configurations into `rule_version_history`.

### Explainable Case Brief Synthesizer
Generates instant, structured executive case briefs for Competent Authorities prior to issuing final orders:
- Synthesizes application chronology, deficiency history, inspection findings, and document validity into a concise briefing.
- *Strict Grounding Invariant:* Operates strictly on deterministic database facts and direct citations. AI heuristics never invent statutory citations or overrule human judgment.

---

# 27 Security Architecture & Defense-in-Depth Implementation

ReguFlow 360 implements rigorous, defense-in-depth security across every architectural layer:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    DEFENSE-IN-DEPTH SECURITY CONTROL MATRIX                     │
├─────────────────────┬───────────────────────────────────────────────────────────┤
│ 1. IDENTITY & AUTH  │ JWT tokens, database blacklist revocation, active-role    │
│                     │ session switching, strong password hashing (bcrypt).      │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ 2. AUTHORIZATION    │ 8-role strict RBAC matrix, non-bypassable FastAPI         │
│                     │ dependency injection, zero privilege inheritance.        │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ 3. DATA ISOLATION   │ Multi-tenant institutional boundaries, regional director- │
│                     │ ate query scoping, zero cross-region data leakage.        │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ 4. INPUT VALIDATION │ Strict Pydantic v2 schemas, type coercion, regex pattern  │
│                     │ constraints, CSV formula-injection sanitization.          │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ 5. STORAGE INTEGRITY│ UUID file naming, SHA-256 tamper-evident sealing, path-   │
│                     │ traversal defenses, unindexed disk download blocks (404). │
├─────────────────────┼───────────────────────────────────────────────────────────┤
│ 6. FAIL-CLOSED BOOT │ Production boots fail closed on missing/weak SECRET_KEY   │
│                     │ (<32 chars), active DEBUG, active DEMO_MODE, or SQLite.   │
└─────────────────────┴───────────────────────────────────────────────────────────┘
```

---

# 28 Privacy, Data Governance & Tamper-Evident Auditability

- **Personal Data Protection**: Mobile field inspection coordinates, expert contact phone numbers, and institutional financial accounts are accessible strictly to authorized coordinators and regional officers.
- **Tamper-Evident Relational Audit Trail**: Every significant mutation (application filing, deficiency issuance, cure resubmission, EVC panel appointment, COI override, and statutory decision) writes an immutable record to the `audit_events` table recording:
  - Timestamp in UTC and IST.
  - Actor ID, email, and assigned role.
  - Target entity type and ID.
  - Action code and narrative remarks.
  - Cryptographic state snapshot and client IP address.

---

# 29 Civic Precision UI Design System & Universal Light/Dark Theme

Built around the philosophy of **Civic Precision**, the user interface provides a dignified, distraction-free environment tailored for public sector operations:

### Curated Color Palette
- **Midnight Ink (`#152536`)**: Authoritative, high-contrast typography and masthead surfaces.
- **Meridian Teal (`#0E746B`)**: Primary action accent, interactive buttons, and progress indicators.
- **Cool Porcelain (`#F4F6F8`)**: Soft, glare-reducing light background canvas.
- **Amber Warning (`#C5892B`)**: Cautionary indicators, approaching deadlines, and deficiency warnings.
- **Signal Red (`#B9474F`)**: Critical alerts, SLA breaches, and statutory rejections.
- **Slate Borders (`#DFE5E9`)**: Subtle structural dividers ensuring crisp card hierarchy.

### Accessible Dual-Theme Parity
- Full Light and Dark mode parity governed by centralized CSS variables mapped into Tailwind configuration (`var(--brand-*)`).
- Anti-flash pre-hydration script eliminates wrong-theme flicker during page loads.
- Fully responsive across 320px mobile viewports up to 4K desktop command centers.

---

# 30 Interactive Judge Demonstration Explorer

To provide evaluators with immediate, hands-on verification of complex regulatory workflows without manual data entry, the platform includes a built-in **Judge Demonstration Explorer** (`/demo/explorer`):
- **Five Pre-Configured Demonstration Tracks**:
  1. *Track 1 (New Technical Institution)*: Guides evaluators through the `SCRUTINY_EVC` pathway, mandatory EVC panel appointment, and field inspection.
  2. *Track 2 (Annual EOA Scrutiny-Only)*: Demonstrates the accelerated `ONLY_SCRUTINY` pathway bypassing physical EVC directly to the decision desk.
  3. *Track 3 (Deficiency Cure & Resubmission Loop)*: Demonstrates the complete deficiency lifecycle—memo issuance, institutional cure submission, and RO verification.
  4. *Track 4 (Compliance Passport & Deadline Escalation)*: Demonstrates post-approval undertakings, automated deadline scans, and progressive multi-tier escalation triggers.
  5. *Track 5 (Competent Authority Decision Desk)*: Demonstrates prerequisite verification, statutory decision execution, and QR-verifiable PDF order generation.
- **State Reset Mechanism**: Evaluators can reset synthetic demonstration data to its pristine initial state with a single click, enabling repeatable, deterministic testing.
- **Production Fail-Closed Guard**: In production environments (`ENVIRONMENT=production` or `DEMO_MODE=false`), all demo exploration endpoints fail closed with HTTP 403 Forbidden.

---

# 31 Step-by-Step End-to-End Evaluation Walkthrough

Evaluators can verify the complete regulatory lifecycle using the following 8-step journey on the live deployment ([https://avedansetu.vercel.app](https://avedansetu.vercel.app)):

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    END-TO-END EVALUATION JOURNEY SEQUENCE                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  [Step 1: Login] ──> Select persona (e.g. RO Western) via Quick Switcher        │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 2: Scrutiny] ──> Open App #AICTE-2026-REV-77192, review, issue memo      │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 3: Cure] ──> Switch to Institution Admin, provide cure remarks & proof   │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 4: Verify] ──> Switch back to RO Western, sign off scrutiny completion    │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 5: EVC Panel] ──> Switch to EVC Coordinator, run COI check, assign     │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 6: Field App] ──> Open Mobile Field App, verify GPS, upload photos       │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 7: Decision] ──> Switch to Competent Authority, issue Statutory Order    │
│          │                                                                      │
│          ▼                                                                      │
│  [Step 8: Audit] ──> Scan QR code on generated PDF, verify SHA-256 in Ledger    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Step 1: Authenticate via Persona Quick-Switcher**: Access `/login` and select the pre-configured persona **Regional Officer (RO Western - Dr. Sanjay Deshmukh)**.
2. **Step 2: Scrutiny & Deficiency Issuance**: In the **Regional Command Center**, open application `AICTE-2026-REV-77192`. Review the submitted files and issue an itemized deficiency notice for *"Land carpet area documentation deficiency"*. Status advances to `DEFICIENCY_COMMUNICATED`.
3. **Step 3: Institutional Cure & Resubmission**: Switch persona to **Institution Admin (Apex Institute)**. Navigate to **Action Centre**, enter specific cure remarks, upload supporting documentation, and click *Resubmit Application*. Status advances to `RESUBMITTED`.
4. **Step 4: Scrutiny Sign-Off**: Switch back to **RO Western**. Review the cured evidence, confirm satisfaction, and click *Complete Scrutiny*. Status advances to `AWAITING_EVC_SCHEDULE`.
5. **Step 5: EVC Panel Appointment & COI Evaluation**: Switch persona to **EVC Coordinator (Prof. K. Raman)**. Open **EVC Coordination Desk**. Select the application, evaluate candidate experts, verify the automated Conflict-of-Interest clearance, and appoint the panel. Status advances to `EVC_SCHEDULED`.
6. **Step 6: Mobile Field Inspection**: Navigate to `/officer/evc/field/:id`. Execute campus check-in (verifying GPS coordinates), complete the 5-point APH checklist, upload inspection photographs, and submit the visit report recommending approval. Status advances to `EVC_COMPLETED` $\rightarrow$ `AWAITING_COMPETENT_AUTHORITY`.
7. **Step 7: Competent Authority Statutory Order**: Switch persona to **Competent Authority (Dr. Ramesh Chandra)**. Review the consolidated docket (Scrutiny Verified + EVC Recommended Approval). Execute the statutory order by selecting **Grant Approval** with official remarks. Status advances to `APPROVED`.
8. **Step 8: Dynamic QR Verification & Audit Ledger**: Click *Generate Statutory Order Artifact*. View the generated PDF order, scan the embedded QR code with a smartphone camera, and verify the persisted institutional approval details and SHA-256 document checksum.

---

# 32 API Surface, Schema Validation & Integration Boundaries

The backend exposes a clean, fully typed RESTful API documented via OpenAPI at `/docs`:
- `/api/auth`: Login, logout, session verification, active role switching, and token blacklist management.
- `/api/applications`: Scoped application querying, detailed dossier retrieval, guarded state machine mutations, and deficiency cure submissions.
- `/api/evc`: Inspection roster querying, expert profile registry, automated COI assessments, appointment dispatch, mobile check-in, and report filing.
- `/api/compliance`: Compliance Passport obligations, evidence upload, Regional Officer verification desk, and correction requests.
- `/api/documents`: Multi-year Document Vault records, renewal submissions, SHA-256 verification, and local PDF document intelligence scans.
- `/api/notifications`: Transactional outbox querying, SSE stream ticket issuance, channel telemetry, and manual message retry.
- `/api/orders`: Statutory decision order generation, PDF binary downloads, and dynamic QR token verification.
- `/api/reports`: Seven executive analytical reporting endpoints, comparative regional benchmarks, and sanitized CSV exports.
- `/api/rules`: Regulatory Rule Studio policy lifecycle management, rule validation, and dry-run execution.
- `/api/demo`: Judge Demonstration Explorer scenario inspection and deterministic state resets.

---

# 33 Deployment Architecture, Docker Orchestration & Multi-Stage Release

ReguFlow 360 supports both containerized micro-services and cloud-native serverless deployments:
- **Cloud Production Topology**:
  - *Frontend Application*: Deployed on **Vercel** edge infrastructure with global CDN caching and automatic HTTPS.
  - *API Engine*: Deployed on **Render Cloud** running Python 3.12 with Uvicorn async workers.
  - *Authoritative Database*: Managed **PostgreSQL 16** with SSL encryption, automated WAL archiving, and daily snapshots.
- **Docker Production Orchestration (`docker-compose.prod.yml`)**:
  - Implements a dedicated one-shot `migration` service running `alembic upgrade head`. The backend API service waits for migration completion (`condition: service_completed_successfully`), preventing concurrent DDL lock races.
  - Isolates database ports strictly to internal Docker bridge networking, exposing zero database ports to the public host.

---

# 34 Operational Readiness, Release Engineering & Observability

Deep operational observability is built directly into the core platform:
- **Comprehensive Health Probes (`/api/health`)**: Reports sub-millisecond database ping latencies, connection pool statistics, background scheduler thread status, distributed leaseholder telemetry, and scan staleness.
- **Dedicated Orchestrator Probes**: Exposes dual `/health/liveness` and `/health/readiness` endpoints mounted at both root and `/api` levels for universal compatibility with Kubernetes, Docker Compose, and cloud load balancers.
- **Distributed Scheduler Leases**: When multiple backend API workers run concurrently, background deadline scans coordinate via the `scheduler_leases` table, ensuring mutual exclusion and preventing overlapping scan executions.

---

# 35 Comprehensive Testing Strategy & Verified Quality Evidence

Every capability within ReguFlow 360 is validated through automated test suites:
- **Backend Test Suite (Pytest)**: **236 Tests Passing (100% Pass Rate)** spanning 15 specialized test modules:
  - `test_workflow.py`: Guarded state transitions, optimistic concurrency, and deficiency cure validation.
  - `test_auth.py`: JWT issuance, active-role switching, and token blacklist revocation.
  - `test_regional_isolation.py`: Regional Officer and institutional multi-tenant boundary enforcement.
  - `test_evc_coi.py`: Automated conflict-of-interest checks, cooling-off intervals, and invitation lifecycles.
  - `test_deadlines.py`: Stage SLAs, undertaking due dates, document validity, and idempotency deduplication.
  - `test_outbox.py`: Transactional outbox commits, retry backoff, and dead-letter queue transitions.
  - `test_orders.py`: Competent Authority order exclusivity, PDF artifact generation, and QR verification.
  - `test_rule_studio.py`: Regulatory policy versioning, dry-run simulation, and audit export sanitization.
- **Frontend Test Suite (Vitest)**: **42 Tests Passing** verifying component rendering, responsive navigation drawers, theme switching, and form validation.
- **Static Code Quality**: Strict TypeScript compilation (`tsc --noEmit`) and ESLint pass with **0 errors and 0 warnings**.

---

# 36 Government Adoption Model & AICTE Operating Blueprint

To facilitate seamless real-world adoption by the All India Council for Technical Education, ReguFlow 360 is architected for phased integration:
1. **Phase 1: Shadow Operation & Sandbox Rehearsal (Months 1–2)**: Deploy ReguFlow 360 in parallel with existing portals for a single regional directorate (e.g., Western Region). Regional officers and select institutions operate in shadow mode to calibrate SLA thresholds and rule templates.
2. **Phase 2: Single-Region Pilot Deployment (Months 3–4)**: Transition one full regional office to primary processing for Extension of Approval (EOA) and Document Vault renewals. Connect government SMTP relays and test SMS gateways.
3. **Phase 3: National Rollout & SSO Federation (Months 5–6)**: Integrate with Government of India single sign-on (**Parichay / MeriPehchan**), onboard all regional directorates, and enable digital signature certificate (DSC) signing for official orders.

---

# 37 Impact Framework, Efficiency Metrics & Measurable Outcomes

Implementing ReguFlow 360 across AICTE operations projects transformative improvements in regulatory efficiency:

| Operational Dimension | Traditional Administrative Baseline | ReguFlow 360 Target / Outcome | Projected Efficiency Gain |
|---|---|---|---|
| **Deficiency Cure Cycle** | 21–30 calendar days via ad-hoc correspondence | **5–7 calendar days** via itemized cure desk | **75% Reduction in Cure Delays** |
| **EVC Panel Formation** | 10–14 days manual academician search | **Instant COI clearance (< 1 min)** | **90% Faster Panel Appointment** |
| **Post-Approval Monitoring** | Episodic, unmonitored covenants | **100% Real-Time Passport Tracking** | **Complete Elimination of Compliance Blindspot** |
| **Document Expiry Notice** | Reactive notice after expiry has occurred | **Proactive alerts at T-90, T-60, T-30 days**| **95% Reduction in Lapsed Leases / NOCs** |
| **Audit Dossier Assembly** | 2–3 days manual file collation | **Instant Single-Click Audit Reconstruction** | **100% Real-Time Audit Readiness** |

---

# 38 Strategic Roadmap & National Integration Horizons

### Horizon 1 (Immediate Post-Hackathon)
- Connect with Government of India **Parichay / MeriPehchan** SAML 2.0 / OAuth 2.0 Single Sign-On infrastructure.
- Integrate licensed Indian Electronic Signature Service (**eSign / DSC**) under the Controller of Certifying Authorities (CCA) framework for legally binding digital signatures on approval orders.

### Horizon 2 (Near-Term Expansion)
- Integrate with **DigiLocker** national document repository for automated verification of municipal building permits, fire safety certificates, and land titles.
- Implement specialized offline mobile synchronization for field inspectors operating in remote, low-connectivity rural campuses.

### Horizon 3 (Long-Term Strategic Innovations)
- Machine learning-assisted spatial verification analyzing satellite imagery to monitor campus land boundary encroachments over 33-year lease horizons.
- Cross-regulatory interoperability APIs connecting AICTE approval dossiers with National Board of Accreditation (NBA) and NIRF institutional ranking platforms.

---

# 39 Risk Matrix, Operational Limitations & Technical Mitigations

| Operational Risk | Potential Impact | Technical Mitigation Implemented in ReguFlow 360 |
|---|---|---|
| **Concurrent Document Updates** | Lost updates or overwritten scrutiny findings | Enforced **Optimistic Concurrency Control** (`expected_version`), aborting conflicting writes with HTTP 409. |
| **Alert Fatigue & Duplicate Notices** | Officers and institutions ignore spam notifications | Enforced **Composite Idempotency Keys**, guaranteeing zero duplicate alerts per deadline threshold. |
| **Compromised Field Inspections** | Biased panels or fraudulent remote check-ins | Enforced **Automated COI Engine** (trust, affiliation, cooling-off) and **Geotagged Browser Check-Ins**. |
| **Database Network Exposure** | Public scanning and unauthorized data probes | Database ports bound strictly to **Loopback (127.0.0.1)** in development and **Internal Bridge** in production. |
| **CSV Spreadsheet Exploits** | Malicious formula injection via institution names | Enforced **CSV Formula Sanitization**, escaping leading `=`, `+`, `-`, and `@` characters. |

---

# 40 Recommended Pilot Implementation & Phased Rollout Plan

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     RECOMMENDED 12-WEEK PILOT TIMELINE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Weeks 1–2: Infrastructure Provisioning, Secret Rotation & DB Sizing             │
│ Weeks 3–4: Ingestion of Regional Master Data & Policy Template Configuration    │
│ Weeks 5–6: Stakeholder Orientation (RO Scrutiny Teams & EVC Coordinators)      │
│ Weeks 7–8: Shadow Pilot Execution alongside Existing Portals (Western Region)   │
│ Weeks 9–10: SLA Threshold Calibration, Outbox Audit & Gateway Verification      │
│ Weeks 11–12: Formal Pilot Evaluation Report & National Cutover Decision         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# 41 Glossary of Regulatory & Engineering Terms

- **Approval Process Handbook (APH)**: The official statutory document published by AICTE laying down legal norms, faculty ratios, space requirements, and procedural guidelines for technical institutions.
- **Deficiency Cure Loop**: The structured, itemized mechanism allowing institutions to respond to specific scrutiny shortcomings with explanatory remarks and evidence files within a strict statutory window.
- **Expert Visiting Committee (EVC)**: A committee of senior academicians appointed by AICTE to conduct physical on-site or virtual verifications of institutional infrastructure, laboratories, and safety amenities.
- **Conflict of Interest (COI)**: Any academic, financial, trust-level, or personal relationship between an appointed inspector and the inspected institution that could compromise regulatory objectivity.
- **Compliance Passport**: A continuous digital monitoring ledger tracking institutional fulfilment of time-bound conditions and statutory covenants following initial approval.
- **Optimistic Concurrency Control (OCC)**: A database design pattern preventing lost updates in multi-user systems by validating that an entity's version has not changed prior to committing mutations.
- **Transactional Outbox**: An enterprise architectural pattern where business state updates and corresponding notification requests commit in the same database transaction, guaranteeing reliable message dispatch.

---

# 42 Acronyms, Regulatory Standards & Bibliographic Citations

### Acronyms
- **AICTE**: All India Council for Technical Education
- **APH**: Approval Process Handbook
- **COI**: Conflict of Interest
- **EOA**: Extension of Approval
- **EVC**: Expert Visiting Committee
- **NOC**: No Objection Certificate
- **OCC**: Optimistic Concurrency Control
- **RO**: Regional Office / Regional Officer
- **BO**: Bureau Officer (AICTE Headquarters)
- **SAC / SHC**: Standing Appellate Committee / Standing Hearing Committee
- **SIH**: Smart India Hackathon
- **SLA**: Service Level Agreement
- **SSE**: Server-Sent Events

### Standards & References
1. **All India Council for Technical Education (AICTE)**, *Approval Process Handbook (APH) 2024–25 to 2026–27*, New Delhi, India. [Online Available: [aicte-india.org](https://www.aicte-india.org)]
2. **Ministry of Electronics and Information Technology (MeitY)**, *eSign Online Electronic Signature Service Guidelines*, Controller of Certifying Authorities (CCA), Government of India.
3. **National Informatics Centre (NIC)**, *Parichay: Government of India Single Sign-On Identity Platform Specifications*, New Delhi, India.

---

# 43 Conclusion: Building a Transparent, Accountable Regulatory Future

ReguFlow 360 (आवेदनसेतु | AvedanSetu), engineered by **Team TechTitans 2.0** for **SIH 2026 Problem Statement 26262**, represents a transformative shift in higher education regulatory governance. By bridging pre-approval scrutiny, conflict-free inspection logistics, post-approval compliance undertakings, multi-year document validity tracking, and hierarchical deadline escalations into a single, cohesive, and auditable operational ecosystem, the platform demonstrates that regulatory rigor and administrative efficiency can co-exist harmoniously.

With its robust state-machine foundation, defense-in-depth security, strict human sovereignty, 100% verified test coverage, responsive dual-theme user experience, and interactive demonstration explorer, ReguFlow 360 stands fully prepared for evaluation, pilot onboarding, and national regulatory deployment.

---

*Submitted with pride by **Team TechTitans 2.0** (Team ID: 197859), KIET Deemed to be University, for the Smart India Hackathon (SIH 2026).*
