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
- **Compliance Undertaking Statuses**: `NOT_YET_DUE`, `DUE_SOON`, `PENDING_VERIFICATION`, `VERIFIED`, `DEFICIENT`, `OVERDUE`
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

