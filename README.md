# ReguFlow 360 — Integrated AICTE Approval Workflow, Compliance Monitoring & Alert System
## SIH 2026 Problem Statement 26262
**Platform Repository:** `https://github.com/Saksham2005-coder/sih`  
**Active Branch:** `main`  
**Version:** 1.0.0 (Remediation 1 Hardened & SIH Demo Ready)  
**Quality Status:** 130 Passing Tests (100%), 0 Linter Warnings, Production Build Verified

---

### 1. Executive Summary & Problem Statement
ReguFlow 360 is a unified, enterprise-grade regulatory operations platform engineered for **AICTE Problem Statement 26262**. It automates institutional application lifecycles, continuous compliance monitoring via the **Institutional Compliance Passport**, multi-year document validity tracking, EVC inspection panel coordination, and deterministic alert escalations.

Built upon a cohesive **Modular Monolith** architecture with a single shared backend, strict multi-tenant database isolation, and the **Civic Precision** regulatory design system.

---

### 2. Dedicated Operational Workspaces Across All 8 Roles

ReguFlow 360 delivers genuinely distinct operational workspaces for all eight canonical roles over a coherent shared dataset:

#### A. Institution Workspaces
- **Institution Administrator Workspace** (`/institution/dashboard`): Institutional application pipeline, deficiency returns with itemized instructions, renewal countdowns, and authorized filings.
- **Compliance Officer Workspace** (`/institution/compliance-workspace`): Dedicated institutional statutory compliance desk, mandatory covenants, SHA-256 evidence submissions, and lease/NOC validity desk.

#### B. AICTE Officer Workspaces
- **Regional Officer Command Workspace** (`/officer/regional-workspace`): Scoped to assigned region (`Western`), regional priority triage queue, deficiency issuance, resubmission review, and undertaking verification.
- **Bureau Officer Oversight Workspace** (`/officer/bureau-workspace`): Apex national regulatory oversight, cross-regional workload and pendency comparisons, and Tier-2 escalation queue.
- **Committee Member Review Workspace** (`/officer/committee-workspace`): Standing hearing committee (SAC/CAC) docket cases, review evidence, inspection findings, and hearing observations.
- **EVC Coordinator Workspace** (`/officer/evc-workspace`): Inspection scheduling desk, Convener & Expert panel formation, future date picker, and visit rosters.
- **Competent Authority Decision Workspace** (`/officer/authority-workspace`): Decision desk for cases awaiting statutory order (`AWAITING_COMPETENT_AUTHORITY`) with verified prerequisite audits, and official gazette Approval/Rejection orders.
- **System Administrator Workspace** (`/officer/admin-workspace`): Telemetry command center, sub-millisecond database ping latency, distributed scheduler leases, on-demand deadline scan trigger, and formula-safe CSV audit export.
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

- **Backend Pytest Suite (123 Tests):**
  ```bash
  cd backend
  python -m pytest
  ```
- **Database Migrations Execution & Schema Validation:**
  ```bash
  cd backend
  python -m alembic upgrade head
  ```
- **Frontend ESLint:**
  ```bash
  cd frontend
  npm run lint
  ```
- **Frontend Strict TypeScript Check & Production Build:**
  ```bash
  cd frontend
  npm run build
  ```
- **Operational Health & Readiness Verification:**
  ```bash
  curl http://localhost:8000/api/health
  curl http://localhost:8000/api/health/readiness
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