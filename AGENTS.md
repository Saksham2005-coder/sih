# ReguFlow 360 — Engineering & Agent Operational Guidelines
## SIH 2026 — AICTE Problem Statement 26262
**Working Product Name:** ReguFlow 360  
**Repository:** https://github.com/Saksham2005-coder/sih  
**Branch:** `main`

---

### 1. Mission and Core Purpose
ReguFlow 360 is an integrated, enterprise-grade AICTE approval workflow automation, compliance monitoring, deadline enforcement, EVC scheduling, document validity, and alert escalation platform.

This platform bridges two synchronized experiences over a single unified backend and database:
1. **Institution Portal**: Application submission, deficiency cure & resubmission, Compliance Passport (undertakings & renewals), lease tracking, and action-oriented alerts.
2. **AICTE Officer Portal**: Regional Officer (RO), Bureau Officer (BO), Committee Member (SAC/CAC), EVC Coordinator, Competent Authority (CA), and System Administrator operational command center and rule studio.

---

### 2. Immutable Engineering Rules
1. **Single Source of Truth**: All statuses, workflow transitions, role permissions, and deadline calculations are governed by backend state machines and database constraints. No client-side bypass.
2. **Deterministic & Illustrative AICTE Logic**: We do not invent official AICTE rules or deadlines as statutory law. Workflow routes, APH norms, and SLA thresholds are modeled as configurable rule templates with illustrative seed defaults.
3. **No Unversioned Overwrites**: Documents and workflow rules must be versioned. Submitting a new document version computes SHA-256 checksums and preserves previous document records.
4. **Idempotent Background Scans**: Deadline scans, reminder triggers, and escalation generators must use database-level uniqueness/idempotency keys (`obligation_id + trigger_type + threshold_days + escalation_level`) to guarantee zero duplicate alerts.
5. **Strict Multi-Tenant & RBAC Isolation**:
   - Institution users can only query and mutate records scoped to their own `institution_id`.
   - AICTE officers can only act on records within their assigned region/bureau or role authority.
   - Role escalation, approval overrides, and self-verification are strictly prohibited.
6. **No Fake Stubs / Broken Links**: Every link, button, filter, tab, and navigation item must resolve to working functional interfaces with real API synchronization.
7. **Typed Contracts**: Strict TypeScript in frontend (`noImplicitAny`, strict null checks). Strict Pydantic v2 schemas in backend. Synchronized models.
8. **Civic Precision Design Language**:
   - Midnight Ink: `#152536`
   - Cool Porcelain: `#F4F6F8`
   - White surface: `#FFFFFF`
   - Meridian Teal: `#0E746B`
   - Amber warning: `#C5892B`
   - Signal Red danger: `#B9474F`
   - Border: `#DFE5E9`
   - Muted text: `#526473`
   No neon gradients, no random card clutter, no empty placeholder charts.
9. **Zero-Secret Commits**: All secrets must be loaded from environment variables (`.env`). Seed credentials in demo mode must be explicitly documented for local testing only.
10. **Phase Gate Protocol**: Each phase must pass all lints, builds, unit/integration checks, and data verification before git commit.

---

### 3. Repository Directory Structure
```
/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
├── AGENTS.md
├── docs/
│   ├── product-spec.md
│   ├── architecture.md
│   ├── workflow-matrix.md
│   ├── role-permission-matrix.md
│   ├── data-model.md
│   ├── ui-design-system.md
│   ├── api-contracts.md
│   ├── acceptance-tests.md
│   ├── demo-script.md
│   └── limitations-and-assumptions.md
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── seed/
│   ├── tests/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── context/
    │   ├── pages/
    │   │   ├── institution/
    │   │   ├── officer/
    │   │   └── auth/
    │   ├── types/
    │   ├── App.tsx
    │   ├── index.css
    │   └── main.tsx
    ├── package.json
    ├── tailwind.config.js
    ├── tsconfig.json
    └── vite.config.ts
```

---

