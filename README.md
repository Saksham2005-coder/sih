# आवेदनसेतु | AvedanSetu — AICTE Workflow Automation, Compliance Monitoring & Alert System
## SIH 2026 Problem Statement 26262
**Platform Repository:** `https://github.com/Saksham2005-coder/sih`  
**Active Branch:** `main`  
**Working Title:** AvedanSetu (आवेदनसेतु)  
**Quality Status:** 258 Passing Backend Tests (100%), 42 Passing Frontend Tests (100%), 0 Linter Warnings, Zero Data-Loss Deployment Guaranteed

---

### 1. Executive Summary & Problem Statement
**AvedanSetu (आवेदनसेतु)** is an integrated, enterprise-grade regulatory operations platform engineered specifically for **AICTE Problem Statement 26262**. It automates institutional application lifecycles, continuous compliance monitoring via the **Institutional Compliance Passport**, multi-year document validity tracking, EVC inspection panel coordination, and deterministic alert escalations.

Built upon a cohesive **Modular Monolith** architecture with a single shared backend, strict multi-tenant database isolation, fail-closed production deployment hardening, automatic zero-data-loss database hydration on deployment, and the **Civic Precision** regulatory design system.

---

### 2. Dedicated Operational Workspaces Across All 8 Roles

ReguFlow 360 delivers genuinely distinct operational workspaces for all eight canonical roles over a coherent shared dataset:

#### A. Institution Workspaces
- **Institution Administrator Workspace** (`/institution/dashboard`): Institutional application pipeline, deficiency returns with itemized instructions, renewal countdowns, and authorized filings.
- **Compliance Officer Workspace** (`/institution/compliance-workspace`): Dedicated institutional statutory compliance desk, mandatory covenants, SHA-256 evidence submissions, and lease/NOC validity desk.

#### B. AICTE Officer Workspaces
- **Regional Officer Command Workspace** (`/officer/regional-workspace`): Scoped to assigned region (`Western`), regional priority triage queue, deficiency issuance, resubmission review, and undertaking verification.
- **Bureau Officer Oversight Workspace** (`/officer/bureau-workspace`): Apex national regulatory oversight, cross-regional workload and pendency comparisons, and Tier-2 escalation queue.
- **Committee Member Review Workspace** (`/officer/committee-workspace`): Standing hearing committee (SAC/CAC) docket cases, review evidence, inspection findings, hearing deficiency notices, and hearing observations.
- **EVC Coordinator Workspace** (`/officer/evc-workspace`): Inspection scheduling desk, Convener & Expert panel formation, future date picker, and visit rosters.
- **Competent Authority Decision Workspace** (`/officer/authority-workspace`): Decision desk for cases awaiting statutory order (`AWAITING_COMPETENT_AUTHORITY`) with verified prerequisite audits, and official gazette Approval/Rejection orders.
- **System Administrator Workspace** (`/officer/admin-workspace`): Telemetry command center, sub-millisecond database ping latency, distributed scheduler leases, on-demand deadline scan trigger, and formula-safe CSV audit export.
- **Reports & Analytics**: 100% database-reconciled stage-wise pendency and regional workload distribution.
- **Immutable Audit Trail**: Append-only non-repudiable audit log tracking every transition and action.
- **Rule Studio**: Visual configuration of SLA thresholds and workflow templates with version increments.
- **Administration**: Diagnostics, platform health, and RBAC tenant boundaries.

---

### 3. Demo Personas & Development Credentials (Local Dev / Prototype Only)

> [!IMPORTANT]
> The credentials below are synthetic demo identities seeded strictly for local development and SIH evaluators (`ENVIRONMENT=development` and `DEMO_MODE=true`). In production mode (`ENVIRONMENT=production`), one-click demo chips and synthetic database seeding are strictly prohibited and fail closed.

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

---

### 4. Quick Start & Execution

#### Option 1: Local Development (Zero-friction SIH Demo)

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

