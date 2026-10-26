# Architecture Specification — ReguFlow 360
## Integrated Modular Monolith Architecture
**SIH 2026 Problem Statement 26262**  
**Version:** 4.0.0 (Remediation 3 Production-Safety Hardened & Release Integrity Verified)

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
|  | JWT (jti blacklst)|  | Versioned State M/c|  | Timezone-Aware Asia/Kolkata   | |
|  | Tenant/Reg Scoping|  | Optimistic Locking |  | Idempotent Scans & Triggers   | |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|                                                                                   |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|  | Compliance Engine |  | Document Vault     |  | Audit & Reporting             | |
|  | Passport Manager  |  | SHA-256 Checksums  |  | Immutable Append-Only Logs    | |
|  | EVC Scheduler     |  | Traversal-Guarded  |  | Atomic Commit Guarantees      | |
|  +-------------------+  +--------------------+  +-------------------------------+ |
+------------------------------------------+----------------------------------------+
                                           | SQLAlchemy 2.0 ORM / Core
+------------------------------------------v----------------------------------------+
|                                DATA PERSISTENCE                                   |
|   PostgreSQL 16 (Production) / SQLite 3 (Zero-friction Local Dev & Tests)        |
|   Alembic Migrations | Foreign Key Integrity | Version Columns | Unique Keys      |
+-----------------------------------------------------------------------------------+
```

---

### 2. Backend Architecture (`/backend`)
Built with Python 3.12 and FastAPI for asynchronous high-throughput request handling and automatic OpenAPI 3.1 schema generation.

- **`app/core/`**:
  - `config.py`: Environment configuration via Pydantic BaseSettings. Contains `DEMO_MODE` flag and production security guards (`is_demo_allowed`).
  - `database.py`: SQLAlchemy 2.0 engine, scoped session factory, database connection health checker. Supports SQLite (with WAL mode & foreign keys enabled) and PostgreSQL with identical ORM models.
  - `security.py`: Password hashing using BCrypt/Argon2, JWT creation with enriched claims (`sub`, `roles`, `active_role`, `institution_id`, `region`, `jti`), token signature verification, and secure password validation.
  - `rbac.py`: Canonical 8-role model, domain permission constants, and resource-scoping functions (`check_institution_scope`, `check_regional_scope`, `check_case_assignment`).
  - `dependencies.py`: FastAPI route dependencies for user extraction, token blacklist checks, active role verification, tenant scoping, and fine-grained RBAC permission checks (`require_permission`, `verify_institution_access`, `verify_regional_access`).
- **`app/models/`**:
  - Explicit SQLAlchemy 2 DeclarativeBase models with strict foreign keys, cascade safety, indexed lookups, and UTC datetime defaults.
  - `Application`: Contains `version = Column(Integer, default=1, nullable=False)` for monotonic optimistic concurrency control.
  - `RevokedToken`: Contains `jti`, `token_type`, `revoked_at`, and `expires_at` for instantaneous token invalidation upon logout.
- **`app/schemas/`**:
  - Pydantic v2 schemas validating request payloads and formatting API responses with `model_config = ConfigDict(from_attributes=True)`.
- **`app/services/`**:
  - `workflow_engine.py`: Encapsulates valid state transitions, optimistic locking (`expected_version`), mandatory remarks validation, deficiency resolution verification, EVC prerequisites, role guard enforcement, atomic audit logging, and automated notification dispatch.
  - `compliance_service.py`: Governs compliance undertaking lifecycle, secure evidence uploads with rollback safety, verifications, and correction-required loops.
  - `document_service.py`: Computes SHA-256 checksums, validates MIME & magic bytes, stores versioned files in private storage, prevents overwrites.
  - `evc_service.py`: Governs EVC route eligibility, panel formation (convener & expert), future date validation, inspection report submissions, and workflow coordination.
  - `deadline_service.py`: Computes pending SLA days, checks due dates against UTC/Asia-Kolkata timestamps, triggers tiered escalations.
  - `priority_service.py`: Computes the Explainable Priority Score (0-100) based on dynamic case factors.
  - `audit_service.py`: Appends non-mutating audit entries for all state mutations.
- **`app/api/`**:
  - Modular routers for `/auth`, `/institutions`, `/applications`, `/compliance`, `/documents`, `/evc`, `/alerts`, `/rules`, `/audit`, `/reports`, `/health`.
  - All endpoints enforce granular RBAC permissions and resource tenant/regional scoping.

---

### 3. Frontend Architecture (`/frontend`)
Crafted with React, TypeScript in strict mode, Vite, and Tailwind CSS configured with the **Civic Precision** design tokens.

- **Routing & State**:
  - `react-router-dom`: Nested layout routes distinguishing Public/Auth, Institution Portal (`/institution/*`), and AICTE Officer Portal (`/officer/*`).
  - `TanStack Query (React Query)`: Server state caching, background invalidation on mutation, automatic retry, optimistic updates.
  - `AuthContext`: Centralizes current session, user profile, active role switcher (in multi-role authorization), authenticated logout, and institution scope.
- **Optimistic Concurrency & Conflict Handling**:
  - Transition actions pass the application's current `expected_version`.
  - In the event of a concurrent update (`HTTP 409 Conflict`), the UI alerts the user and refreshes the application dossier to display the latest authoritative state.
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

### 4. Background Processing & Deadline Engine Architecture
Phase 4 implements a deterministic, multi-vector deadline monitoring, automated notification, and escalation engine that operates continuously without requiring an open browser or manual trigger.

- **Unified Multi-Vector Deadline Service (`DeadlineService`)**:
  - Encapsulates deadline discovery and SLA evaluation across 5 regulatory vectors:
    1. *Application Stage SLAs*: Scrutiny pendency (e.g. 7-day SLA), deficiency cure window (15 days), EVC scheduling window (10 days).
    2. *Compliance Undertakings*: Explicit calendar due dates with upcoming reminder windows (T-15, T-7, T-0) and overdue escalation triggers.
    3. *Document Records & Expiry*: Lease deeds (33-year), Fire NOCs, Building Plans with warning thresholds (T-45, T-30, T-7, T-0) and renewal tracking.
    4. *EVC Scheduling SLAs*: Inspection queue age monitoring for EVC Coordinators.
    5. *EVC Report Submission SLAs*: Post-visit report upload compliance for inspection panels.
  - Dynamic Rule Studio Integration: Reads SLA thresholds, reminder offsets, and escalation recipient chains directly from active `RuleDefinition` records (`RULE_EOA_SLA`, `RULE_COMPLIANCE_UNDERTAKING`, `RULE_DOCUMENT_VALIDITY`, `RULE_EVC_SLA`) with safe fallback defaults.

- **Cycle-Aware Deduplication & Idempotency**:
  - Formulates a deterministic SHA-256 idempotency key:
    `idempotency_key = sha256(f"{entity_type}:{entity_id}:{trigger_type}:{threshold_days}:{escalation_level}:{recipient_role}:{cycle_id}")`
  - Injected `cycle_id` (e.g. `v1`, `v2`) ensures that if a deficiency is returned for a second round of scrutiny, legitimate new alerts are emitted without being suppressed by previous cycle records.
  - Backed by a database unique constraint on `alert_escalations.idempotency_key` ensuring zero duplicate records across concurrent worker executions.

- **Multi-Tier Escalation Model**:
  - Overdue conditions trigger progressive, role-authorized escalation steps:
    - `REMINDER_L1`: Institution Admin / Compliance Officer reminder.
    - `REMINDER_L2`: Urgent notice to Institution and Regional Officer.
    - `ESCALATION_L1_RO`: Breached SLA routed to Regional Officer for action.
    - `ESCALATION_L2_BO`: Breached SLA (> 3-5 days overdue) escalated to Bureau Officer.
    - `ESCALATION_L3_MEMBER_SEC`: Severe breach (> 7-10 days overdue) escalated to Member Secretary / Competent Authority.
  - Prevents automated statutory decisions: Escalation generates actionable operational alerts and records, never an automated approval or rejection.

- **Auto-Resolution of Obsolete Alerts**:
  - When an underlying obligation is resolved (e.g. deficiency cured, compliance verified, or document renewal verified), all related unresolved alerts are atomically updated to `status = "RESOLVED"` with a recorded timestamp and justification reason.

- **Autonomous Background Scheduler (`DeadlineScheduler`)**:
  - Managed singleton running an asynchronous non-blocking loop via `asyncio.create_task` initialized during FastAPI `lifespan`.
  - Configurable polling interval (`DEADLINE_SCAN_INTERVAL_SECONDS`, default 300s).
  - Telemetry and Audit: Each run generates an immutable record in `deadline_engine_runs` capturing items scanned, alerts generated, duplicates prevented, execution time, and error status.
  - On-Demand Scan Trigger: Authorized officers (`rules.manage` or `application.transition`) can trigger manual scans via `POST /api/alerts/run-scan`, sharing identical service logic and idempotency guarantees.

---

### 5. Operational Command Centre, Explainable Intelligence & Rule Studio
Phase 5 elevates ReguFlow 360 into an operationally intelligent platform with full explainability, administrative control, and non-repudiation:

- **AICTE Operational Command Centre**:
  - Unified operational workspace answering priority, bottleneck, and queue ageing questions.
  - Role-scoped queries guarantee that Regional Officers only view records in their regional jurisdiction, Institution Admins only view their own tenancy, and System Admins access national telemetry.
  - Reconciled metrics: Every overview metric (stage breakdown, overdue counts, bottleneck averages) maps 1:1 to underlying database records.

- **Explainable Deadline Intelligence (`PriorityService`)**:
  - Deterministic priority scoring engine (0-100) combining stage ageing, unresolved deficiencies, statutory approval milestones, overdue compliance undertakings, expiring documents, active escalations, and repeated deficiency cycles.
  - Configurable weighting policy sourced directly from Rule Studio (`RULE_PRIORITY_POLICY`).
  - Structured factor attribution: Every priority score provides human-readable point breakdowns and recommended next regulatory actions.
  - Invariant: Operational priority scores strictly prioritize human officer attention and never mutate an application's statutory decision state.

- **Robust Versioned Rule Studio**:
  - Full rule lifecycle management (`DRAFT`, `VALIDATED`, `PUBLISHED`, `RETIRED`).
  - Strict validation engine checking required fields, JSON syntax, positive integer SLAs, canonical recipient roles, and threshold ordering.
  - Dry-run simulation sandbox (`POST /api/rules/{rule_code}/simulate`) evaluates hypothetical scenarios without mutating database state or triggering notifications.
  - Immutable version history ledger (`rule_version_history`) archives previous configuration snapshots upon publication with change reasons and actor metadata.

- **Unified Audit Explorer**:
  - Server-side filterable investigation tool with multi-field search (`entity_type`, `action`, `actor_role`, `search`, date ranges) and pagination.
  - Regional and tenant scoping enforces that ROs only access events in their region, institutions only access their own events, and system admins access the global ledger.
  - Formula injection defense: CSV export sanitizes cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` by prefixing a single quote (`'`), while generating an export audit event.

- **Distributed Scheduler Coordination (`SchedulerLease`)**:
  - Dedicated distributed database lease table coordinates multi-worker or multi-process deployments.
  - Workers acquire a named lease (`deadline_engine_scan`) with a configurable TTL, renew via heartbeat, and skip overlapping scans when a lease is held by another active worker.
  - Date-only deadlines (e.g. `DocumentRecord.expiry_date`) calculate boundaries against Asia/Kolkata local calendar dates to prevent premature UTC-midnight expiration errors.

- **Evidence-Grounded Case Brief Assistant (`CaseBriefService`)**:
  - Synthesizes complex application dossiers into executive summaries, deficiency timelines, compliance passport status, and EVC inspection findings.
  - Grounded with explicit database citations referencing stage transitions, deficiency IDs, and inspection records.
  - Deterministic fallback operates without requiring third-party LLM API keys.
  - Statutory boundary: Strictly informative case synthesis; cannot approve, reject, or overrule human regulatory decisions.

---

### 6. Role Workspaces, Multi-Tenant Data Scoping & Cache Isolation Architecture

Critical Remediation 1 eliminates the generic single-dashboard defect by introducing dedicated operational workspaces and strict data boundary enforcement:

1. **Role-Specific Workspace Composition**:
   - `InstitutionDashboard`: Scoped strictly to Institution Administrator filings, deficiency returns, and renewal notices for their institution.
   - `ComplianceOfficerWorkspace`: Focused exclusively on institutional compliance obligations, covenants desk, and evidence submission.
   - `RegionalOfficerWorkspace`: Operational command for regional scrutiny queues, deficiency issuance, and undertaking verification (scoped to assigned region, e.g. Western).
   - `BureauOfficerWorkspace`: Apex national oversight, cross-regional workload comparisons, and Tier-2 escalation acknowledgments.
   - `CommitteeMemberWorkspace`: Standing hearing committee docket cases, review evidence, and hearing observation recording.
   - `EVCCoordinatorWorkspace`: Expert visit scheduling, panel roster management (Convener + Expert members), and inspection logistics.
   - `CompetentAuthorityWorkspace`: Statutory decision desk for cases awaiting final order with verified prerequisite audits.
   - `SystemAdminWorkspace`: Platform telemetry, live database ping latency, Rule Studio lifecycle, distributed leases, and audit trail export.

2. **Backend Scoping Enforcement (`rbac.py` & `dependencies.py`)**:
   - `verify_institution_access`: Rejects cross-tenant attempts with HTTP 403.
   - `verify_regional_access`: Enforced on list, detail, deficiency, and transition endpoints (`get_application_detail` verifies region for Regional Officers).
   - `check_case_assignment`: Restricts hearing panel observation access.

3. **Query Cache Isolation (`queryClient.clear()`)**:
   - Centralized `queryClient` singleton in `src/queryClient.ts`.
   - `AuthContext.tsx` triggers `queryClient.clear()` on login, logout, and role switching, guaranteeing zero residual cached records across persona transitions.

---

### 7. Deployment Security Architecture, Container Hardening & Settings Validation

ReguFlow 360 separates local development ergonomics from production deployment security:

1. **Dual Docker Compose Architecture**:
   - `docker-compose.yml` (Development):
     - PostgreSQL port is bound strictly to `127.0.0.1:5432:5432` on the loopback adapter, ensuring the database is accessible for local development tools while preventing host LAN/WAN exposure.
     - Includes automated healthchecks and ordered service dependency (`depends_on: backend: condition: service_healthy`) to eliminate startup race conditions.
   - `docker-compose.prod.yml` (Hardened Production):
     - Database port `5432` is omitted from port mapping; database container communicates solely through the internal Docker network.
     - Includes a dedicated one-shot `migration` service running `alembic upgrade head` before backend web workers start, preventing concurrent DDL execution across workers (`condition: service_completed_successfully`).
     - Requires external provisioning of `SECRET_KEY` and `DATABASE_URL` via environment variables.
     - Disables debug and demo capabilities (`ENVIRONMENT=production`, `DEBUG=false`, `DEMO_MODE=false`).

2. **Fail-Closed Configuration Validation (`config.py`)**:
   - Built on Pydantic v2 `model_validator(mode="after")`.
   - In production mode (`is_production == True`):
     - `SECRET_KEY` must be explicitly provided, must be >= 32 characters, and cannot match known development keys or substrings (`supersecret_dev_key`, `dev_key`, `change_in_production`, `secret`, `changeme`).
     - `DEBUG=True` is rejected.
     - `DEMO_MODE=True` is rejected.
     - SQLite `DATABASE_URL` is rejected.
     - Default development passwords in `DATABASE_URL` (`:reguflow_secret@`, `:reguflow_secure_pass@`, `:postgres@`) are rejected.
     - Validation exceptions never print, format, or leak the actual secret values.

3. **Database Seeding Lifecycle**:
   - `seed_database()` executes conditionally in development mode only when `is_demo_allowed and not is_production`.
   - In production mode, `seed_database()` actively raises a `RuntimeError`, guaranteeing that shared demo accounts and synthetic fixtures cannot be inadvertently inserted into a production database.

---

### 8. Document Intelligence, Evidence Extraction and Compliance Cross-Checking Architecture

ReguFlow 360 integrates an explainable, local, and auditable Document Intelligence subsystem designed for statutory compliance corroboration without relying on paid third-party APIs or sending confidential institutional documents to external cloud services:

1. **Local Open-Source Extraction Engine**:
   - Built on `pypdf` for native digital PDF text and font extraction.
   - Graceful fallback for scanned documents: detects absence of text layer, queries host for local Tesseract executable (`shutil.which('tesseract')`), and records `ocr_provider: "UNAVAILABLE"` with zero crashes when OCR binary is missing.
   - Conservative regex heuristics extract field candidates:
     - Document Category (`LAND_LEASE_DEED`, `FIRE_SAFETY_NOC`, `BUILDING_STABILITY`, `OCCUPANCY_CERTIFICATE`, `POLLUTION_NOC`, `EVC_INSPECTION_REPORT`, `COMPLIANCE_EVIDENCE`).
     - Reference / Registration Numbers.
     - Issuing Authorities.
     - Issue Dates and Expiry / Validity Dates (including derived multi-year terms, e.g., "period of 33 years from 01/04/2021").
     - Property / Land survey and plot numbers.
   - Extracts exact source page indices and verbatim character excerpts for every candidate fact.

2. **Persistent Traceable Lifecycle**:
   - State Machine: `QUEUED` &rarr; `PROCESSING` &rarr; `REVIEW_REQUIRED` &rarr; `CONFIRMED` / `FAILED`.
   - **Idempotency Guarantee**: Keyed to `f"DOC_VERSION:{version.id}:{version.checksum_sha256}:1.0.0"`. Repeat scans of identical files return the existing record without duplicate DB rows.
   - Engine telemetry, page count, text layer status, overall confidence score, and timestamps are recorded in the `document_analyses` table.

3. **Deterministic Regulatory Cross-Checks**:
   - **EXPIRY_DATE_MISMATCH**: Compares institution-entered expiry against extracted certificate validity date.
   - **CERTIFICATE_ALREADY_EXPIRED**: Flags documents whose extracted validity date is in the past.
   - **DOCUMENT_NUMBER_MISMATCH**: Detects discrepancies between vault record numbers and deed text.
   - **CATEGORY_MISMATCH**: Flags when an uploaded file's content signatures contradict its record type.
   - **RENEWAL_VALIDITY_EXTENDED**: Confirms that a renewal version extends validity beyond prior versions.
   - **RENEWAL_VALIDITY_NOT_EXTENDED**: Flags renewals that fail to extend tenure.
   - **COMPLIANCE_EVIDENCE_CORROBORATED**: Verifies that submitted evidence contains required regulatory domain terms.
   - **OCR_EXTRACTION_UNAVAILABLE**: Accurately flags scanned documents requiring manual human review when local OCR engine is unavailable.
   - Classification labels: `MATCH`, `POSSIBLE_MISMATCH`, `MISSING_EVIDENCE`, `EXTRACTION_UNAVAILABLE`, `HUMAN_REVIEW_REQUIRED`.

4. **Non-Automation Statutory Invariant**:
   - Extraction and cross-checks NEVER autonomously alter database validity dates, approve compliance, or reject applications.
   - Authoritative dates in `DocumentRecord` are mutated ONLY when an authorized AICTE officer (`REGIONAL_OFFICER`, `BUREAU_OFFICER`, `SYSTEM_ADMIN`) reviews the analysis, inputs mandatory remarks, and explicitly selects `apply_to_record=True`.
   - All review actions log immutable `DOCUMENT_ANALYSIS_REVIEWED` audit events.

---

### 9. Formal Statutory Decision Orders & QR Integrity Verification Architecture

1. **Deterministic Order Generation**:
   - Orders (`StatutoryOrder`) are generated exclusively after the Competent Authority records a statutory `APPROVED` or `REJECTED` decision.
   - Generates official order identifiers formatted as `AICTE/RO-{REGION}/{YEAR}/{APPLICATION_NUMBER}` with versioning (`version = 1, 2, ...`).
   - Generates verifiable PDF artifacts with header seals, terms, conditions, and cryptographic verification metadata.
   - Computes canonical SHA-256 checksum of generated bytes and generates 64-character verification tokens.
   - Dynamic QR codes point to public verification endpoints (`/verify-order/{token}`).

2. **Prototype Signature State & IT Act 2000 Disclosure**:
   - Explicitly records `signature_status="UNSIGNED_PROTOTYPE"` and `signing_provider="NONE_PROTOTYPE_MODE"`.
   - Clear disclosure that generated PDFs are unverifiable prototype approval artifacts until configured with an authorized DSC / Aadhaar e-Sign gateway (C-DAC / NIC / eMudhra).

3. **Public & Physical Artifact Verification**:
   - Token lookup (`GET /api/orders/verify/{token}`) verifies status (`VERIFIED_AUTHENTIC`, `REVOKED`, `SUPERSEDED`, `NOT_FOUND`).
   - File upload verification (`POST /api/orders/verify-upload`) computes SHA-256 hash of user-provided PDF and compares with stored checksum (`AUTHENTIC_MATCH` vs `TAMPERED_OR_UNREGISTERED`).

---

### 10. Reliable Notification Delivery, Transactional Outbox & Real-Time SSE Architecture

1. **Transactional Outbox Pattern**:
   - Eliminates distributed dual-write inconsistencies between database mutations and notification dispatch.
   - Business mutations (stage changes, deficiency alerts, SLA breaches, statutory orders) atomically write a `NotificationOutbox` record within the active SQLAlchemy transaction.
   - If a business transaction fails or rolls back, zero phantom emails or SMS messages are ever queued or transmitted.

2. **Outbox State Machine & Delivery Lifecycle**:
   - Statuses: `QUEUED` &rarr; `PROCESSING` &rarr; `ACCEPTED_BY_PROVIDER` | `SIMULATED` | `NOT_CONFIGURED` | `RETRY_SCHEDULED` &rarr; `DEAD_LETTER`.
   - **MTA Relay Distinction**: For SMTP, successful transmission returns `ACCEPTED_BY_PROVIDER` (not falsely claiming `DELIVERED`), recognizing that SMTP server acceptance (250 OK) does not guarantee delivery to a recipient's inbox.
   - **Gateway Boundary**: For SMS, returns `SIMULATED` in sandbox or `NOT_CONFIGURED` in production until authorized CDAC / NIC gateway credentials are provided.
   - **Exponential Backoff**: Transient errors (timeouts, network resets) trigger bounded exponential backoff (`base_sec * (2 ** (attempt - 1))`, max 4 attempts) before transitioning to `DEAD_LETTER`.
   - **Administrative Recovery**: Authorized officers can inspect failed outbox items and trigger manual retries via `POST /api/notifications/outbox/{id}/retry`.

3. **Real-Time Server-Sent Events (SSE) Pub/Sub Broker**:
   - Connection endpoint: `GET /api/notifications/stream?token={jwt}` with token validation.
   - Bounded queues: 50 items per subscriber with automatic pruning on disconnect.
   - Heartbeat: 15-second `: ping` comments preserve proxy and firewall keep-alive.
   - Scoped broadcasting: Events are sanitized (summary metadata only; zero document binary leaks) and filtered by user ID, institution ID, role, and regional jurisdiction.
   - Robust polling fallback: Header components query `/api/notifications/unread-count` every 25 seconds if SSE connections disconnect or are blocked by intermediate enterprise proxies.




