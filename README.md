# आवेदनसेतु (AvedanSetu) | ReguFlow 360
### Integrated AICTE Approval Workflow Automation, Compliance Monitoring, Document Validity & Multi-Tier Alert Management System

<div align="center">

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH_2026-Problem_Statement_26262-0E746B?style=for-the-badge&logo=gov.uk&logoColor=white)](https://www.sih.gov.in/)
[![Live Web Portal](https://img.shields.io/badge/Live_Portal-avedansetu.vercel.app-152536?style=for-the-badge&logo=vercel&logoColor=white)](https://avedansetu.vercel.app)
[![Production API Docs](https://img.shields.io/badge/API_Docs-Swagger_UI-0284C7?style=for-the-badge&logo=fastapi&logoColor=white)](https://reguflow-backend.onrender.com/docs)
[![YouTube Video Demo](https://img.shields.io/badge/Video_Demo-YouTube_Walkthrough-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=1zidGymZ5VM)
[![Master Technical Dossier](https://img.shields.io/badge/Google_Docs-Technical_Dossier-4285F4?style=for-the-badge&logo=googledocs&logoColor=white)](https://docs.google.com/document/d/1cWmb5WSjq3zaJfsF_mbcQczPFOx3Vbyv17jt-bHNDXg/edit?tab=t.0)

<br/>

[![Backend Test Suite](https://img.shields.io/badge/Backend_Pytest-258%2F258_Passing_(100%25)-success?style=flat-square&logo=pytest)](./backend/tests)
[![Frontend Test Suite](https://img.shields.io/badge/Frontend_Tests-42%2F42_Passing_(100%25)-success?style=flat-square&logo=node.js)](./frontend/src/__tests__)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict_Checked_0_Errors-3178C6?style=flat-square&logo=typescript&logoColor=white)](./frontend/tsconfig.json)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](./backend)
[![React](https://img.shields.io/badge/Frontend-React_18.3%2B_Vite_5-61DAFB?style=flat-square&logo=react&logoColor=black)](./frontend)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Theme Architecture](https://img.shields.io/badge/Design_System-Civic_Precision_Dual_Theme-0E746B?style=flat-square)](./docs/ui-design-system.md)
[![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](./LICENSE)

**Engineered by Team TechTitans 2.0 (Team ID: 197859) • KIET Deemed to be University, Delhi-NCR, Ghaziabad**  
*Submitted for Smart India Hackathon (SIH 2026) — Ministry of Education & AICTE*

</div>

---

## 📌 Quick Access & Evaluation Links

| Resource | Target Link | Description |
|---|---|---|
| 🌐 **Live Web Portal** | [https://avedansetu.vercel.app](https://avedansetu.vercel.app) | Production web application deployed on Vercel with responsive dual-theme Civic Precision UI |
| ⚙️ **Production Backend API** | [https://reguflow-backend.onrender.com](https://reguflow-backend.onrender.com) | Live containerized FastAPI backend on Render Cloud |
| 📖 **Interactive API Docs** | [https://reguflow-backend.onrender.com/docs](https://reguflow-backend.onrender.com/docs) | Interactive OpenAPI 3.1 Swagger UI testing all regulatory endpoints |
| 📺 **YouTube Video Demonstration** | [https://www.youtube.com/watch?v=1zidGymZ5VM](https://www.youtube.com/watch?v=1zidGymZ5VM) | Comprehensive end-to-end walkthrough demonstrating all 8 role workspaces and workflows |
| 📄 **Master System Technical Dossier** | [Google Docs Master System Dossier](https://docs.google.com/document/d/1cWmb5WSjq3zaJfsF_mbcQczPFOx3Vbyv17jt-bHNDXg/edit?tab=t.0) | Complete official technical submission dossier detailing compliance, architecture, and evidence |
| 🩺 **Live Telemetry & Health Probe** | [https://reguflow-backend.onrender.com/api/health](https://reguflow-backend.onrender.com/api/health) | Real-time orchestrator diagnostics, DB ping latency, and scheduler lease status |
| 🐙 **Source Code Repository** | [https://github.com/Saksham2005-coder/sih](https://github.com/Saksham2005-coder/sih) | Official GitHub repository maintaining continuous verification on `main` branch |

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Key System Architectural Diagrams](#2-key-system-architectural-diagrams)
   - [A. End-to-End System Architecture](#a-end-to-end-system-architecture)
   - [B. Route-Aware Regulatory State Machine Flowchart](#b-route-aware-regulatory-state-machine-flowchart)
   - [C. EVC 4-Way Conflict-of-Interest (COI) Engine](#c-evc-4-way-conflict-of-interest-coi-engine)
   - [D. Multi-Vector Deadline Scanner & Escalation Ladder](#d-multi-vector-deadline-scanner--escalation-ladder)
   - [E. Continuous Compliance Passport & Document Vault Lifecycle](#e-continuous-compliance-passport--document-vault-lifecycle)
3. [The 8 Dedicated Role Workspaces](#3-the-8-dedicated-role-workspaces)
4. [Demo Personas & Evaluation Credentials](#4-demo-personas--evaluation-credentials)
5. [Core Engineering Innovations](#5-core-engineering-innovations)
6. [Complete Technology Stack](#6-complete-technology-stack)
7. [Local Setup & Quick Start Guide](#7-local-setup--quick-start-guide)
8. [Docker & Production Deployment](#8-docker--production-deployment)
9. [Automated Quality Verification & Test Evidence](#9-automated-quality-verification--test-evidence)
10. [Source of Truth Documentation Directory](#10-source-of-truth-documentation-directory)
11. [Team Information & Institutional Credits](#11-team-information--institutional-credits)

---

## 1. Executive Summary & Problem Statement

### The Problem (SIH 2026 Problem Statement 26262)
Technical education in India operates under the regulatory stewardship of the **All India Council for Technical Education (AICTE)**. Every annual approval cycle involves thousands of institutions applying for Extension of Approval (EoA), new institutions, program additions, or seat quota variations governed by the **Approval Process Handbook (APH)**.

Historically, this massive regulatory operation has been constrained by five systemic operational bottlenecks:
1. **Opaque Stage Pendency & Sliced Communication:** Institutional deficiency memos and cure documents were exchanged via disjointed channels, leading to protracted back-and-forth loops with zero visibility into SLA ageing.
2. **Delayed EVC Scheduling & Undetected Conflicts of Interest:** Expert Visiting Committee (EVC) panel formation lacked automated cross-referencing against parent trusts, institutional affiliations, and 3-year cooling-off windows, risking compromised site visits.
3. **The "Post-Approval Compliance Blindspot":** Statutory approvals are frequently granted subject to mandatory covenants (e.g. barrier-free ramps, specialized AI labs, anti-ragging councils). Historically, post-approval undertakings slipped through administrative cracks.
4. **Multi-Year Document Expiry Hazards:** Critical regulatory assets—such as 33-year registered land lease deeds, structural stability certificates, and annual municipal fire safety NOCs—carry independent validity timelines that often expire unnoticed outside annual approval cycles.
5. **Alert Fatigue & Unmonitored SLA Breaches:** Disjointed notifications caused alert fatigue, while critical statutory deadline breaches failed to escalate hierarchically to Regional Officers, Bureau Chiefs, and the Member Secretary.

### The Solution: आवेदनसेतु (AvedanSetu) / ReguFlow 360
**AvedanSetu** is an enterprise-grade regulatory workflow automation, continuous compliance monitoring, and multi-tier alert escalation platform. Engineered upon a cohesive **Modular Monolith** pattern, it bridges institutions, regional directorates, inspection experts, standing hearing committees, and apex authorities over a single unified, auditable relational database.

- **Guarded State Machine:** Mathematically sound, route-aware stage transitions with monotonic optimistic concurrency locking (`HTTP 409 Conflict`).
- **Eight Distinct Role Workspaces:** Eliminates generic dashboards; every stakeholder gets an interface tailored to their exact statutory mandate.
- **Explainable Conflict-of-Interest (COI) Engine:** Evaluates proposed EVC inspection panels against 4 automated cross-checks with auditable override justification.
- **Mobile-First Field Inspection Desk:** Real-time browser GPS coordinate verification, 5-point APH checklist, and SHA-256 tamper-evident photo sealing.
- **Continuous Compliance Passport:** Real-time covenant tracking with multi-version digital evidence dossiers (`v1` → `v2`) and regional officer verification desks.
- **Multi-Vector Deadline Engine:** Automated background scans computing localized `Asia/Kolkata` date boundaries and triggering deduplicated multi-tier escalations (`REMINDER_L1` to `ESCALATION_L3_MEMBER_SEC`).
- **Transactional Outbox & Live SSE:** Zero dropped notifications via transactional database commits, bounded exponential backoff, and live Server-Sent Events with fallback polling.
- **Verifiable Statutory Orders:** Dynamic ReportLab PDF compilation with cryptographic SHA-256 digests and scannable verification QR codes.

---

## 2. Key System Architectural Diagrams

### A. End-to-End System Architecture

```mermaid
graph TB
    subgraph ClientLayer ["1. Presentation Layer (React 18 + Strict TypeScript + Vite)"]
        UI_Inst["Institution Portal<br/>(/institution/dashboard)"]
        UI_RO["Regional Command<br/>(/officer/regional-workspace)"]
        UI_BO["Apex Bureau Desk<br/>(/officer/bureau-workspace)"]
        UI_EVC["EVC Studio & Mobile App<br/>(/officer/evc/field/:id)"]
        UI_SAC["Committee Hearing Desk<br/>(/officer/committee-workspace)"]
        UI_CA["Competent Authority<br/>(/officer/authority-workspace)"]
        UI_Admin["Rule Studio & Telemetry<br/>(/officer/admin-workspace)"]
        Theme["Civic Precision Design System<br/>(Porcelain Light #F4F6F8 / Obsidian Dark #101820)"]
    end

    subgraph GatewayLayer ["2. Application Gateway & Security Perimeter (FastAPI 0.110+)"]
        JWT["JWT Bearer Authenticator<br/>(Argon2/BCrypt, Database Blacklist)"]
        RBAC["Hierarchical RBAC / ABAC Interceptors<br/>(verify_institution_access, verify_regional_access)"]
        Pydantic["Pydantic v2 Schema Sanitization<br/>(Strict Validation & ConfigDict)"]
        SSEBroker["Real-Time SSE Event Broker<br/>(/api/notifications/stream)"]
    end

    subgraph ServiceLayer ["3. Specialized Business Domain Services"]
        WF["WorkflowEngine<br/>State Machine & Route Routing"]
        EVC_SVC["EVCService<br/>4-Way COI Engine & Field Roster"]
        COMP_SVC["ComplianceService<br/>Covenants & Document Vault"]
        DOC_INTEL["DocumentIntelligence<br/>pypdf Parser & Excerpt Grounding"]
        DL_SVC["DeadlineEngine<br/>Multi-Vector Scanner & Deduplication"]
        PRIO_SVC["PriorityService<br/>Deterministic 0-100 Queue Triage"]
        ORDER_SVC["OrderGenerationService<br/>ReportLab PDF & Verifiable QR"]
        OUTBOX_SVC["NotificationOutboxDispatcher<br/>Transactional Outbox & Bounded Retry"]
        RULE_SVC["RuleStudioService<br/>Versioned Policy Sandbox & Sim"]
    end

    subgraph DataLayer ["4. Persistence, Audit & Distributed Storage Tier"]
        DB[(PostgreSQL 16 Relational Engine<br/>Row-Level Locks: FOR UPDATE SKIP LOCKED)]
        Alembic["Alembic DDL Migrations<br/>(Sequential One-Shot Execution)"]
        AuditLedger["Immutable Relational Audit Ledger<br/>(Non-repudiable audit_events)"]
        Leases["Distributed Coordination Leases<br/>(scheduler_leases Table)"]
        Vault["Secure Storage Vault<br/>(UUID Filenames & SHA-256 Checksums)"]
    end

    ClientLayer ==> GatewayLayer
    GatewayLayer ==> ServiceLayer
    ServiceLayer ==> DataLayer

    style ClientLayer fill:#F4F6F8,stroke:#152536,stroke-width:2px,color:#152536
    style GatewayLayer fill:#E6FFFA,stroke:#0E746B,stroke-width:2px,color:#0E746B
    style ServiceLayer fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A
    style DataLayer fill:#FDF2F8,stroke:#9D174D,stroke-width:2px,color:#831843
```

---

### B. Route-Aware Regulatory State Machine Flowchart

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Institution Creates Application
    DRAFT --> SUBMITTED: Institution Submits Dossier

    state Scrutiny_Stage {
        SUBMITTED --> UNDER_SCRUTINY: RO Commences Scrutiny
        UNDER_SCRUTINY --> DEFICIENCY_COMMUNICATED: RO Issues Itemized Defects
        DEFICIENCY_COMMUNICATED --> RESUBMITTED: Institution Submits Itemized Cures
        RESUBMITTED --> UNDER_SCRUTINY: RO Re-examines Cure Evidence
        UNDER_SCRUTINY --> SCRUTINY_COMPLETED: Scrutiny Cleared (0 Deficiencies)
    }

    state Route_Branching <<choice>>
    SCRUTINY_COMPLETED --> Route_Branching: Route Evaluation

    Route_Branching --> AWAITING_COMPETENT_AUTHORITY: Route 1: ONLY_SCRUTINY (e.g. Annual EoA)
    Route_Branching --> AWAITING_EVC_SCHEDULE: Routes 2 & 3: SCRUTINY_EVC / EVC_SAC_SHC

    state EVC_Inspection_Cycle {
        AWAITING_EVC_SCHEDULE --> EVC_SCHEDULED: EVC Coord Selects 4-Way COI-Cleared Panel
        EVC_SCHEDULED --> IN_PROGRESS: Experts Arrive (GPS Geotagged Check-In)
        IN_PROGRESS --> EVC_COMPLETED: Panel Submits Sealed Report & Recommendation
    }

    state Post_EVC_Branching <<choice>>
    EVC_COMPLETED --> Post_EVC_Branching: Route Evaluation
    
    Post_EVC_Branching --> AWAITING_SAC_CAC_REVIEW: Route 3: EVC_SAC_SHC (Dispute / Hearing)
    AWAITING_SAC_CAC_REVIEW --> AWAITING_COMPETENT_AUTHORITY: Committee Records Hearing Findings
    Post_EVC_Branching --> AWAITING_COMPETENT_AUTHORITY: Route 2 Cleared

    state Statutory_Determination {
        AWAITING_COMPETENT_AUTHORITY --> APPROVED: Authorized Order Signed (QR Code Generated)
        AWAITING_COMPETENT_AUTHORITY --> REJECTED: Rejection Order Issued with Statutory Grounds
    }

    APPROVED --> Compliance_Passport: Mandatory Covenants Issued
    REJECTED --> [*]: Case Closed
    Compliance_Passport --> [*]: Ongoing Monitoring
```

---

### C. EVC 4-Way Conflict-of-Interest (COI) Engine

```mermaid
flowchart TD
    Start([EVC Coordinator Selects Candidate Expert]) --> Check1{1. Current Affiliation Check}
    
    Check1 -- Expert employed by Applicant Institution --x|FAIL: AFFILIATION_CONFLICT| ConflictDetected[Assignment Blocked<br/>Flagged CONFLICT_DETECTED]
    Check1 -- Clear --> Check2{2. Parent Trust / Society Check}

    Check2 -- Expert institution shares same Parent Trust --x|FAIL: PARENT_TRUST_CONFLICT| ConflictDetected
    Check2 -- Clear --> Check3{3. 3-Year Cooling-Off Check}

    Check3 -- Inspected this institution within 36 months --x|FAIL: COOLING_OFF_ACTIVE| ConflictDetected
    Check3 -- Clear --> Check4{4. Declared Personal Dispute}

    Check4 -- Active dispute or personal relationship logged --x|FAIL: DECLARED_CONFLICT| ConflictDetected
    Check4 -- Clear --> Cleared[Expert Verified Clear<br/>Status: ELIGIBLE]

    ConflictDetected --> OverrideDecision{Coordinator Override?}
    OverrideDecision -- No --> Reassign[Reassign Different Expert from Roster]
    OverrideDecision -- Yes (Specialized Scarcity) --> MandatoryJustification[Mandatory Substantive Justification<br/>Immutably Written to Audit Ledger]
    MandatoryJustification --> Cleared

    Cleared --> Appoint[Panel Appointed & Invited<br/>Status: EVC_SCHEDULED]

    style ConflictDetected fill:#FEE2E2,stroke:#B9474F,stroke-width:2px,color:#991B1B
    style Cleared fill:#DCFCE7,stroke:#16A34A,stroke-width:2px,color:#166534
    style MandatoryJustification fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#92400E
```

---

### D. Multi-Vector Deadline Scanner & Escalation Ladder

```mermaid
flowchart LR
    subgraph TriggerSources ["1. Autonomous Scanners"]
        T1["Stage Scrutiny SLA<br/>(14 Days Limit)"]
        T2["Deficiency Cure Window<br/>(10 Days Limit)"]
        T3["Compliance Undertaking<br/>(Due Date T+60d/T+180d)"]
        T4["Document Vault Expiry<br/>(T-90d, T-60d, T-30d)"]
    end

    subgraph Scanner ["2. Background Coordinator"]
        Lease{"scheduler_leases<br/>Lease Acquired?"}
        ScanEngine["Multi-Vector Scanner<br/>Asia/Kolkata Calendar Bound"]
        IdemGen["Idempotency Key Generator<br/>MD5(id + type + days + level)"]
    end

    subgraph EscalationLadder ["3. Hierarchical Deduplicated Escalations"]
        L1["REMINDER_L1<br/>(Advance Notice: T-7 Days)"]
        L2["REMINDER_L2<br/>(Urgent Notice: T-2 Days)"]
        E1["ESCALATION_L1_RO<br/>(Regional Officer: T+1 Day Overdue)"]
        E2["ESCALATION_L2_BO<br/>(Apex Bureau Chief: T+7 Days Overdue)"]
        E3["ESCALATION_L3_MEMBER_SEC<br/>(Member Secretary: T+14 Days Overdue)"]
    end

    subgraph Delivery ["4. Outbox & Streaming"]
        Outbox["Transactional Outbox<br/>(FOR UPDATE SKIP LOCKED)"]
        SSE["Real-Time SSE Stream<br/>(/api/notifications/stream)"]
        Fallback["25s Resilient Polling"]
    end

    TriggerSources --> Lease
    Lease -- Yes --> ScanEngine --> IdemGen
    IdemGen --> L1 --> L2 --> E1 --> E2 --> E3
    EscalationLadder --> Outbox --> SSE & Fallback

    style EscalationLadder fill:#FFFBEB,stroke:#C5892B,stroke-width:2px,color:#92400E
    style Delivery fill:#EFF6FF,stroke:#1D4ED8,stroke-width:2px,color:#1E40AF
```

---

### E. Continuous Compliance Passport & Document Vault Lifecycle

```mermaid
stateDiagram-v2
    state Compliance_Passport {
        [*] --> NOT_YET_DUE: Approval Covenants Issued
        NOT_YET_DUE --> DUE_SOON: Threshold Reached (T-15 Days)
        DUE_SOON --> PENDING_VERIFICATION: Institution Uploads Evidence v1
        
        state Officer_Verification {
            PENDING_VERIFICATION --> VERIFIED: RO Approves Proof
            PENDING_VERIFICATION --> CORRECTION_REQUIRED: RO Requests Remediation
            CORRECTION_REQUIRED --> PENDING_VERIFICATION: Institution Uploads Evidence v2
            PENDING_VERIFICATION --> DEFICIENT: Material Non-Compliance
        }

        DUE_SOON --> OVERDUE: Due Date Passed (No Proof Uploaded)
        OVERDUE --> Escalation_Ladder: Escalated to Regional & Bureau Officers
    }

    state Document_Vault {
        [*] --> ACTIVE: Document Registered (e.g. 33-Year Land Lease)
        ACTIVE --> EXPIRING_SOON: Reaches T-90 / T-60 / T-30 Days
        EXPIRING_SOON --> RENEWAL_SUBMITTED: Institution Uploads Renewed Deed
        RENEWAL_SUBMITTED --> VERIFIED_DOC: RO Verifies Validity & Issues Endorsement
        VERIFIED_DOC --> ACTIVE: Promoted as Active Document
        EXPIRING_SOON --> EXPIRED: Expiry Date Passed Without Renewal
    }
```

---

## 3. The 8 Dedicated Role Workspaces

AvedanSetu strictly rejects generic, one-size-fits-all administrative consoles. Every canonical regulatory role operates within a purpose-built workspace:

| # | Role Canonical Name | Workspace Route | Statutory Mandate & Functional Scope |
|---|---|---|---|
| 1 | **Institution Administrator** | `/institution/dashboard` | End-to-end institutional docket management, application drafting, deficiency cure responses, renewal tracking, and authorized filings. Scoped strictly to own `institution_id`. |
| 2 | **Compliance Officer** | `/institution/compliance-workspace` | Institutional statutory compliance desk, post-approval covenants, multi-year document vault renewal submissions, and SHA-256 evidence dossiers. |
| 3 | **Regional Officer (RO)** | `/officer/regional-workspace` | Regional scrutiny queue, SLA priority triage, itemized deficiency memo issuance, resubmission sign-off, and compliance evidence verification. Scoped to assigned region (`Western`). |
| 4 | **Bureau Officer (BO)** | `/officer/bureau-workspace` | Apex national oversight, inter-regional SLA and pendency benchmarking, Tier-2 unresolved escalation queue (`ESCALATION_L2_BO`), and national performance heatmaps. |
| 5 | **Committee Member (SAC/CAC)** | `/officer/committee-workspace` | Standing hearing committee dockets, review of contested applications, inspection report evaluations, hearing deficiency issuance, and hearing observations. |
| 6 | **EVC Coordinator** | `/officer/evc-workspace` | Expert Visiting Committee scheduling desk, 4-way Conflict-of-Interest (COI) engine evaluations, Convener & Subject Expert assignment, and field visit rosters. |
| 7 | **Competent Authority (CA)** | `/officer/authority-workspace` | Exclusive statutory decision desk for applications in `AWAITING_COMPETENT_AUTHORITY`. Generates official gazette Approval/Rejection orders with dynamic QR verification. |
| 8 | **System Administrator** | `/officer/admin-workspace` | Platform telemetry, sub-millisecond database health probes, distributed scheduler lease controls, on-demand deadline execution, and formula-safe CSV audit ledger exports. |

---

## 4. Demo Personas & Evaluation Credentials

For seamless evaluation by SIH judges and evaluators, the development environment includes seeded demo credentials representing each canonical stakeholder:

| Persona Role | Login Email | Password | Scope Boundary & Assignment |
|---|---|---|---|
| **Institution Administrator** | `admin@apex.edu.in` | `Password123!` | Apex Institute of Technology (Western Region, Mumbai) |
| **Institution Compliance Officer** | `compliance@apex.edu.in` | `Password123!` | Apex Institute of Technology (Western Region, Mumbai) |
| **Institution Administrator (North)** | `admin@nier.edu.in` | `Password123!` | Northern Institute of Engineering & Research (Delhi) |
| **Regional Officer (RO)** | `ro.western@aicte.gov.in` | `Password123!` | AICTE Western Regional Directorate |
| **EVC Coordinator** | `evc.coord@aicte.gov.in` | `Password123!` | EVC National Inspection Desk |
| **Bureau Officer (BO)** | `bo.approval@aicte.gov.in` | `Password123!` | AICTE Apex Approval Bureau, New Delhi |
| **Committee Member (SAC/CAC)** | `committee.member@aicte.gov.in` | `Password123!` | Standing Scrutiny & Appellate Hearing Committee |
| **Competent Authority (CA)** | `member.sec@aicte.gov.in` | `Password123!` | Member Secretary / Apex Decision Authority |
| **System Administrator** | `sysadmin@aicte.gov.in` | `Password123!` | Central Platform Telemetry & System Administration |

> **Production Hardening Disclosure:** In production mode (`ENVIRONMENT=production` or `DEMO_MODE=false`), demo personas, one-click login chips, and synthetic database seeding are strictly disabled and fail closed (`HTTP 403 Forbidden`).

---

## 5. Core Engineering Innovations

### 1. Zero-Data-Loss Deployment Hydration
When deployed to serverless or containerized cloud platforms (such as Vercel and Render), AvedanSetu guarantees zero regulatory data loss:
- On cold boot, the backend lifecycle detects if the target PostgreSQL database is empty.
- It automatically hydrates the complete regulatory state from `snapshot_data.json`, restoring all 25 relational tables and resetting PostgreSQL primary key sequences (`setval`).
- All 42 demo applications, documents, covenants, and audit logs are immediately accessible on the live deployment.

### 2. Monotonic Optimistic Concurrency Control
To prevent write skew and lost updates when multiple officers review the same application queue simultaneously, all state mutation endpoints enforce monotonic versioning:
- Requests submit the client's `expected_version` integer.
- If another officer updated the record concurrently, the backend rejects the write with `HTTP 409 Conflict`, returning the latest database version.

### 3. Civic Precision Design System & Dual Theme Architecture
Built specifically for government applications demanding visual authority and clarity:
- **Light Theme (Cool Porcelain):** `#F4F6F8` canvas, `#FFFFFF` surfaces, `#152536` ink, `#DFE5E9` borders, and `#0E746B` Meridian Teal accent.
- **Dark Theme (Obsidian):** `#101820` canvas, `#1B2835` card surfaces, `#233342` elevated elements, and `#14B8A6` high-contrast teal.
- **Anti-Flash Pre-Hydration:** An inline script in `index.html` resolves stored preferences or system OS preference before the DOM paints, preventing wrong-theme flashes.

### 4. ReportLab PDF Orders with Dynamic Cryptographic QR Verification
Approved and rejected applications generate formal statutory gazette decision orders:
- Two-pass ReportLab engine computing total page counts (`Page X of Y`), signature blocks, and legal disclaimers.
- Scannable dynamic QR code resolving to public verification desk (`/verify/order?token=...`).
- Cross-verifies document authenticity using SHA-256 cryptographic file checksums, guaranteeing document integrity.

### 5. Mobile-First Field Inspection Desk
Inspectors in the field can access `/officer/evc/field/:id` directly from mobile browsers:
- Captures browser GPS coordinates and accuracy radius at check-in.
- Implements the 5-point APH Core Inspection Checklist (Land/Carpet Area, Computing & AI Labs, Library, Barrier-Free Access, Fire Safety).
- Attaches geotagged photographs hashed with SHA-256 into the immutable inspection docket.

### 6. CSV Formula-Injection Sanitization
All analytical exports and audit log CSV generators automatically prepend single quotes (`'`) to cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r`, eliminating spreadsheet formula execution exploits.

---

## 6. Complete Technology Stack

| Layer | Component | Technology Selected | Version | Purpose & Architectural Rationale |
|---|---|---|---|---|
| **Frontend** | Framework | **React** | 18.3.1 | Declarative, component-driven UI for complex regulatory workspaces |
| | Language | **TypeScript** | 5.3.3 | Strict type safety (`noImplicitAny`), preventing runtime undefined errors |
| | Build Tool | **Vite** | 5.4.21 | Lightning-fast HMR and optimized production bundling |
| | Styling | **Tailwind CSS** | 3.4.1 | Civic Precision design token encapsulation and dark-mode utilities |
| | State & Caching | **TanStack Query** | 5.28.4 | Server-state caching with automated persona-switch cache flushing |
| | Icons | **Lucide React** | 0.359.0 | Clean, accessible regulatory iconography |
| **Backend** | Framework | **FastAPI** | 0.110.0+ | High-throughput async framework with automatic OpenAPI 3.1 contracts |
| | Language | **Python** | 3.12+ | Modern syntax, robust typing, native async/await runtime |
| | Schemas | **Pydantic** | v2.6.4+ | Lightning-fast C-extension payload validation and response filtering |
| | ORM | **SQLAlchemy** | 2.0.28+ | Type-safe ORM supporting row-level locking (`FOR UPDATE SKIP LOCKED`) |
| | Migrations | **Alembic** | 1.13.1+ | Version-controlled, reproducible relational DDL migrations |
| | Auth & JWT | **Python-JOSE & BCrypt** | 3.3.0+ | Cryptographic token signing with database token blacklist support |
| | PDF Engine | **ReportLab & pypdf** | 4.0+ | Native PDF order compilation and local text extraction intelligence |
| **Database** | Production DB | **PostgreSQL** | 16 | ACID transactions, referential integrity, and distributed scheduler leases |
| | Local DB | **SQLite** | 3 (WAL) | Zero-friction local development and automated CI testing |
| **DevOps** | Containerization | **Docker & Compose** | Latest | Loopback-isolated dev stack & hardened production container manifests |
| | Deployments | **Vercel & Render** | Cloud | Global CDN edge delivery for UI; containerized API micro-workers |

---

## 7. Local Setup & Quick Start Guide

### Prerequisites
- **Python:** 3.12 or newer
- **Node.js:** 18.0 or newer (npm 9+)
- **Git**

### Step 1: Clone the Repository
```bash
git clone https://github.com/Saksham2005-coder/sih.git
cd sih
```

### Step 2: Configure Environment Variables
Copy the sample environment configuration:
```bash
cp .env.example .env
```

### Step 3: Backend Setup & Database Seeding
Open a terminal in the project root:
```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed regulatory dataset
python -m alembic upgrade head
python -m app.seed.seed_data

# Start backend server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend is running at `http://127.0.0.1:8000` with Swagger Docs at `http://127.0.0.1:8000/docs`.*

### Step 4: Frontend Setup
Open a second terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend is running at `http://localhost:5173`.*

---

## 8. Docker & Production Deployment

### Option A: Development Docker Stack (Port-Isolated)
To run the full stack including PostgreSQL via Docker Compose:
```bash
docker-compose up --build
```
- PostgreSQL is bound strictly to `127.0.0.1:5432:5432` to prevent public host exposure.
- Frontend: `http://localhost:80`
- Backend API Docs: `http://localhost:8000/docs`
- Health Diagnostic: `http://localhost:8000/api/health`

### Option B: Hardened Production Docker Stack
```bash
# Set strong production secrets
export SECRET_KEY="$(openssl rand -hex 32)"
export DATABASE_URL="postgresql+asyncpg://prod_user:strong_password@db:5432/reguflow360_prod"

# Launch production compose
docker-compose -f docker-compose.prod.yml up --build -d
```
- **Fail-Closed Safeguards:** Backend startup immediately aborts if `SECRET_KEY` is weak, default, or missing, if `DEBUG=true`, if `DEMO_MODE=true`, or if SQLite is detected.
- **One-Shot Migrations:** DDL migrations run sequentially via a dedicated migration container before web workers launch.
- **Port Isolation:** PostgreSQL database port is completely unexposed to host networks.

---

## 9. Automated Quality Verification & Test Evidence

ReguFlow 360 enforces an uncompromising automated testing standard across all layers:

```
========================================================================================
QUALITY VERIFICATION RESULTS: 100% PASSING (300 TOTAL TESTS ACROSS REPOSITORY)
========================================================================================
```

### 1. Backend Pytest Suite (258 Passing Tests across 19 Modules)
```bash
cd backend
python -m pytest
```
```
collected 258 items

tests/test_auth_and_isolation.py .................................... [ 14%]
tests/test_authentication_hardening.py .............................. [ 26%]
tests/test_authorization_matrix.py .................................. [ 38%]
tests/test_compliance_passport.py ................................... [ 50%]
tests/test_deadline_engine.py ....................................... [ 62%]
tests/test_document_intelligence.py ................................. [ 74%]
tests/test_evc_authorization_hardening.py ........................... [ 82%]
tests/test_evc_expert_integrity.py .................................. [ 88%]
tests/test_phase6_e2e_journeys.py ................................... [ 94%]
tests/test_statutory_orders.py ...................................... [ 98%]
tests/test_workflow_transitions.py .................................. [100%]

======================= 258 passed in 136.73s (0:02:16) =======================
```

### 2. Frontend Unit & Theme Suite (42 Passing Tests across 6 Suites)
```bash
cd frontend
npm test
```
```
▶ ReguFlow 360 — Document Intelligence & Evidence Verification UI (6 tests) [PASS]
▶ ReguFlow 360 — EVC Expert Integrity, COI Engine & Mobile Field UI (6 tests) [PASS]
▶ ReguFlow 360 — Judge Demonstration Centre & Live Workflow Explorer (6 tests) [PASS]
▶ ReguFlow 360 — Reliable Notification Delivery & Event Outbox UI (5 tests) [PASS]
▶ ReguFlow 360 — Statutory Decision Orders & QR Integrity Verification UI (7 tests) [PASS]
▶ ReguFlow 360 — Theme System & Token Architecture (12 tests) [PASS]

ℹ tests 42 | suites 6 | pass 42 | fail 0 | cancelled 0 | skipped 0
```

### 3. Strict TypeScript & Production Build Verification
```bash
cd frontend
npm run build
```
```
✓ 1575 modules transformed.
dist/index.html                   1.57 kB │ gzip:   0.83 kB
dist/assets/index-BJ2mjvqS.css   69.83 kB │ gzip:  12.17 kB
dist/assets/index-1SlbZaJh.js   712.07 kB │ gzip: 156.26 kB
✓ built in 34.64s
```

---

## 10. Source of Truth Documentation Directory

All architectural blueprints, regulatory matrices, and acceptance evidence are maintained in version-controlled markdown under `/docs`:

1. [`docs/product-spec.md`](./docs/product-spec.md): Product vision, regulatory context, personas, and modules.
2. [`docs/architecture.md`](./docs/architecture.md): Modular monolith design, transactional outbox, SSE pub/sub, idempotent scans.
3. [`docs/judge-acceptance-matrix.md`](./docs/judge-acceptance-matrix.md): Comprehensive 50-item requirement verification matrix with test commands.
4. [`docs/sih-26262-requirement-traceability.md`](./docs/sih-26262-requirement-traceability.md): Regulatory compliance audit and requirement mapping.
5. [`docs/workflow-matrix.md`](./docs/workflow-matrix.md): Guarded state machine transitions and permissions.
6. [`docs/role-permission-matrix.md`](./docs/role-permission-matrix.md): Granular 8-role RBAC authorization matrix.
7. [`docs/data-model.md`](./docs/data-model.md): Entity relationship definitions, indexes, and constraints.
8. [`docs/ui-design-system.md`](./docs/ui-design-system.md): Civic Precision design tokens, typography, and badges.
9. [`docs/api-contracts.md`](./docs/api-contracts.md): REST endpoints, request/response envelopes.
10. [`docs/acceptance-tests.md`](./docs/acceptance-tests.md): Verification checklists and test criteria.
11. [`docs/demo-script.md`](./docs/demo-script.md): Step-by-step regulatory presentation script.
12. [`docs/limitations-and-assumptions.md`](./docs/limitations-and-assumptions.md): Regulatory boundaries and assumptions.
13. [`AGENTS.md`](./AGENTS.md): Engineering guidelines and canonical status dictionary.

---

## 11. Team Information & Institutional Credits

**Smart India Hackathon (SIH 2026)**  
**Problem Statement ID:** 26262  
**Problem Title:** Integrated AICTE Approval Workflow Automation, Compliance Monitoring and Alert Management System  
**Organization:** All India Council for Technical Education (AICTE), Ministry of Education  
**Category:** Software | **Theme:** Smart Automation  

### Team TechTitans 2.0 (Team ID: 197859)
**Institutional Affiliation:** KIET Deemed to be University, Delhi-NCR, Ghaziabad  

| Name | Role | Responsibilities & System Domain |
|---|---|---|
| **Ayush Soni** | **Team Leader** | Regulatory Architecture, State Machine & Coordination |
| **Saksham Gupta** | **Core Developer** | Full-Stack Systems, Distributed Schedulers, Outbox & Security |
| **Ankit Kumar** | **Core Developer** | EVC Management, 4-Way COI Engine & Mobile Field App |
| **Pranjali Sehrawat** | **Developer** | Compliance Passport, Document Intelligence & Validations |
| **Diya Kataria** | **Developer** | Civic Precision UI System, Dual Theme & Workspaces |
| **Diksha Verma** | **Developer** | Analytics Engine, Audit Logging & Acceptance Testing |

---

<div align="center">

**AvedanSetu (आवेदनसेतु) — Advancing Transparency, Speed & Integrity in Technical Education Regulation.**  
*Built with ❤️ by Team TechTitans 2.0 for SIH 2026*

</div>