#### Option 2: Docker Compose (Development Stack)
```bash
docker-compose up --build
```
- In development Compose, the PostgreSQL database is safely bound to loopback `127.0.0.1:5432:5432` only, preventing public LAN/WAN host exposure.
- Frontend: `http://localhost:80`
- Backend API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/health`

#### Option 3: Production Docker Deployment (Hardened)
```bash
# Generate a cryptographically secure 64-character signing key:
# openssl rand -hex 32
export SECRET_KEY="your-strong-production-secret-key-at-least-32-chars"
export DATABASE_URL="postgresql+asyncpg://prod_user:strong_password@db:5432/reguflow360_prod"
docker-compose -f docker-compose.prod.yml up --build -d
```
- **Fail-Closed Guarantees**: Backend startup immediately aborts if `SECRET_KEY` is missing/weak/default, if `DEBUG=true`, if `DEMO_MODE=true`, or if `DATABASE_URL` is SQLite or uses default dev passwords.
- **Port Isolation**: Database port is NOT published to host networks; communication occurs over internal container bridge only.
- **Zero Demo Seeding**: Automatic synthetic database seeding is permanently prohibited in production mode.

---

### 5. Running Quality Checks & Tests

- **Backend Pytest Suite (193 Tests across 19 modules — 100% Passing, 0 Warnings):**
  ```bash
  cd backend
  python -m pytest
  ```
- **Frontend Unit & Theme Test Suite (30 Tests across 4 suites — 100% Passing):**
  ```bash
  cd frontend
  node --test src/__tests__/*.test.mjs
  ```
- **Frontend ESLint (0 Errors, 0 Warnings):**
  ```bash
  cd frontend
  npm run lint
  ```
- **Frontend Strict TypeScript Check & Production Build:**
  ```bash
  cd frontend
  npm run build
  ```
- **Database Migrations Execution & Schema Validation:**
  ```bash
  cd backend
  python -m alembic upgrade head
  ```
- **Operational Health & Readiness Verification:**
  ```bash
  curl http://localhost:8000/api/health
  curl http://localhost:8000/api/health/readiness
  ```

---

### 5. Deployment & Zero-Data-Loss Database Persistence

AvedanSetu guarantees that **no regulatory records, applications, documents, or audit trails are lost during deployment**:

#### A. Automated First-Boot Hydration (Recommended)
When deploying AvedanSetu to any cloud host (Render, Railway, Supabase, Neon, AWS, or Docker):
1. Configure your target database URL in `.env` or cloud environment variables:
   ```bash
   DATABASE_URL=postgresql+psycopg2://user:password@db-host:5432/avedansetu
   ```
2. When the backend service boots up for the first time, its startup lifecycle detects if the target database is empty.
3. It **automatically hydrates the complete regulatory dataset** from `snapshot_data.json` into PostgreSQL/SQLite, restores all 25 tables, and automatically resets PostgreSQL primary key sequences.
4. All existing applications (`AICTE-2026-NEW-00001` through `AICTE-2026-EXT-00042`), demo accounts, EVC panels, document records, and rules are immediately available in the live deployed website!

#### B. Direct SQLite-to-PostgreSQL Migration CLI
If you prefer to manually migrate from your local SQLite database directly to PostgreSQL before launching:
```bash
cd backend
python migrate_to_postgres.py --target "postgresql+psycopg2://user:password@host:5432/dbname"
```
This utility:
- Dumps the exact local database state
- Creates the schema and tables in the target PostgreSQL instance
- Hydrates all rows in topological foreign-key order
- Resets all PostgreSQL sequence counters (`setval`)
- Prints verification record counts across all regulatory tables

---

### 6. Workflow Routes & Regulatory Invariants

ReguFlow 360 models all APH approval routes deterministically:
1. **Only Scrutiny (e.g. Annual EoA Extension)**: Applications bypass EVC inspection because physical inspection is not prescribed. Upon completion of scrutiny (`SCRUTINY_COMPLETED`), the application advances directly to `AWAITING_COMPETENT_AUTHORITY`.
   > [!IMPORTANT]
   > The "Only Scrutiny" route does **NOT** automatically approve an application. Final statutory approval or rejection strictly requires an explicit decision order issued by the authorized Competent Authority (`member.sec@aicte.gov.in`).
2. **Scrutiny + EVC (e.g. New Institution / New Program)**: Applications require mandatory physical inspection. EVC completion is an unbypassable prerequisite before reaching Committee Review or Competent Authority.
3. **EVC + SAC/SHC (e.g. Increase in Intake / NRI Quota with Hearing)**: Includes standing hearing committee evaluation where committee members can issue hearing deficiencies, review institutional cures, and record hearing observations.
4. **Only EVC (e.g. Closure of Institution / Verification Visit)**: Applications enter the EVC queue directly from initial submission. Non-EVC applications attempting direct entry are strictly rejected.

---

### 7. Production-Quality Light and Dark Theme Architecture
ReguFlow 360 features a full design-token driven light and dark theme system based on the **Civic Precision** regulatory aesthetic:
- **Light Theme**: Bright, crisp regulatory workspace (`#F4F6F8` Cool Porcelain canvas, `#FFFFFF` card surface, `#152536` ink, `#DFE5E9` slate borders, `#0E746B` Meridian Teal accent).
- **Dark Theme**: Restrained operational command workspace (`#101820` obsidian background, `#1B2835` card surface, `#233342` elevated surface, `#F1F5F8` primary text, `#354653` borders, `#14B8A6` high-contrast teal).
- **System Synchronization**: Dynamic OS preference tracking with zero-flash pre-hydration bootstrap script.
- **Accessible Controls**: Segmented and dropdown theme toggles available globally across both the authenticated header and unauthenticated login portals.

---

### 8. Reliable Notification Delivery, Transactional Outbox & Real-Time SSE
ReguFlow 360 implements a robust, observable regulatory notification lifecycle:
- **Transactional Outbox Pattern**: State mutations (stage transitions, deficiency memos, cures, SLA alerts, compliance evidence, orders) atomically write `NotificationOutbox` rows within the active business transaction. Business mutations never wait on external provider network roundtrips.
- **Honest Delivery Evidence**: Distinguishes MTA relay acceptance (`ACCEPTED_BY_PROVIDER`) from confirmed recipient delivery. Unconfigured services report `NOT_CONFIGURED`, while sandbox dispatches report `SIMULATED`—never fabricating live telecom delivery.
- **Bounded Backoff & Dead-Letter Handling**: Asynchronous background dispatcher applies bounded exponential backoff (`next_retry_at = now + 2^attempt * base`) with a max 4-attempt limit before transitioning to `DEAD_LETTER` for officer triage and manual retry.
- **Real-Time Server-Sent Events (SSE)**: Authenticated `/api/notifications/stream` connection streams authorized event summaries with periodic 15-second heartbeats. Event broadcasts are strictly scoped by user, tenant (`institution_id`), and regional jurisdiction. The client UI seamlessly falls back to 25-second interval polling if SSE is disconnected.
- **Officer Outbox Command Desk**: Scoped administrative desk (`/officer/notifications/outbox`) exposes live SMTP, SMS, and SSE channel health cards, delivery metrics, filterable outbox records, plain text/HTML payload inspectors, and manual retry controls.

---

### 9. Source of Truth Documentation (`/docs`)
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