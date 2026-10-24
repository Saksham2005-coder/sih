# ReguFlow 360 — Integrated AICTE Approval Workflow, Compliance Monitoring & Alert System
## SIH 2026 Problem Statement 26262
**Platform Repository:** `https://github.com/Saksham2005-coder/sih`  
**Active Feature Branch:** `sih-26262`  
**Version:** 1.0.0 (Phase 1 Baseline & Production Architecture)

---

### 1. Executive Summary & Problem Statement
ReguFlow 360 is a unified, enterprise-grade regulatory operations platform engineered for **AICTE Problem Statement 26262**. It automates institutional application lifecycles, continuous compliance monitoring via the **Institutional Compliance Passport**, multi-year document validity tracking, EVC inspection panel coordination, and deterministic alert escalations.

Built upon a cohesive **Modular Monolith** architecture with a single shared backend, strict multi-tenant database isolation, and the **Civic Precision** regulatory design system.

---

### 2. Dual Portal Experiences

#### A. Institution Portal
- **Institution Dashboard**: Operational status banner, pendency counts, imminent compliance milestones.
- **My Applications**: Comprehensive regulatory docket (EoA Annual, New Institution, Intake Variation), priority indicators, and new filing modal.
- **Application Dossier & Timeline**: Complete chronological milestone progression, itemized deficiency memos, cure submission forms, and resubmission triggers.
- **Action Centre**: High-priority aggregated view of pending deficiency cures, expiring documents, and overdue undertakings.
- **Compliance Passport**: Continuous tracking of time-bound undertakings with cryptographic (SHA-256) evidence submission and verification history.
- **Documents & Renewals**: Multi-year validity management (33-year land lease deed, municipal fire NOC, structural stability) with versioned renewals.
- **Notifications**: Real-time regulatory alerts and deficiency communication feed.
- **Submission History**: Complete traceable record of institutional filings.

#### B. AICTE Officer Portal
- **Officer Dashboard (Command Centre)**: Reconciled operational metrics, regional docket distribution, stage ageing, and explainable priority ranking.
- **Application Registry**: Searchable national registry with multi-stage filters and scrutiny console links.
- **Officer Scrutiny Console**: Itemized deficiency memo issuance, cure verification, and guarded stage transitions.
- **EVC Inspection Queue**: Expert committee roster panel assignment (Convener + Expert), visit scheduling, and inspection report submissions.
- **Compliance Monitoring**: Verification queue for institutional compliance evidence.
- **Escalations & SLA Console**: Timezone-aware (Asia/Kolkata) idempotent alert scanner triggering progressive escalations (RO → BO → Apex).
- **Reports & Analytics**: 100% database-reconciled stage-wise pendency and regional workload distribution.
- **Immutable Audit Trail**: Append-only non-repudiable audit log tracking every transition and action.
- **Rule Studio**: Visual configuration of SLA thresholds and workflow templates with version increments.
- **Administration**: Diagnostics, platform health, and RBAC tenant boundaries.

---

### 3. Demo Personas & Development Credentials

| Persona Role | Email | Password | Scope Boundary |
|---|---|---|---|
| **Institution Administrator** | `admin@apex.edu.in` | `Password123!` | Apex Institute (Western Region) |
| **Institution Compliance Officer** | `compliance@apex.edu.in` | `Password123!` | Apex Institute (Western Region) |
| **Institution Administrator** | `admin@nier.edu.in` | `Password123!` | Northern Institute (Delhi) |
| **Regional Officer (RO)** | `ro.western@aicte.gov.in` | `Password123!` | Western Regional Office |
| **EVC Coordinator** | `evc.coord@aicte.gov.in` | `Password123!` | Western / National EVC Roster |
| **Bureau Officer (BO)** | `bo.approval@aicte.gov.in` | `Password123!` | Approval Bureau, New Delhi |
| **Committee Member (SAC/CAC)** | `committee.member@aicte.gov.in` | `Password123!` | Standing Scrutiny Committee |
| **Competent Authority (CA)** | `member.sec@aicte.gov.in` | `Password123!` | Member Secretary / Apex Council |
| **System Administrator** | `sysadmin@aicte.gov.in` | `Password123!` | Platform-wide Administration |

*Note: In the login screen, click any persona chip for 1-click test entry.*

---

### 4. Quick Start & Local Execution

#### Option 1: Local Development (Recommended)

**Prerequisites:** Python 3.12+, Node.js 18+

1. **Backend Setup:**
   ```bash
   cd backend
   # Virtual environment setup
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # Install dependencies
   pip install -r requirements.txt
   # Run migrations & seed data
   python -m app.seed.seed_data
   # Start backend server (port 8000)
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Frontend Setup (in a separate terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

#### Option 2: Docker Compose (Full Stack)
```bash
docker-compose up --build
```
- Frontend: `http://localhost:80`
- Backend API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

---

### 5. Running Quality Checks & Tests

- **Backend Pytest Suite:**
  ```bash
  cd backend
  $env:PYTHONPATH="backend"
  .\venv\Scripts\pytest -v tests
  ```
- **Database Migrations Check:**
  ```bash
  cd backend
  $env:PYTHONPATH="."
  .\venv\Scripts\alembic upgrade head
  ```
- **Frontend Production Build & Strict Type Check:**
  ```bash
  cd frontend
  npm run build
  ```

---

### 6. Source of Truth Documentation (`/docs`)
1. [`docs/product-spec.md`](./docs/product-spec.md): Product vision, regulatory context, personas, and modules.
2. [`docs/architecture.md`](./docs/architecture.md): Modular monolith design, idempotent background scans, data flows.
3. [`docs/workflow-matrix.md`](./docs/workflow-matrix.md): Guarded state machine transitions and permissions.
4. [`docs/role-permission-matrix.md`](./docs/role-permission-matrix.md): Granular 8-role RBAC authorization matrix.
5. [`docs/data-model.md`](./docs/data-model.md): Entity relationship definitions, indexes, and constraints.
6. [`docs/ui-design-system.md`](./docs/ui-design-system.md): Civic Precision design tokens, typography, and badges.
7. [`docs/api-contracts.md`](./docs/api-contracts.md): REST endpoints, request/response envelopes.
8. [`docs/acceptance-tests.md`](./docs/acceptance-tests.md): Verification checklists and test criteria.
9. [`docs/demo-script.md`](./docs/demo-script.md): Step-by-step regulatory presentation script.
10. [`docs/limitations-and-assumptions.md`](./docs/limitations-and-assumptions.md): Regulatory boundaries and assumptions.
11. [`AGENTS.md`](./AGENTS.md): Engineering guidelines and canonical status dictionary.