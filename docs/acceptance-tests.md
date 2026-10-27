# Acceptance Tests & Quality Criteria — ReguFlow 360
## End-to-End Test Plan & Verification Procedures
**SIH 2026 Problem Statement 26262**  
**Version:** 5.0.0 (Remediation 3 Production-Safety Hardened & Release Integrity Verified)

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
- [x] Compliance evidence submission validates file size (<= 10MB), MIME type, magic bytes, generates an immutable version record, and computes SHA-256 checksum.
- [x] Officer verification updates undertaking status to `VERIFIED` or `DEFICIENT` with mandatory official notes, while self-verification by institutions is strictly blocked.
- [x] Correction-required workflow: officer requests cure with remarks, institution resubmits evidence (generating v2 with SHA-256), and status advances to `PENDING_VERIFICATION`.
- [x] Document renewal upload increments version number without overwriting previous versions, storing validated file metadata in private directory.
- [x] Document verification sign-off updates document status to `ACTIVE` on approval, while rejection preserves original validity without extending expiry.
- [x] Path-traversal attempts and unauthenticated downloads are strictly blocked; resource-scoped downloads verify institution and regional boundaries.
- [x] EVC queue filters non-EVC applications and only lists applications eligible under configured workflow rules.
- [x] EVC scheduling enforces future date validation, complete panel formation (convener + expert), and regional jurisdiction.
- [x] EVC report upload records recommendation (`RECOMMENDED_APPROVAL`, `DEFICIENCY_NOTED`, `RECOMMENDED_REJECTION`) with mandatory notes, advancing application stage to `EVC_COMPLETED` without prematurely approving.
- [x] Workflow state machine enforces mandatory EVC completion prerequisite before allowing advancement to Committee Review or Competent Authority decision.
- [x] Alembic migration (`e5a821bf6290`) upgrades and downgrades cleanly.
- [x] Total automated tests: 78 automated backend tests passing in pytest suite (`78 passed, 0 failed`).
- [x] Frontend TypeScript type check (`tsc --noEmit`) and production build (`tsc && vite build`) passing with 0 errors.

#### Phase 4: Deterministic Deadline Engine & Escalations
- [x] Timestamps evaluated and displayed in `Asia/Kolkata` with UTC database storage.
- [x] Running deadline scanner repeatedly produces zero duplicate alerts (SHA-256 cycle-aware idempotency key enforcement).
- [x] Multi-vector deadline discovery across Application stage SLAs, Compliance undertakings, Document expiries, and EVC visits.
- [x] Overdue deficiency triggers Tier-1 notification, then escalates through configured chain (`REMINDER_L1`, `REMINDER_L2`, `ESCALATION_L1_RO`, `ESCALATION_L2_BO`, `ESCALATION_L3_MEMBER_SEC`).
- [x] Resolving or curing an underlying deficiency/obligation automatically resolves related pending alerts.
- [x] Autonomous background scheduler (`scheduler.py`) runs periodic scans without requiring an open browser or manual intervention.
- [x] Strict tenant isolation on notifications and regional scoping on escalations (`check_regional_scope`).
- [x] Cross-region escalation acknowledgement is denied with `HTTP 403 Forbidden`.
- [x] Single notification mark-as-read validates resource ownership before updating read state.
- [x] Alembic migration (`b978968a8caa`) upgrades and downgrades cleanly.
- [x] Total automated tests: 92 automated backend tests passing in pytest suite (`92 passed, 0 failed`).
- [x] Frontend TypeScript type check (`tsc --noEmit`) and production build (`tsc && vite build`) passing with 0 errors.

#### Phase 5: Command Centre, Rule Studio & Differentiators
- [x] Command Centre aggregate metrics reconcile 100% with underlying record counts.
- [x] Explainable Priority Score outputs numeric index (0-100) and itemized contributing factors without mutating statutory state.
- [x] Rule Studio allows updating SLA thresholds and workflow routes with version increments and immutable version history ledger.
- [x] Audit trail filterable by entity, actor, and date with sanitized CSV export against formula injection.
- [x] Deterministic Case Brief correctly summarizes application history without requiring paid LLM API, grounded in real database citations.
- [x] Phase 5 automated tests: 17 comprehensive tests passing (`17 passed, 0 failed`). Total tests: 109.