### 4. Canonical Status Reference
- **Application Statuses**: `DRAFT`, `SUBMITTED`, `UNDER_SCRUTINY`, `DEFICIENCY_COMMUNICATED`, `RESUBMITTED`, `SCRUTINY_COMPLETED`, `AWAITING_EVC_SCHEDULE`, `EVC_SCHEDULED`, `EVC_COMPLETED`, `AWAITING_SAC_CAC_REVIEW`, `AWAITING_COMPETENT_AUTHORITY`, `APPROVED`, `REJECTED`, `CLOSED`
- **Compliance Undertaking Statuses**: `NOT_YET_DUE`, `DUE_SOON`, `PENDING_VERIFICATION`, `UNDER_VERIFICATION`, `CORRECTION_REQUIRED`, `VERIFIED`, `DEFICIENT`, `OVERDUE`
- **Document Expiry Statuses**: `ACTIVE`, `EXPIRING_SOON`, `RENEWAL_SUBMITTED`, `VERIFIED`, `EXPIRED`
- **EVC Statuses**: `PENDING_ASSIGNMENT`, `SCHEDULED`, `IN_PROGRESS`, `REPORT_SUBMITTED`, `DEFICIENCY_NOTED`, `RECOMMENDED_APPROVAL`, `RECOMMENDED_REJECTION`
- **Alert Escalation Levels**: `REMINDER_L1`, `REMINDER_L2`, `ESCALATION_L1_RO`, `ESCALATION_L2_BO`, `ESCALATION_L3_MEMBER_SEC`

---

### 5. Git & Branching Policy (Single Main Branch Architecture)
1. **Single Working Branch**: `main` is the sole working branch for this entire project.
2. **Direct Implementation on Main**: All future phases (Phase 3 through Phase 6) are implemented directly on `main`.
3. **No Unrequested Feature Branches**: Do not create or switch to feature branches (e.g. `sih-26262` or others) for subsequent phases unless explicitly requested by the user.
4. **Phase Commits**: Each completed phase receives one meaningful, verified commit on `main`.
5. **Direct Remote Push**: Push completed phase commits directly to `origin/main`.
6. **No Premature Commits**: Never commit unfinished work as a completed phase.
7. **No History Rewrites**: Never force-push or rewrite existing commit history.
8. **Working Tree Safety**: Always inspect the working tree (`git status`) before starting and before committing a phase.
9. **Functionality Preservation**: Preserve the existing commit history and all current application functionality across all phases.
10. **Phase Gate Adherence**: Do not start subsequent phases until the preceding phase is fully consolidated, tested, and verified.

---

### 6. Phase 5 Operational & Intelligence Directives
1. **Command Centre Role Scoping**: Every operational metric, priority action item, and activity log must be strictly scoped to the authenticated caller's jurisdiction (Regional Officers to their region, Institution users to their tenancy, System Admins to platform telemetry).
2. **Deterministic Priority Invariant**: Operational priority scores (0-100) are triage aids for officer queues. They must never mutate application statutory status or infer statutory non-compliance.
3. **Versioned Policy Lifecycle**: Rule Studio policies follow an explicit lifecycle (`DRAFT`, `VALIDATED`, `PUBLISHED`, `RETIRED`). Publishing must archive prior configurations into `rule_version_history`.
4. **Formula Injection Sanitization**: All audit CSV exports must prepend single quotes (`'`) to cells starting with `=`, `+`, `-`, `@`, `\t`, `\r`.
5. **Distributed Scheduler Coordination**: Multi-worker background deadline scans coordinate through database leases (`scheduler_leases`), ensuring mutual exclusion and preventing overlapping execution.
6. **Statutory AI Boundary**: Case brief summaries are strictly informational syntheses grounded in database facts and citations. AI must never approve, reject, verify compliance, or overrule human officers.

---

### 7. Phase 6 Hardening, End-to-End Scenarios & SIH Demo Release Directives
1. **End-to-End Regulatory Integrity**: All 6 acceptance journeys (Journeys A through F) are backed by automated tests, verifying application deficiency cures, EVC scheduling & panel reporting, compliance undertakings & document renewals, automated deadline scans & deduplicated escalations, Rule Studio simulations & audit logs, and explainable case briefs.
2. **Unindexed Storage Boundary**: Storage downloads reject unindexed files on disk for non-administrators with HTTP 404, eliminating arbitrary storage path probing.
3. **Deep Operational Telemetry**: The `/api/health` endpoint reports sub-millisecond database ping latencies, scheduler thread state, distributed lease telemetry, and scan staleness alongside dedicated `/health/liveness` and `/health/readiness` orchestrator probes.
4. **Production Demo Fail-Closed**: In production environments (`ENVIRONMENT=production` or `DEMO_MODE=false`), demo persona routes fail closed with HTTP 403 Forbidden.
5. **Single Main Release Commit**: Release commit message must strictly match: `Harden end-to-end flows and prepare SIH demo release`.

