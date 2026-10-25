# Data Model Specification — ReguFlow 360
## Relational Schema & Entity Relationship Definitions
**SIH 2026 Problem Statement 26262**  
**Version:** 3.0.0 (Phase 4 Hardened)

---

### 1. Schema Overview & Relational Integrity
ReguFlow 360 uses a normalized relational architecture implemented via SQLAlchemy 2.0 with strict foreign key constraints, explicit indexing on frequently filtered lookup columns (`institution_id`, `current_stage`, `due_date`, `expiry_date`, `idempotency_key`), monotonic versioning for optimistic locking, and UTC-timestamped audit triggers.
Phase 3 establishes an immutable, versioned document store, explicit institutional compliance passport undertakings with structured evidence histories, and EVC inspection panel coordination with prerequisite enforcement in the workflow state machine.
Phase 4 introduces a deterministic, multi-vector deadline and escalation engine with an autonomous background scheduler, cycle-aware deduplication keys, persistent engine run telemetry, and multi-tier escalation chains across application stages, compliance undertakings, document renewals, and EVC visits.

```
                  +-------------------+
                  |   institutions    |
                  +---------+---------+
                            | 1
                            |
           +----------------+----------------+
           | *                               | *
+----------v----------+            +---------v---------+
|        users        |            |   applications    |  (version: Integer, evc_required: Boolean)
+----------+----------+            +----+----+----+----+
           | 1                          | 1  | 1  | 1
           | *                          | *  | *  | 1
+----------v----------+      +----------v-+  |    |
|     user_roles      |      | app_stages |  |    +--------+
+---------------------+      +------------+  | *           | 1
                                       +-----v--------+ +--v------------+
                                       | deficiencies | |evc_inspections|
                                       +--------------+ +---------------+

                  +-------------------+
                  |   institutions    |
                  +---------+---------+
                            | 1
                            |
           +----------------+----------------+
           | *                               | *
+----------v----------+            +---------v---------+
| compliance_undertake|            | document_records  | (issuing_authority, valid_from, renewal_required)
+----------+----------+            +---------+---------+
           | 1                               | 1
           | *                               | *
+----------v----------+            +---------v---------+
| compliance_evidence |            | document_versions | (storage_key, mime_type, file_size, SHA-256)
+---------------------+            +-------------------+

+---------------------+     +-----------------------+     +-----------------------+     +-------------------+
|    notifications    |     |   alert_escalations   |     | deadline_engine_runs  |     |   audit_events    |
| (user / role / inst)|     | (cycle-aware key)     |     | (scheduler telemetry) |     | (immutable log)   |
+---------------------+     +-----------------------+     +-----------------------+     +-------------------+
```

---

### 2. Entity Definitions