#### Phase 6: Hardening, E2E Scenarios & Demo Readiness
- [x] Strict TypeScript check (`tsc --noEmit`) passes with 0 errors.
- [x] Frontend ESLint passes with 0 errors and 0 warnings.
- [x] Frontend production build (`npm run build`) completes cleanly in 3.19s with optimized chunks.
- [x] Backend pytest suite passes 100% with 123 tests (`123 passed, 0 failed, 0 errors`).
- [x] End-to-End User Journeys (A through F) verified across both Institution and AICTE Officer portals.
- [x] Security attack vectors tested: Cross-tenant ID substitution, cross-region mutation, revoked JWT reuse, directory path traversal, and unindexed document downloads.
- [x] Gated demo mode verified: Demo persona switcher disabled when `ENVIRONMENT=production` or `DEMO_MODE=false`.
- [x] Operational health & readiness endpoints (`/api/health`, `/health/liveness`, `/health/readiness`) verified with database latency and scheduler lease telemetry.
- [x] Live browser verification confirmed pristine Civic Precision styling, zero console errors, and high-density regulatory layout.

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

---

### 3. Phase 3 Test Coverage Summary (31 New Tests, Total 78 Tests)

1. `tests/test_compliance_passport.py` (11 tests):
   - `test_institution_views_own_compliance_undertakings`: Tenant-scoped listing.
   - `test_institution_cannot_access_other_institution_undertaking`: Cross-tenant read returns 403.
   - `test_institution_user_submits_valid_evidence`: Multipart file upload, SHA-256 calculation, status advance to `PENDING_VERIFICATION`.
   - `test_compliance_officer_cannot_verify_own_evidence`: Self-verification blocked (403).
   - `test_regional_officer_verifies_in_scope_obligation`: Verification sign-off with mandatory notes advances status to `VERIFIED`.
   - `test_regional_officer_cross_region_verification_blocked`: Jurisdiction enforcement across regions returns 403.
   - `test_officer_requests_correction_on_undertaking`: Transition to `CORRECTION_REQUIRED` with feedback.
   - `test_institution_cures_correction_required_obligation`: Resubmission generates version 2 with updated SHA-256.
   - `test_missing_notes_on_verification_rejected`: Empty notes return 400.
   - `test_invalid_compliance_verification_status_rejected`: Invalid status codes return 400.
   - `test_unauthorized_roles_cannot_verify_compliance`: Role-based verification denial for unauthorized personas.

2. `tests/test_secure_document_lifecycle.py` (11 tests):
   - `test_document_renewal_valid_upload_success`: Uploads renewed document version, computes SHA-256 and media metadata, sets status `RENEWAL_SUBMITTED`.
   - `test_unsupported_file_extension_rejected_with_415`: `.exe` or disallowed extensions rejected with 415.
   - `test_invalid_magic_bytes_rejected_with_400`: Spoofed MIME types failing magic bytes validation rejected with 400.
   - `test_path_traversal_filename_sanitized`: Filename directory traversal attempts (`../../`) sanitized safely.
   - `test_authorized_user_downloads_own_document`: Authenticated document download within tenant scope.
   - `test_cross_institution_download_blocked_with_403`: Cross-institution document download blocked with 403.
   - `test_regional_officer_in_scope_can_download_document`: In-jurisdiction officer download permitted.
   - `test_rejected_renewal_does_not_extend_expiry`: Rejected renewal maintains original expiry date and preserves history.
   - `test_verified_renewal_marks_document_active`: Verified renewal updates document validity and status to `ACTIVE`.
   - `test_missing_verification_notes_rejected`: Mandatory verification sign-off notes enforced.
   - `test_nonexistent_file_download_returns_404`: Missing storage files return 404.

3. `tests/test_evc_management.py` (9 tests):
   - `test_evc_queue_lists_pending_and_eligible_inspections`: Queue filtering based on workflow route eligibility.
   - `test_evc_scheduling_valid_panel_and_future_date`: Future date validation and convener + expert assignment.
   - `test_evc_scheduling_past_date_rejected_with_400`: Historical or past dates rejected with 400.
   - `test_evc_scheduling_missing_panel_members_rejected`: Incomplete panel rejected with 400.
   - `test_regional_officer_cross_region_evc_scheduling_blocked`: Cross-region scheduling blocked with 403.
   - `test_unauthorized_institution_cannot_schedule_evc`: Institution personas blocked from EVC scheduling.
   - `test_evc_report_submission_success`: Panel report upload advances inspection to `REPORT_SUBMITTED` and application to `EVC_COMPLETED` without prematurely approving.
   - `test_invalid_evc_recommendation_rejected`: Non-canonical recommendations rejected with 400.
   - `test_missing_evc_report_notes_rejected`: Missing report notes rejected with 400.

