# Architecture Specification — ReguFlow 360
## Integrated Modular Monolith Architecture
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. High-Level Architectural Pattern
ReguFlow 360 is engineered as a **cohesive Modular Monolith**. Microservices introduce distributed transaction complexity, network latency, and deployment overhead that undermine regulatory transactional consistency. A clean, modular monolith with explicit boundaries guarantees ACID compliance, instant auditability, and unified role enforcement.

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|  React 18+ (Strict TypeScript) | Tailwind CSS (Civic Precision) | TanStack Query  |
|  +-------------------------------------+  +------------------------------------+  |
|  |       INSTITUTION PORTAL            |  |        AICTE OFFICER PORTAL        |  |
|  | Dashboard, Passport, Action Centre  |  | Command Centre, Registry, EVC,     |  |
|  | Renewals, Submissions, Alert Feed   |  | Rule Studio, Escalations, Audit    |  |
|  +-------------------------------------+  +------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           | HTTPS / JSON REST API
+------------------------------------------v----------------------------------------+
|                                BACKEND SERVICE                                    |
|                       Python 3.12+ / FastAPI Modular Core                         |
|                                                                                   |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|  | Auth & RBAC Guard |  | Workflow Engine    |  | Deadline & Escalation Engine  | |
|  | JWT / Session     |  | State Machine      |  | Timezone-Aware Asia/Kolkata   | |
|  | Tenant Isolation  |  | Guarded Transition |  | Idempotent Scans & Triggers   | |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|                                                                                   |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|  | Compliance Engine |  | Document Vault     |  | Audit & Reporting             | |
|  | Passport Manager  |  | SHA-256 Checksums  |  | Immutable Append-Only Logs    | |
|  | EVC Scheduler     |  | Version History    |  | Deterministic Case Briefs     | |
|  +-------------------+  +--------------------+  +-------------------------------+ |
+------------------------------------------+----------------------------------------+
                                           | SQLAlchemy 2.0 ORM / Core
+------------------------------------------v----------------------------------------+
|                                DATA PERSISTENCE                                   |
|   PostgreSQL 16 (Production) / SQLite 3 (Zero-friction Local Dev & Tests)        |
|   Alembic Migrations | Foreign Key Integrity | Check Constraints | Unique Keys    |
+-----------------------------------------------------------------------------------+
```

---

### 2. Backend Architecture (`/backend`)
Built with Python 3.12 and FastAPI for asynchronous high-throughput request handling and automatic OpenAPI 3.1 schema generation.

- **`app/core/`**:
  - `config.py`: Environment configuration via Pydantic BaseSettings.
  - `database.py`: SQLAlchemy 2.0 engine, scoped session factory, database connection health checker. Supports SQLite (with WAL mode & foreign keys enabled) and PostgreSQL with identical ORM models.
  - `security.py`: Password hashing using BCrypt/Argon2, JWT creation, token signature verification.
  - `dependencies.py`: FastAPI route dependencies for user extraction, tenant scoping, and fine-grained RBAC permission checks.
- **`app/models/`**:
  - Explicit SQLAlchemy 2 DeclarativeBase models with strict foreign keys, cascade safety, indexed lookups, and UTC datetime defaults.
- **`app/schemas/`**:
  - Pydantic v2 schemas validating request payloads and formatting API responses with `from_attributes = True`.
- **`app/services/`**:
  - `workflow_engine.py`: Encapsulates valid state transitions, role guard enforcement, and automated timeline generation.
  - `deadline_service.py`: Computes pending SLA days, checks due dates against UTC/Asia-Kolkata timestamps, triggers tiered escalations.
  - `priority_service.py`: Computes the Explainable Priority Score (0-100) based on dynamic case factors.
  - `document_service.py`: Computes SHA-256 checksums, validates MIME types, stores document versions, prevents overwrites.
  - `audit_service.py`: Appends non-mutating audit entries for all state mutations.
- **`app/api/`**:
  - Modular routers for `/auth`, `/institutions`, `/applications`, `/compliance`, `/documents`, `/evc`, `/alerts`, `/rules`, `/audit`, `/reports`, `/health`.

---

### 3. Frontend Architecture (`/frontend`)
Crafted with React, TypeScript in strict mode, Vite, and Tailwind CSS configured with the **Civic Precision** design tokens.

- **Routing & State**:
  - `react-router-dom`: Nested layout routes distinguishing Public/Auth, Institution Portal (`/institution/*`), and AICTE Officer Portal (`/officer/*`).
  - `TanStack Query (React Query)`: Server state caching, background invalidation on mutation, automatic retry, optimistic updates.
  - `AuthContext`: Centralizes current session, user profile, active role switcher (in multi-role authorization), and institution scope.
- **Design System & Components**:
  - Standardized component library (`src/components/ui/`):
    - `Button`, `Badge`, `Card`, `Modal`, `Table`, `Tabs`, `Input`, `Select`, `Breadcrumbs`, `Timeline`, `StatCard`, `EmptyState`.
  - Responsive layouts: Collapsible side navigation, contextual top bar, accessible breadcrumbs, clear status indicators.
- **Design Tokens (Civic Precision)**:
  - Midnight Ink (`#152536`)
  - Cool Porcelain (`#F4F6F8`)
  - White surface (`#FFFFFF`)
  - Meridian Teal primary (`#0E746B`)
  - Amber warning (`#C5892B`)
  - Signal Red danger (`#B9474F`)
  - Border (`#DFE5E9`)
  - Muted text (`#526473`)

---

### 4. Background Processing & Deadline Engine
The deadline engine is designed to run synchronously on-demand (via an authorized API endpoint `/api/alerts/run-scan`) or asynchronously in a standalone cron/worker daemon.
- **Idempotency Guarantee**: Every alert event generated calculates a deterministic idempotency key:
  `idempotency_key = sha256(f"{obligation_type}:{obligation_id}:{stage}:{threshold_days}:{escalation_level}:{target_user_id or target_role}")`
- If an alert with this key already exists in the database, the alert generation is skipped.
- When an underlying obligation is satisfied (e.g., deficiency cured or document verified), all pending unresolved alerts linked to that obligation are automatically closed.

---

### 5. Multi-Tenant Security & RBAC Isolation Model
1. **Tenant Scoping**: All requests initiated by an institution user are forced through an authorization guard that verifies `user.institution_id == target_record.institution_id`. Any attempt to read or mutate another institution's data returns HTTP 403 Forbidden.
2. **Role Boundaries**:
   - Only `REGIONAL_OFFICER` and above can change status from `SUBMITTED` to `UNDER_SCRUTINY` or `DEFICIENCY_COMMUNICATED`.
   - Only `EVC_COORDINATOR` and `REGIONAL_OFFICER` can schedule an EVC visit.
   - Only `COMPETENT_AUTHORITY` can execute `APPROVED` or `REJECTED` transitions.
   - Self-approvals and unauthorized role elevation are systematically blocked at the API dependency layer.