#### 2.1 `institutions`
- `id` (UUID / Integer Primary Key)
- `code` (VARCHAR(32), UNIQUE, INDEXED) — E.g. `"1-3324901"` (AICTE Permanent Institute ID)
- `name` (VARCHAR(255), NOT NULL) — E.g. `"Apex Institute of Technology & Management"`
- `category` (VARCHAR(64)) — E.g. `"ENGINEERING_AND_TECHNOLOGY"`, `"MANAGEMENT"`, `"PHARMACY"`
- `state` (VARCHAR(64), NOT NULL) — E.g. `"Maharashtra"`, `"Delhi"`
- `region` (VARCHAR(64), NOT NULL, INDEXED) — E.g. `"Western"`, `"Northern"`, `"Southern"`
- `address` (TEXT)
- `contact_email` (VARCHAR(255), NOT NULL)
- `contact_phone` (VARCHAR(32))
- `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE, DEFAULT UTC)

#### 2.2 `users` & `user_roles`
- `users`:
  - `id` (UUID / Integer Primary Key)
  - `email` (VARCHAR(255), UNIQUE, INDEXED)
  - `hashed_password` (VARCHAR(255), NOT NULL)
  - `full_name` (VARCHAR(128), NOT NULL)
  - `institution_id` (FK -> `institutions.id`, NULLABLE for AICTE officers)
  - `region` (VARCHAR(64), NULLABLE, for Regional Officers)
  - `is_active` (BOOLEAN, DEFAULT TRUE)
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `user_roles`:
  - `id` (Primary Key)
  - `user_id` (FK -> `users.id`, ON DELETE CASCADE)
  - `role` (VARCHAR(64), NOT NULL) — Enum (`INSTITUTION_ADMIN`, `COMPLIANCE_OFFICER`, `REGIONAL_OFFICER`, `BUREAU_OFFICER`, `COMMITTEE_MEMBER`, `EVC_COORDINATOR`, `COMPETENT_AUTHORITY`, `SYSTEM_ADMIN`)

#### 2.3 `revoked_tokens` (Hardened Token Invalidation)
- `id` (Primary Key)
- `jti` (VARCHAR(64), UNIQUE, INDEXED, NOT NULL) — Unique token identifier claim
- `token_type` (VARCHAR(32), NOT NULL, DEFAULT `"access"`)
- `revoked_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT UTC)
- `expires_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)

#### 2.4 `applications` & `application_stages`
- `applications`:
  - `id` (Primary Key)
  - `application_number` (VARCHAR(64), UNIQUE, INDEXED) — E.g. `"AICTE-2026-EOA-98124"`
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `academic_year` (VARCHAR(16), NOT NULL) — E.g. `"2026-2027"`
  - `application_type` (VARCHAR(64), NOT NULL) — E.g. `"EOA_ANNUAL"`, `"NEW_INSTITUTION"`, `"INTAKE_VARIATION"`
  - `workflow_template_code` (VARCHAR(64), NOT NULL, DEFAULT `"EOA_ANNUAL"`)
  - `current_stage` (VARCHAR(64), NOT NULL, INDEXED)
  - `version` (INTEGER, NOT NULL, DEFAULT 1) — **Monotonic Optimistic Lock Version**
  - `evc_required` (BOOLEAN, NOT NULL, DEFAULT FALSE) — Explicit route flag for mandatory physical / virtual EVC inspections
  - `scrutiny_officer_id` (FK -> `users.id`, NULLABLE)
  - `priority_score` (INTEGER, DEFAULT 0) — 0 to 100 Explainable Priority Index
  - `priority_factors` (JSON / TEXT) — Itemized explanation breakdown
  - `submitted_at`, `approved_at`, `rejected_at` (TIMESTAMP WITH TIME ZONE)
  - `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)
- `application_stages` (Timeline):
  - `id` (Primary Key)
  - `application_id` (FK -> `applications.id`, ON DELETE CASCADE)
  - `from_stage` (VARCHAR(64))
  - `to_stage` (VARCHAR(64), NOT NULL)
  - `actor_id` (FK -> `users.id`)
  - `actor_role` (VARCHAR(64))
  - `remarks` (TEXT)
  - `created_at` (TIMESTAMP WITH TIME ZONE)