---

### 4. Phase 4 Test Coverage Summary (14 New Tests, Total 92 Tests)

`tests/test_deadline_engine.py` (14 comprehensive tests):
1. `test_deadline_condition_derivation_boundaries`: Verifies deterministic condition derivation (`ON_TRACK`, `DUE_SOON`, `DUE_TODAY`, `OVERDUE`) across UTC/Asia-Kolkata boundaries and threshold days.
2. `test_multi_vector_deadline_scan_executes_successfully`: Verifies execution across all vectors (Application stage SLAs, Compliance undertakings, Document renewals, EVC scheduling, EVC report submissions).
3. `test_zero_duplicate_alerts_on_repeated_scans`: Verifies strict idempotency; running the scanner consecutively yields 0 new alerts and records `duplicates_prevented > 0`.
4. `test_cycle_aware_idempotency_allows_new_cycle_alert`: Verifies that cycle discriminators (`v1` vs. `v2`) permit legitimate alert generation when an obligation enters a new workflow cycle.
5. `test_auto_resolution_of_cured_deficiency_escalations`: Verifies that curing a deficiency or verifying compliance atomically transitions active escalations to `RESOLVED` with justification reasons.
6. `test_multi_tier_escalation_chain_exists`: Verifies progressive escalation generation through configured tiers (`REMINDER_L1`, `REMINDER_L2`, `ESCALATION_L1_RO`, `ESCALATION_L2_BO`, `ESCALATION_L3_MEMBER_SEC`).
7. `test_regional_officer_scoping_on_escalations`: Verifies Regional Officers query escalations strictly within their jurisdiction.
8. `test_cross_region_escalation_acknowledgment_blocked`: Verifies that an officer attempting to acknowledge an out-of-jurisdiction escalation is denied with `HTTP 403 Forbidden`.
9. `test_officer_acknowledges_in_scope_escalation`: Verifies successful escalation acknowledgement with official follow-up remarks and audit event generation.
10. `test_institution_isolation_on_notifications`: Verifies multi-tenant isolation on `/api/alerts/notifications` preventing leakage across institutions.
11. `test_mark_notification_read_ownership_enforcement`: Verifies single notification mark-as-read requires recipient or tenant ownership (denies cross-tenant tampering with 403).
12. `test_engine_status_endpoint_returns_metrics`: Verifies `GET /api/alerts/engine-status` reports scheduler health, interval, and aggregate run counts.
13. `test_unauthorized_user_cannot_trigger_scan`: Verifies RBAC protection on `POST /api/alerts/run-scan` (denies regular institution users with 403).
14. `test_rule_studio_updates_affect_deadline_service`: Verifies dynamic integration with Rule Studio; modifying SLA thresholds in `RuleDefinition` config alters scanner calculations.

---

