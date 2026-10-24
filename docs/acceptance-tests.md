# Acceptance Tests & Quality Criteria — ReguFlow 360
## End-to-End Test Plan & Verification Procedures
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

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

#### Phase 2: Authentication, RBAC & Workflow State Machine
- [ ] Multi-tenant isolation: Institution user querying another institution's application receives `HTTP 403`.
- [ ] Self-approval guard: Institution user cannot advance application beyond permitted submission stages.
- [ ] Guarded transition: Advancing from `UNDER_SCRUTINY` to `SCRUTINY_COMPLETED` fails if unresolved deficiencies exist.
- [ ] Deficiency cure loop: Officer returns -> Institution cures -> Officer re-evaluates -> Transition succeeds.
- [ ] Audit trail automatically appends an event for each stage transition with actor attribution.

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