#### 2.5 `deficiencies`
- `id` (Primary Key)
- `application_id` (FK -> `applications.id`, ON DELETE CASCADE)
- `category` (VARCHAR(64), NOT NULL) — E.g. `"INFRASTRUCTURE"`, `"FACULTY_CADRE"`, `"FINANCIAL_AUDIT"`, `"LAND_TITLE"`
- `description` (TEXT, NOT NULL)
- `required_document` (VARCHAR(255))
- `status` (VARCHAR(32), NOT NULL, DEFAULT `"OPEN"`) — `"OPEN"`, `"CURED"`, `"WAIVED"`
- `cure_document_url` (VARCHAR(512), NULLABLE)
- `cure_remarks` (TEXT, NULLABLE)
- `cured_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
- `resolved_by_officer_id` (FK -> `users.id`, NULLABLE)
- `created_at` (TIMESTAMP WITH TIME ZONE)

#### 2.6 Compliance Passport: `compliance_undertakings` & `compliance_evidence`
- `compliance_undertakings`:
  - `id` (Primary Key)
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `application_id` (FK -> `applications.id`, NULLABLE) — Linked approval application
  - `rule_code` (VARCHAR(64), NULLABLE) — Configurable APH rule reference
  - `title` (VARCHAR(255), NOT NULL)
  - `category` (VARCHAR(64), NOT NULL) — `"BIOMETRIC_ATTENDANCE"`, `"FIRE_SAFETY"`, `"FACULTY_SALARY"`, etc.
  - `description` (TEXT)
  - `due_date` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)
  - `status` (VARCHAR(32), NOT NULL, DEFAULT `"NOT_YET_DUE"`) — `"NOT_YET_DUE"`, `"DUE_SOON"`, `"PENDING_VERIFICATION"`, `"UNDER_VERIFICATION"`, `"CORRECTION_REQUIRED"`, `"VERIFIED"`, `"DEFICIENT"`, `"OVERDUE"`
  - `responsible_user_id` (FK -> `users.id`, NULLABLE) — Institution officer accountable
  - `reviewer_id` (FK -> `users.id`, NULLABLE) — AICTE officer assigned for review
  - `evidence_type` (VARCHAR(64), DEFAULT `"PDF_DOCUMENT"`) — Prescribed evidence format
  - `fulfilled_at` (TIMESTAMP WITH TIME ZONE, NULLABLE) — Timestamp evidence was accepted
  - `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `verified_by_id` (FK -> `users.id`, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `compliance_evidence`:
  - `id` (Primary Key)
  - `undertaking_id` (FK -> `compliance_undertakings.id`, ON DELETE CASCADE)
  - `version` (INTEGER, NOT NULL, DEFAULT 1) — Sequential immutable version
  - `file_name` (VARCHAR(255), NOT NULL)
  - `file_url` (VARCHAR(512), NOT NULL)
  - `storage_key` (VARCHAR(255), NULLABLE) — Sanitized private storage identifier
  - `file_size` (INTEGER, NULLABLE) — Exact byte count
  - `mime_type` (VARCHAR(64), NULLABLE) — Validated media type
  - `checksum_sha256` (VARCHAR(64), NOT NULL) — SHA-256 integrity hash
  - `remarks` (TEXT)
  - `submitted_by_id` (FK -> `users.id`)
  - `submitted_at` (TIMESTAMP WITH TIME ZONE)
  - `verification_status` (VARCHAR(32), DEFAULT `"PENDING"`)
  - `verified_by_id` (FK -> `users.id`, NULLABLE)
  - `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `verification_notes` (TEXT, NULLABLE)

#### 2.7 Document Lifecycle: `document_records` & `document_versions`
- `document_records`:
  - `id` (Primary Key)
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `application_id` (FK -> `applications.id`, NULLABLE)
  - `document_type` (VARCHAR(64), NOT NULL) — `"LAND_DEED_33YR"`, `"FIRE_NOC"`, `"BUILDING_PLAN"`, etc.
  - `title` (VARCHAR(255), NOT NULL)
  - `document_number` (VARCHAR(128))
  - `issuing_authority` (VARCHAR(255), NULLABLE) — E.g. `"Sub-Registrar Pune"`, `"Fire Safety Bureau"`
  - `valid_from` (DATE, NULLABLE)
  - `issue_date` (DATE, NULLABLE)
  - `expiry_date` (DATE, NULLABLE, INDEXED) — Supports documents with continuous / no expiry
  - `renewal_required` (BOOLEAN, DEFAULT TRUE)
  - `status` (VARCHAR(32), NOT NULL, DEFAULT `"ACTIVE"`) — `"ACTIVE"`, `"EXPIRING_SOON"`, `"RENEWAL_SUBMITTED"`, `"VERIFIED"`, `"EXPIRED"`
  - `current_version` (INTEGER, DEFAULT 1)
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `document_versions`:
  - `id` (Primary Key)
  - `document_record_id` (FK -> `document_records.id`, ON DELETE CASCADE)
  - `version` (INTEGER, NOT NULL)
  - `file_name` (VARCHAR(255), NOT NULL)
  - `file_url` (VARCHAR(512), NOT NULL)
  - `storage_key` (VARCHAR(255), NULLABLE)
  - `file_size` (INTEGER, NULLABLE)
  - `mime_type` (VARCHAR(64), NULLABLE)
  - `checksum_sha256` (VARCHAR(64), NOT NULL)
  - `renewal_reason` (TEXT, NULLABLE)
  - `uploaded_by_id` (FK -> `users.id`)
  - `uploaded_at` (TIMESTAMP WITH TIME ZONE)
  - `verification_status` (VARCHAR(32), DEFAULT `"PENDING"`) — `"PENDING"`, `"VERIFIED"`, `"REJECTED"`
  - `verified_by_id` (FK -> `users.id`, NULLABLE)
  - `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `verification_notes` (TEXT, NULLABLE)

#### 2.8 `evc_inspections`
- `id` (Primary Key)
- `application_id` (FK -> `applications.id`, NOT NULL)
- `inspection_type` (VARCHAR(32), NOT NULL) — `"PHYSICAL_ONSITE"`, `"VIRTUAL_REMOTE"`
- `scheduled_date` (TIMESTAMP WITH TIME ZONE, INDEXED)
- `convener_name` (VARCHAR(128))
- `expert_member_name` (VARCHAR(128))
- `coordinator_id` (FK -> `users.id`, NULLABLE) — EVC Coordinator who scheduled
- `convener_user_id` (FK -> `users.id`, NULLABLE) — Panel Convener user record
- `expert_user_id` (FK -> `users.id`, NULLABLE) — Panel Expert user record
- `completed_at` (TIMESTAMP WITH TIME ZONE, NULLABLE) — Exact visit sign-off timestamp
- `completed_by_id` (FK -> `users.id`, NULLABLE) — Official who certified completion
- `status` (VARCHAR(32), NOT NULL, DEFAULT `"PENDING_ASSIGNMENT"`) — `"PENDING_ASSIGNMENT"`, `"SCHEDULED"`, `"IN_PROGRESS"`, `"REPORT_SUBMITTED"`, `"DEFICIENCY_NOTED"`, `"RECOMMENDED_APPROVAL"`, `"RECOMMENDED_REJECTION"`
- `report_url` (VARCHAR(512), NULLABLE)
- `report_notes` (TEXT, NULLABLE)
- `recommendation` (VARCHAR(64), NULLABLE) — `"RECOMMENDED_APPROVAL"`, `"DEFICIENCY_NOTED"`, `"RECOMMENDED_REJECTION"`
- `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)

#### 2.9 `notifications`, `alert_escalations` & `deadline_engine_runs`
- `notifications`:
  - `id` (Primary Key)
  - `user_id` (FK -> `users.id`, NULLABLE) — Specific recipient user record
  - `recipient_role` (VARCHAR(64), NULLABLE, INDEXED) — Role-targeted broadcasts (e.g. `REGIONAL_OFFICER`, `BUREAU_OFFICER`)
  - `institution_id` (FK -> `institutions.id`, NULLABLE, INDEXED) — Tenant isolation scope
  - `entity_type` (VARCHAR(64), NULLABLE, INDEXED) — Regulatory entity reference (`APPLICATION`, `UNDERTAKING`, `DOCUMENT`, `EVC`)
  - `entity_id` (INTEGER, NULLABLE, INDEXED) — Foreign reference identifier
  - `title` (VARCHAR(255), NOT NULL)
  - `message` (TEXT, NOT NULL)
  - `channel` (VARCHAR(32), DEFAULT `"IN_APP"`)
  - `level` (VARCHAR(32), DEFAULT `"INFO"`) — `"INFO"`, `"WARNING"`, `"CRITICAL"`
  - `delivery_channel` (VARCHAR(32), DEFAULT `"IN_APP"`) — `"IN_APP"`, `"EMAIL"`, `"SMS"`
  - `delivery_status` (VARCHAR(32), DEFAULT `"DELIVERED"`) — `"PENDING"`, `"DELIVERED"`, `"FAILED"`, `"SIMULATED"`
  - `is_read` (BOOLEAN, DEFAULT FALSE)
  - `read_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `link_url` (VARCHAR(255)) — Deep action link to application/passport/EVC view
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `alert_escalations`:
  - `id` (Primary Key)
  - `idempotency_key` (VARCHAR(128), UNIQUE, INDEXED) — Deterministic SHA-256 deduplication key: `hash(f"{entity_type}:{entity_id}:{trigger_type}:{threshold_days}:{escalation_level}:{recipient_role}:{cycle_id}")`
  - `entity_type` (VARCHAR(64), NOT NULL) — `"APPLICATION"`, `"UNDERTAKING"`, `"DOCUMENT"`, `"EVC"`
  - `entity_id` (INTEGER, NOT NULL)
  - `trigger_type` (VARCHAR(64), NOT NULL) — `"REMINDER_UPCOMING"`, `"OVERDUE_ESCALATION"`, `"EXPIRY_WARNING"`, `"VISIT_COMPLETION"`
  - `threshold_days` (INTEGER, NOT NULL)
  - `escalation_level` (VARCHAR(64), NOT NULL) — `"REMINDER_L1"`, `"REMINDER_L2"`, `"ESCALATION_L1_RO"`, `"ESCALATION_L2_BO"`, `"ESCALATION_L3_MEMBER_SEC"`
  - `recipient_role` (VARCHAR(64))
  - `status` (VARCHAR(32), DEFAULT `"ACTIVE"`) — `"ACTIVE"`, `"ACKNOWLEDGED"`, `"RESOLVED"`, `"CLOSED"`
  - `cycle_id` (VARCHAR(64), DEFAULT `"v1"`, INDEXED) — Cycle discriminator enabling alert generation on reopened/returned cycles
  - `rule_code` (VARCHAR(64), NULLABLE) — Originating Rule Studio policy code
  - `rule_version` (VARCHAR(16), NULLABLE) — Snapshot of rule configuration version at trigger time
  - `region` (VARCHAR(64), NULLABLE, INDEXED) — Regional boundary for RO scoping
  - `institution_id` (INTEGER, NULLABLE, INDEXED) — Institution tenancy identifier
  - `resolved_at` (TIMESTAMP WITH TIME ZONE, NULLABLE) — Auto-resolution or official closure timestamp
  - `resolved_reason` (TEXT, NULLABLE) — E.g. `"Deficiency cured by institution"`, `"Document renewal verified"`
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `deadline_engine_runs`:
  - `id` (Primary Key)
  - `run_id` (VARCHAR(64), UNIQUE, INDEXED, NOT NULL) — UUID string for run trace
  - `trigger_mode` (VARCHAR(32), NOT NULL) — `"SCHEDULED_WORKER"`, `"ON_DEMAND_MANUAL"`
  - `scanned_entities` (INTEGER, DEFAULT 0)
  - `reminders_created` (INTEGER, DEFAULT 0)
  - `escalations_created` (INTEGER, DEFAULT 0)
  - `duplicates_prevented` (INTEGER, DEFAULT 0)
  - `resolved_count` (INTEGER, DEFAULT 0)
  - `execution_time_ms` (INTEGER, DEFAULT 0)
  - `status` (VARCHAR(32), DEFAULT `"SUCCESS"`) — `"SUCCESS"`, `"FAILED"`, `"PARTIAL"`
  - `error_message` (TEXT, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT UTC)

#### 2.10 `audit_events`, `rule_definitions`, `rule_version_history` & `scheduler_leases`
- `audit_events`:
  - `id` (Primary Key)
  - `actor_id` (INTEGER, NULLABLE)
  - `actor_name` (VARCHAR(128))
  - `actor_role` (VARCHAR(64))
  - `action` (VARCHAR(64), NOT NULL)
  - `entity_type` (VARCHAR(64), NOT NULL)
  - `entity_id` (INTEGER, NOT NULL)
  - `details` (JSON / TEXT)
  - `ip_address` (VARCHAR(64))
  - `institution_id` (INTEGER, NULLABLE, INDEXED) — Phase 5: Tenant scoping
  - `region` (VARCHAR(64), NULLABLE, INDEXED) — Phase 5: Regional jurisdiction scoping
  - `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT UTC)
- `rule_definitions`:
  - `id` (Primary Key)
  - `rule_code` (VARCHAR(64), UNIQUE, NOT NULL)
  - `name` (VARCHAR(128), NOT NULL)
  - `category` (VARCHAR(64), NOT NULL)
  - `version` (VARCHAR(16), NOT NULL, DEFAULT `"1.0.0"`)
  - `config_json` (TEXT, NOT NULL)
  - `is_active` (BOOLEAN, DEFAULT TRUE)
  - `status` (VARCHAR(32), NOT NULL, DEFAULT `"PUBLISHED"`) — Phase 5: `DRAFT`, `VALIDATED`, `PUBLISHED`, `RETIRED`
  - `description` (TEXT, NULLABLE)
  - `created_by_id` (INTEGER, FK -> `users.id`, NULLABLE)
  - `change_reason` (TEXT, NULLABLE)
  - `effective_from` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `updated_at` (TIMESTAMP WITH TIME ZONE)
- `rule_version_history` (Phase 5 Immutable Policy Ledger):
  - `id` (Primary Key)
  - `rule_id` (INTEGER, FK -> `rule_definitions.id`, ON DELETE CASCADE, INDEXED)
  - `rule_code` (VARCHAR(64), INDEXED, NOT NULL)
  - `version` (VARCHAR(16), NOT NULL)
  - `category` (VARCHAR(64), NOT NULL)
  - `config_json` (TEXT, NOT NULL)
  - `status` (VARCHAR(32), NOT NULL)
  - `change_reason` (TEXT, NULLABLE)
  - `created_by_id` (INTEGER, FK -> `users.id`, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT UTC)
- `scheduler_leases` (Phase 5 Distributed Lease Coordination):
  - `id` (Primary Key)
  - `lease_name` (VARCHAR(64), UNIQUE, NOT NULL, INDEXED) — E.g. `"deadline_engine_scan"`
  - `holder_id` (VARCHAR(128), NOT NULL) — Unique worker process UUID
  - `acquired_at` (TIMESTAMP WITH TIME ZONE, NOT NULL)
  - `expires_at` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)
  - `last_heartbeat` (TIMESTAMP WITH TIME ZONE, NOT NULL)