### Phase 5 Test Suite Specification (`tests/test_phase5_command_centre.py`)
17 comprehensive automated tests:
1. `test_calendar_date_deadline_boundaries`: Verifies date-only deadlines with Asia/Kolkata date boundaries (`ON_TRACK`, `DUE_SOON`, `DUE_TODAY`, `OVERDUE`).
2. `test_scheduler_lease_coordination`: Verifies distributed database lease acquisition, mutual exclusion, heartbeat renewal, and release.
3. `test_command_centre_sysadmin_scope`: Verifies global operational metrics, stage distribution, bottlenecks, and priority queue items for System Administrators.
4. `test_command_centre_regional_officer_scoping`: Verifies Regional Officer jurisdiction scoping (Western region only).
5. `test_command_centre_institution_user_scoping`: Verifies multi-tenant isolation for institution users (Apex Institute only).
6. `test_priority_calculation_deterministic`: Verifies identical inputs produce identical priority scores, tier classifications, and factor breakdowns.
7. `test_priority_calculation_does_not_mutate_statutory_state`: Invariant check: priority scoring never mutates application stage, ID, or version.
8. `test_rule_validation_endpoint`: Verifies valid rule schema approval and actionable rejection for negative or out-of-order thresholds.
9. `test_rule_dry_run_simulation`: Verifies scenario simulation evaluates SLA thresholds without mutating database state or dispatching alerts.
10. `test_rule_publish_archives_version_history`: Verifies rule publication archives prior snapshot in `rule_version_history` with actor and change reason.
11. `test_rule_modification_requires_admin`: Verifies non-admin roles (e.g. Regional Officer) cannot publish or modify regulatory policies (`HTTP 403 Forbidden`).
12. `test_audit_explorer_filtering_and_pagination`: Verifies server-side filtering, pagination envelope (`items`, `total`, `page`, `limit`), and regional scoping.
13. `test_audit_csv_export_formula_injection_defense`: Verifies formula injection prevention in CSV export (mitigates DDE by prefixing `'` to `=`, `+`, `-`, `@`).
14. `test_sla_adherence_report`: Verifies stage-wise SLA turnaround and breach analytics derived from real database records.
15. `test_evc_analytics_report`: Verifies EVC inspection turnaround, mode distribution, and recommendation counts.
16. `test_case_brief_endpoint_with_citations`: Verifies structured case brief synthesis with database milestone citations and statutory disclaimer.
17. `test_case_brief_forbidden_for_other_institution`: Verifies tenant isolation prevents cross-institution dossier access (`HTTP 403 Forbidden`).

---

### 6. Phase 6 Test Coverage Summary (14 New Tests, Total 123 Tests)

`tests/test_phase6_e2e_journeys.py` (14 comprehensive end-to-end and security tests):
1. `test_journey_a_deficiency_cure_resubmit_and_scrutiny`:
   - Full Journey A: Institution reviews itemized deficiency -> cures all deficiencies with remarks and supporting documentation -> attempts illegal self-approval (blocked with 400/403) -> resubmits dossier (`RESUBMITTED`) -> Regional Officer re-evaluates and returns to `UNDER_SCRUTINY` -> audit trail verified.
2. `test_journey_b_evc_scheduling_and_report_lifecycle`:
   - Full Journey B: Application enters EVC queue -> EVC Coordinator schedules panel (Convener + Expert) -> application advances to `EVC_SCHEDULED` -> panel inspects and submits official report (`RECOMMENDED_APPROVAL`) -> application advances to `EVC_COMPLETED` without granting premature statutory approval.
3. `test_journey_c_compliance_and_document_renewals`:
   - Full Journey C: Institution submits compliance evidence -> Regional Officer requests correction with mandatory remarks (`CORRECTION_REQUIRED`) -> Institution cures evidence -> Regional Officer verifies -> Institution submits document renewal with automatic version increment (`v1 -> v2`) and SHA-256 hash preservation -> Regional Officer verifies renewed document to `ACTIVE`.
4. `test_journey_d_deadline_scan_escalation_and_idempotency`:
   - Full Journey D: Multi-vector background scan discovers obligations -> consecutive scan proves 0 duplicate alerts (`duplicates_prevented > 0`) -> Regional Officer acknowledges in-scope escalation with official remarks.
5. `test_journey_e_rule_studio_and_audit_explorer`:
   - Full Journey E: Rule Studio administrator creates draft rule -> validation rejects negative thresholds with actionable explanation -> dry-run simulation runs without mutating database records or dispatching alerts -> publishes new version and archives prior configuration in `rule_version_history` -> unauthorized role is denied -> Audit Explorer verifies event history and downloads CSV with formula injection sanitization.
6. `test_journey_f_case_brief_and_command_centre`:
   - Full Journey F: Application case brief synthesizes chronological milestones grounded in database records with citations and statutory disclaimer -> Command Centre reports reconciled operational metrics and priority action items -> unauthorized institution receives 403.
7. `test_security_id_substitution_cross_tenant_denied`:
   - Security Attack 1: Institution user attempts identifier substitution by querying another institution's application directly by ID -> rejected with `403 Forbidden`.
8. `test_security_regional_officer_cross_jurisdiction_denied`:
   - Security Attack 2: Regional Officer attempts cross-jurisdiction transition on an application in another region -> rejected with `403 Forbidden`.