---

### 8. Critical Remediation 1: Role-Based Workspaces & Scoped Operational UX
1. **Genuine Workspace Differentiation**: The platform provides dedicated operational workspaces for each of the 8 canonical roles (`INSTITUTION_ADMIN`, `COMPLIANCE_OFFICER`, `REGIONAL_OFFICER`, `BUREAU_OFFICER`, `COMMITTEE_MEMBER`, `EVC_COORDINATOR`, `COMPETENT_AUTHORITY`, `SYSTEM_ADMIN`). Generic collapsing of dashboards is strictly prohibited.
2. **Zero Cross-Tenant & Cross-Region Data Leaks**: Multi-tenant institutional boundaries and regional jurisdictions are strictly verified on both list and detail endpoints (`get_application_detail` enforces `verify_regional_access` and `verify_institution_access`).
3. **Query Cache Isolation**: Client-side query caches (`queryClient.clear()`) are flushed on login, logout, and role switching, ensuring zero stale data leakage across persona sessions.
4. **Shared Coherent Regulatory Dataset**: Single database records (`app1` to `app6`) are shared across all workspaces at their respective lifecycle stages, preserving complete relationship integrity, audit trails, and prerequisite chains.
5. **Remediation Release Commit**: Release commit message must strictly match: `Differentiate role workspaces and enforce scoped data`.

---

### 9. Critical Remediation 2: Production-Quality Light and Dark Mode
1. **Civic Precision Theme Parity**: ReguFlow 360 provides a complete, accessible dual-theme system (Light: `#F4F6F8` Cool Porcelain canvas, `#FFFFFF` surfaces, `#152536` ink; Dark: `#101820` obsidian canvas, `#1B2835` primary surface, `#233342` elevated surface, `#F1F5F8` primary text, `#354653` slate borders, `#14B8A6` high-contrast teal).
2. **Design-Token Architecture**: Theme styles are governed by centralized CSS variables mapped into Tailwind configuration (`var(--brand-*)`), preventing scattered hardcoded colors and ensuring robust dark mode support across all 8 role workspaces.
3. **Anti-Flash Pre-Hydration**: An inline head script resolves stored preferences (`localStorage.getItem('reguflow_theme')`) or system preference (`prefers-color-scheme: dark`) before hydration, preventing any wrong-theme flicker.
4. **Accessible Theme Controllers**: The application provides accessible, keyboard-operable theme switchers in both authenticated and unauthenticated layouts, supporting Light, Dark, and live OS System synchronization.
5. **Remediation Release Commit**: Release commit message must strictly match: `Add accessible application-wide light and dark themes`.

---

### 10. Critical Remediation 3: Production-Safety Hardening, End-to-End Acceptance, and Release Integrity
1. **Fail-Closed Production Invariants**: In production (`ENVIRONMENT=production`), application startup immediately aborts if `SECRET_KEY` is missing/empty/weak (<32 chars) or contains development defaults, if `DEBUG=True`, if `DEMO_MODE=True`, or if `DATABASE_URL` is SQLite or uses development passwords. Error messages never print or leak secret keys.
2. **Zero Synthetic Seeding in Production**: Automatic database seeding is strictly prohibited in production mode. Calling `seed_database()` in production mode raises an immediate `RuntimeError`.
3. **Network & Database Port Isolation**: Development Docker Compose binds PostgreSQL strictly to loopback `127.0.0.1:5432:5432`. A dedicated `docker-compose.prod.yml` runs with internal database networking and zero published host database ports.
4. **Statutory Decision Exclusivity Invariant**: All approval routes (including "Only Scrutiny") require an explicit, authorized Competent Authority decision order. Bypassing EVC does not grant automated approval.
5. **Remediation Release Commit**: Release commit message must strictly match: `Harden deployment security and verify final acceptance`.
