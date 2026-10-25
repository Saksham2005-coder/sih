# Acceptance Tests & Quality Criteria — ReguFlow 360
## End-to-End Test Plan & Verification Procedures
**SIH 2026 Problem Statement 26262**  
**Version:** 2.0.0 (Phase 2 Hardened)

---

### 1. Phase Gate Acceptance Checklists

#### Phase 1: Repository Foundation & Runnable Shell
- [x] Workspace verified against `https://github.com/Saksham2005-coder/sih` on branch `sih-26262`.
- [x] Initial source-of-truth documents generated and aligned in `/docs`.
- [x] Frontend shell created with strict TypeScript, Vite, Tailwind CSS (Civic Precision tokens).
- [x] FastAPI backend setup with SQLAlchemy 2.0 and Pydantic v2.
- [x] `/api/health` returns healthy database status and current timestamp.
- [x] Reproducible synthetic seed data seeded (2+ institutions, realistic applications, deficiencies, undertakings, documents).
- [x] Both Institution Portal and AICTE Officer Portal navigation render without console errors.

#### Phase 2: Authentication, RBAC & Guarded Workflow Engine Hardening
- [x] Multi-tenant isolation: Institution user querying another institution's application receives `HTTP 403 Forbidden`.
- [x] Regional boundary isolation: Regional Officer attempting to mutate records outside assigned region receives `HTTP 403 Forbidden`.
- [x] Self-approval guard: Institution user cannot advance application beyond permitted submission stages.
- [x] Separation of duties: `SYSTEM_ADMIN` is barred from statutory approvals, scrutinies, and deficiency cures.
- [x] Guarded transition: Advancing from `UNDER_SCRUTINY` to `SCRUTINY_COMPLETED` fails with `HTTP 400` if unresolved deficiencies exist.
- [x] Deficiency cure loop: Officer returns -> Institution cures -> Officer re-evaluates -> Transition succeeds.
- [x] Mandatory remarks: Deficiency returns, rejections, and closures require non-empty remarks.
- [x] Optimistic concurrency control: Concurrent or stale-version transitions fail with `HTTP 409 Conflict`.
- [x] Session revocation: `POST /api/auth/logout` invalidates JWT `jti` in `revoked_tokens` table.
- [x] Gated demo mode: `/api/auth/demo-users` fails closed (`HTTP 403`) when `DEMO_MODE=false` or `ENVIRONMENT=production`.
- [x] Audit trail automatically appends an event for each stage transition with actor attribution atomically.
- [x] Comprehensive test suite: 47 automated tests passing in backend pytest suite (`47 passed, 0 failed`).
- [x] Frontend production build and TypeScript check (`tsc && vite build`) passing with 0 errors.

#### Phase 3: Compliance Passport, Document Lifecycle & EVC
- [ ] Compliance evidence submission generates a version record and computes SHA-256 checksum.
- [ ] Officer verification updates undertaking status to `VERIFIED` and logs verification notes.
- [ ] Document renewal upload increments version number without overwriting previous versions.
- [ ] EVC queue lists applications awaiting inspection; scheduling assigns date and panel members.
- [ ] EVC report upload records recommendation (`RECOMMENDED_APPROVAL`).

#### Phase 4: Deterministic Deadline Engine & Escalations
- [ ] Timestamps evaluated and displayed in `Asia/Kolkata`.
- [ ] Running deadline scanner twice produces zero duplicate alerts (idempotency key enforcement).
- [ ] Overdue deficiency triggers Tier-1 notification, then escalates to Bureau Officer (Tier-2) after SLA breach.
- [ ] Resolving an underlying deficiency automatically clears or marks resolved related pending alerts.

#### Phase 5: Command Centre, Rule Studio & Differentiators
- [ ] Command Centre aggregate metrics reconcile 100% with underlying record counts.
- [ ] Explainable Priority Score outputs numeric index and itemized contributing factors.
- [ ] Rule Studio allows updating SLA thresholds and workflow routes with version increments.
- [ ] Audit trail filterable by entity, actor, and date.
- [ ] Deterministic Case Brief correctly summarizes application history without requiring paid LLM API.

#### Phase 6: Hardening, E2E Scenarios & Demo Readiness
- [ ] `tsc` type check passes with 0 errors.
- [ ] Frontend production build (`npm run build`) completes cleanly.
- [ ] Backend pytest suite passes with full test coverage of critical state machine and isolation guards.
- [ ] Playwright E2E scenarios verify end-to-end user journeys across both portals.

---

### 2. Phase 2 Test Coverage Summary (47 Tests)

1. `tests/test_authentication_hardening.py` (13 tests):
   - Valid login, invalid password (401), unknown account (401), deactivated user (403), missing credentials (422).
   - Expired JWT token, tampered token signature, logout revocation & blacklist check.
   - Active role switching among verified assigned roles, unauthorized role escalation denial.
   - Demo personas enabled in development, denied in production, and denied when demo mode is disabled.
2. `tests/test_authorization_matrix.py` (18 tests):
   - Institution Administrator access to own records vs. cross-institution denial.
   - Compliance Officer boundaries (cannot create application, can submit evidence, cannot verify compliance).
   - Regional Officer in-scope operations vs. cross-region mutation denial.
   - Committee Member evaluation vs. statutory approval denial and rule modification denial.
   - EVC Coordinator inspection scheduling vs. statutory approval denial.
   - Competent Authority approval execution.
   - System Administrator rule management vs. statutory approval denial.
3. `tests/test_workflow_transitions.py` (8 tests):
   - Full end-to-end positive application lifecycle (`DRAFT` -> `SUBMITTED` -> `UNDER_SCRUTINY` -> `SCRUTINY_COMPLETED` -> `AWAITING_EVC_SCHEDULE` -> `EVC_SCHEDULED` -> `EVC_COMPLETED` -> `AWAITING_SAC_CAC_REVIEW` -> `AWAITING_COMPETENT_AUTHORITY` -> `APPROVED`).
   - Invalid stage jump rejection (e.g. `DRAFT` directly to `APPROVED`).
   - Missing mandatory remarks on rejection and deficiency return.
   - Open deficiency blocks `SCRUTINY_COMPLETED`.
   - Uncured deficiency blocks `RESUBMITTED`.
   - Optimistic concurrency conflict returns `409 Conflict`.
   - Atomic state transition and audit log creation verification.
4. `tests/test_auth_and_isolation.py` (4 regression tests)
5. `tests/test_health.py` (2 regression tests)
6. `tests/test_workflow_and_deadlines.py` (2 regression tests)