9. `test_security_token_revocation_on_logout`:
   - Security Attack 3: Logged-out token reuse attempt is rejected with `401 Unauthorized`.
10. `test_security_document_path_traversal_blocked`:
    - Security Attack 4: Document download request with directory traversal characters (`../../`) is rejected with `400/404`.
11. `test_security_unindexed_document_download_blocked`:
    - Security Attack 5: Unindexed or unassociated file on storage disk is blocked for non-admins with `404 Not Found`.
12. `test_security_optimistic_locking_concurrency_conflict`:
    - Concurrency Invariant: Outdated version transition attempt returns `409 Conflict`.
13. `test_security_demo_switcher_production_gating`:
    - Production Hardening: Persona list endpoint `/api/auth/demo-users` fails closed (`403 Forbidden`) when `ENVIRONMENT=production`.
14. `test_health_operational_readiness_endpoint`:
    - Operational Health: `/api/health` reports status, database connectivity, ping latency, scheduler status, and lease telemetry; `/health/liveness` and `/health/readiness` verify microservice orchestrator probes.

---

### 7. Critical Remediation 1 Test Coverage Summary (7 New Tests, Total 130 Tests)

`tests/test_role_workspaces_and_scoping.py` (7 comprehensive role isolation & operational boundary tests):
1. `test_canonical_identity_resolution_all_roles`:
   - Validates that `/api/auth/me` resolves exact canonical roles (`INSTITUTION_ADMIN`, `COMPLIANCE_OFFICER`, `REGIONAL_OFFICER`, `BUREAU_OFFICER`, `COMMITTEE_MEMBER`, `EVC_COORDINATOR`, `COMPETENT_AUTHORITY`, `SYSTEM_ADMIN`), tenant institutions, and regional jurisdictions.
2. `test_institution_admin_vs_compliance_officer_capabilities`:
   - Verifies that both institution roles access own applications; Compliance Officer is denied application creation (`403 Forbidden`) and denied issuing official deficiency notices (`403 Forbidden`).
3. `test_regional_officer_jurisdiction_scoping`:
   - Verifies that Regional Officer Western lists only Western applications and direct GET access to Northern region applications is rejected with `403 Forbidden`.
4. `test_committee_member_scoping_and_forbidden_statutory_actions`:
   - Verifies Committee Member application queue is scoped to cases at `AWAITING_SAC_CAC_REVIEW` or assigned EVC panels; attempting Competent Authority approval is rejected with `403 Forbidden`.
5. `test_evc_coordinator_scoping_and_forbidden_compliance_verification`:
   - Verifies EVC Coordinator application list is scoped to Western region applications requiring EVC; attempting compliance undertaking verification is rejected with `403 Forbidden`.
6. `test_competent_authority_statutory_decision_flow`:
   - Verifies Competent Authority accesses application queue with cases at `AWAITING_COMPETENT_AUTHORITY` (e.g. `AICTE-2026-DEC-33019`), and Command Centre reports role scope `COMPETENT_AUTHORITY` with Apex Council jurisdiction.
7. `test_system_admin_regulatory_boundary`:
   - Verifies System Administrator can access system health, engine status, and audit logs, but is strictly barred from granting statutory approvals (`403 Forbidden`).

---

### 8. Problem Statement Acceptance & APH Route Test Coverage Summary (5 New Tests, Total 135 Tests)

`tests/test_workflow_routes_and_aph_combinations.py` (5 authoritative APH route combination and statutory safeguard tests):
1. `test_route_1_only_scrutiny_lifecycle`:
   - Proves Route 1 (Only Scrutiny): Applications filed under `EOA_ANNUAL` / `ONLY_SCRUTINY` with `evc_required=False` progress through preliminary scrutiny (`UNDER_SCRUTINY` -> `SCRUTINY_COMPLETED`) and advance directly to Competent Authority (`AWAITING_COMPETENT_AUTHORITY` -> `APPROVED`) without requiring an EVC inspection.
2. `test_route_2_scrutiny_plus_evc_prerequisite_enforcement`:
   - Proves Route 2 (Scrutiny + EVC): Applications requiring EVC (`SCRUTINY_EVC` / `NEW_INSTITUTION`) cannot bypass the inspection stage (`HTTP 400 Bad Request: Route requires mandatory EVC inspection, but no completed inspection report exists`). Advances through EVC scheduling, panel inspection report submission, and onward to statutory approval.
3. `test_route_3_evc_plus_sac_shc_hearing_and_deficiency_cure`:
   - Proves Route 3 (EVC + SAC/SHC Hearing): Applications with hearing requirements (`EVC_SAC_SHC` / `INTAKE_VARIATION`) progress through EVC to `AWAITING_SAC_CAC_REVIEW`. Committee Member logs itemized hearing deficiency (`DEFICIENCY_COMMUNICATED`), institution cures and resubmits (`RESUBMITTED`), Committee Member verifies cure, resumes hearing, and recommends approval.
4. `test_route_4_only_evc_direct_queue_entry`:
   - Proves Route 4 (Only EVC): Applications filed under `CLOSURE_PROGRAM` / `ONLY_EVC` are permitted to enter the EVC queue directly from `SUBMITTED` to `AWAITING_EVC_SCHEDULE`. Verifies that non-EVC applications attempting the same direct transition are strictly rejected (`HTTP 400 Bad Request`).
5. `test_statutory_safeguard_approval_reserved_for_competent_authority`:
   - Regulatory Safeguard Invariant: Verifies that automation supports processing but strictly denies approval authority to unauthorized roles (`REGIONAL_OFFICER`, `BUREAU_OFFICER`, `INSTITUTION_ADMIN` receive `HTTP 403 Forbidden`). Verifies that Competent Authority rejections enforce mandatory recorded justifications.

---

### 9. Production-Safety Hardening & Deployment Security Test Coverage Summary (10 New Tests, Total 145 Tests)

`tests/test_production_configuration_hardening.py` (10 automated security & fail-closed startup tests):
1. `test_production_startup_rejects_missing_or_empty_secret_key`:
   - Validates that setting `ENVIRONMENT=production` with an empty or whitespace-only `SECRET_KEY` raises a Pydantic `ValidationError` containing `"SECRET_KEY is mandatory and cannot be empty"`.
2. `test_production_startup_rejects_weak_short_secret_key`:
   - Validates that a `SECRET_KEY` shorter than 32 characters raises a `ValidationError` containing `"must be at least 32 characters in production"`.
3. `test_production_startup_rejects_known_development_default_keys`:
   - Validates that known development defaults (e.g., `"supersecret_dev_key_change_in_production_reguflow360"`, `"dev_secret_key"`, `"changeme"`) are identified and refused with a `ValidationError` containing `"cannot use development default key"`.
4. `test_production_startup_rejects_debug_mode_true`:
   - Validates that setting `DEBUG=True` when `ENVIRONMENT=production` immediately aborts startup with `"DEBUG mode must be disabled in production"`.
5. `test_production_startup_rejects_demo_mode_true`:
   - Validates that setting `DEMO_MODE=True` when `ENVIRONMENT=production` immediately aborts startup with `"DEMO_MODE cannot be enabled in production"`.
6. `test_production_startup_rejects_sqlite_database`:
   - Validates that setting `DATABASE_URL=sqlite:///./test.db` when `ENVIRONMENT=production` immediately aborts startup with `"SQLite is prohibited in production; use an enterprise PostgreSQL database"`.
7. `test_production_startup_rejects_known_development_database_passwords`:
   - Validates that known dev passwords in `DATABASE_URL` (e.g. `:reguflow_secret@`, `:reguflow_secure_pass@`, `:postgres@`) are caught and refused with `"Insecure development database credentials detected in DATABASE_URL"`.
8. `test_production_startup_validation_does_not_leak_secret_value`:
   - Proves that validation failure messages never echo, log, or leak secret keys in plaintext.
9. `test_development_startup_allows_standard_dev_defaults`:
   - Proves regression safety: standard local development configuration (`ENVIRONMENT=development`, `DEBUG=True`, `DEMO_MODE=True`) initializes cleanly and `is_demo_allowed` resolves to `True`.
10. `test_seed_database_prohibited_in_production_runtime`:
    - Proves that calling `seed_database()` in production mode raises `RuntimeError("Production safety violation: Automatic seeding of shared demo identities and synthetic data is prohibited in production mode.")`, preventing accidental demo seed execution.

---

### 10. Judge Explorer Authorization, Regulatory Provenance & EVC Scope Hardening Test Coverage Summary (14 New Tests, Total 250 Tests)

`tests/test_judge_explorer_authorization_and_provenance.py` (14 comprehensive authorization, rule provenance, and scoping tests):
1. `test_judge_explorer_endpoints_require_authentication`:
   - Validates that unauthenticated requests to `/api/demo/scenarios`, `/api/demo/routes`, `/api/demo/explainability/{app_id}`, `/api/demo/telemetry`, and `/api/demo/reset-scenario/{scenario_id}` fail closed with `HTTP 401 Unauthorized`.
2. `test_judge_explorer_production_gate_fail_closed`:
   - Validates that when `DEMO_MODE=false` or `ENVIRONMENT=production`, all judge explorer endpoints return `HTTP 403 Forbidden` with `"Demonstration explorer is strictly disabled in production mode"`.
3. `test_explainability_rejects_arbitrary_or_unseeded_application_ids`:
   - Validates that passing unseeded or arbitrary application IDs (e.g. `999999`) returns `HTTP 404 Not Found`, restricting explainability queries strictly to the synthetic demo allowlist.
4. `test_explainability_enforces_tenant_and_regional_scoping`:
   - Validates that institution users querying another institution's application receive `HTTP 403 Forbidden`, Regional Officers querying outside their region receive `HTTP 403 Forbidden`, and unassigned Regional Officers fail closed with `HTTP 403 Forbidden`.
5. `test_scenario_reset_strictly_restricted_to_authorized_administrators`:
   - Validates that ordinary institution users, compliance officers, regional officers, and committee members attempting to reset demonstration scenarios receive `HTTP 403 Forbidden`.
6. `test_scenario_reset_permitted_for_authorized_demo_operator`:
   - Validates that System Administrators or users with administrative rule management permissions successfully reset synthetic scenarios with an atomic transaction and recorded reset audit event.
7. `test_scenario_5_reset_revokes_statutory_orders`:
   - Validates that resetting Scenario 5 (Competent Authority Decision & Statutory Order Generation) revokes previously issued statutory orders (`is_revoked=True`, `status="REVOKED"`) and cleanly restores the application to `AWAITING_COMPETENT_AUTHORITY`.
8. `test_demo_telemetry_leaseholder_token_redacted_for_non_admins`:
   - Validates that distributed scheduler leaseholder worker tokens are redacted (`holder_id="[REDACTED]"`) for non-administrative roles to protect infrastructure secrets.
9. `test_canonical_routes_registry_matches_workflow_engine_allowed_transitions`:
   - Proves complete parity between the authoritative route registry (`AUTHORITATIVE_ROUTES`) and the workflow engine's statutory state machine (`ALLOWED_TRANSITIONS`) across all 4 canonical routes (`ONLY_SCRUTINY`, `SCRUTINY_EVC`, `EVC_SAC_SHC`, `ONLY_EVC`).
10. `test_explainability_sla_grounded_in_rule_definitions`:
    - Validates that stage SLAs returned by `/api/demo/explainability/{app_id}` are grounded in active Rule Studio `RuleDefinition` records (`RULE_SCRUTINY_SLA`, `RULE_DEFICIENCY_CURE`, `RULE_EVC_SCHEDULE`), displaying rule version, calculation basis, and explicit illustrative policy flags without fabricated statutory citations.
11. `test_evc_inspection_access_scoping_per_role`:
    - Validates role-specific EVC scoping across Institution users (own institution only), Regional Officers (assigned region only), Committee Members (assigned panel inspections only), and EVC Coordinators (scheduling jurisdiction only).
12. `test_committee_member_unassigned_inspection_access_blocked`:
    - Validates that a Committee Member attempting to access an inspection with an active panel assignment belonging to another expert is denied with `HTTP 403 Forbidden`.
13. `test_system_admin_blocked_from_submitting_evc_report`:
    - Validates that System Administrators retain infrastructure monitoring permissions but are strictly prohibited from submitting EVC inspection reports (`HTTP 403 Forbidden`).
14. `test_system_admin_blocked_from_mobile_field_mutations`:
    - Validates that System Administrators are strictly prohibited from performing mobile field check-ins and recording field evidence (`HTTP 403 Forbidden`).



