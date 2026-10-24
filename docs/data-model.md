# Data Model Specification — ReguFlow 360
## Relational Schema & Entity Relationship Definitions
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. Schema Overview & Relational Integrity
ReguFlow 360 uses a normalized relational architecture implemented via SQLAlchemy 2.0 with strict foreign key constraints, explicit indexing on frequently filtered lookup columns (`institution_id`, `current_stage`, `due_date`, `expiry_date`, `idempotency_key`), and UTC-timestamped audit triggers.

```
                  +-------------------+
                  |   institutions    |
                  +---------+---------+
                            | 1
                            |
           +----------------+----------------+
           | *                               | *
+----------v----------+            +---------v---------+
|        users        |            |   applications    |
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
| compliance_undertake|            | document_records  |
+----------+----------+            +---------+---------+
           | 1                               | 1
           | *                               | *
+----------v----------+            +---------v---------+
| compliance_evidence |            | document_versions |
+---------------------+            +-------------------+

+---------------------+     +-----------------------+     +-------------------+
|    notifications    |     |   alert_escalations   |     |   audit_events    |
| (user / inst scope) |     | (idempotent triggers) |     | (immutable log)   |
+---------------------+     +-----------------------+     +-------------------+
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

#### 2.3 `applications` & `application_stages`
- `applications`:
  - `id` (Primary Key)
  - `application_number` (VARCHAR(64), UNIQUE, INDEXED) — E.g. `"AICTE-2026-EOA-98124"`
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `academic_year` (VARCHAR(16), NOT NULL) — E.g. `"2026-2027"`
  - `application_type` (VARCHAR(64), NOT NULL) — E.g. `"EOA_ANNUAL"`, `"NEW_INSTITUTION"`, `"INTAKE_VARIATION"`
  - `workflow_template_code` (VARCHAR(64), NOT NULL, DEFAULT `"EOA_ANNUAL"`)
  - `current_stage` (VARCHAR(64), NOT NULL, INDEXED)
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

#### 2.4 `deficiencies`
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

#### 2.5 Compliance Passport: `compliance_undertakings` & `compliance_evidence`
- `compliance_undertakings`:
  - `id` (Primary Key)
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `title` (VARCHAR(255), NOT NULL) — E.g. `"Establishment of Barrier-Free Access Ramps & Lift"`
  - `category` (VARCHAR(64), NOT NULL) — `"INFRASTRUCTURE"`, `"SAFETY"`, `"FACULTY"`, `"ACADEMIC"`
  - `description` (TEXT)
  - `due_date` (TIMESTAMP WITH TIME ZONE, NOT NULL, INDEXED)
  - `status` (VARCHAR(32), NOT NULL, DEFAULT `"NOT_YET_DUE"`) — `"NOT_YET_DUE"`, `"DUE_SOON"`, `"PENDING_VERIFICATION"`, `"VERIFIED"`, `"DEFICIENT"`, `"OVERDUE"`
  - `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `verified_by_id` (FK -> `users.id`, NULLABLE)
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `compliance_evidence`:
  - `id` (Primary Key)
  - `undertaking_id` (FK -> `compliance_undertakings.id`, ON DELETE CASCADE)
  - `version` (INTEGER, NOT NULL, DEFAULT 1)
  - `file_name` (VARCHAR(255), NOT NULL)
  - `file_url` (VARCHAR(512), NOT NULL)
  - `checksum_sha256` (VARCHAR(64), NOT NULL)
  - `remarks` (TEXT)
  - `submitted_by_id` (FK -> `users.id`)
  - `submitted_at` (TIMESTAMP WITH TIME ZONE)

#### 2.6 Document Lifecycle: `document_records` & `document_versions`
- `document_records`:
  - `id` (Primary Key)
  - `institution_id` (FK -> `institutions.id`, NOT NULL)
  - `document_type` (VARCHAR(64), NOT NULL) — E.g. `"LAND_LEASE_DEED"`, `"FIRE_SAFETY_NOC"`, `"BUILDING_STABILITY"`, `"OCCUPANCY_CERTIFICATE"`
  - `title` (VARCHAR(255), NOT NULL)
  - `document_number` (VARCHAR(128))
  - `issue_date` (DATE)
  - `expiry_date` (DATE, INDEXED) — E.g. 33-year lease expiration or annual Fire NOC date
  - `status` (VARCHAR(32), NOT NULL, DEFAULT `"ACTIVE"`) — `"ACTIVE"`, `"EXPIRING_SOON"`, `"RENEWAL_SUBMITTED"`, `"VERIFIED"`, `"EXPIRED"`
  - `current_version` (INTEGER, DEFAULT 1)
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `document_versions`:
  - `id` (Primary Key)
  - `document_record_id` (FK -> `document_records.id`, ON DELETE CASCADE)
  - `version` (INTEGER, NOT NULL)
  - `file_name` (VARCHAR(255), NOT NULL)
  - `file_url` (VARCHAR(512), NOT NULL)
  - `checksum_sha256` (VARCHAR(64), NOT NULL)
  - `uploaded_by_id` (FK -> `users.id`)
  - `uploaded_at` (TIMESTAMP WITH TIME ZONE)
  - `verification_status` (VARCHAR(32), DEFAULT `"PENDING"`) — `"PENDING"`, `"VERIFIED"`, `"REJECTED"`
  - `verified_by_id` (FK -> `users.id`, NULLABLE)
  - `verified_at` (TIMESTAMP WITH TIME ZONE, NULLABLE)
  - `verification_notes` (TEXT, NULLABLE)

#### 2.7 `evc_inspections`
- `id` (Primary Key)
- `application_id` (FK -> `applications.id`, NOT NULL)
- `inspection_type` (VARCHAR(32), NOT NULL) — `"PHYSICAL_ONSITE"`, `"VIRTUAL_REMOTE"`
- `scheduled_date` (TIMESTAMP WITH TIME ZONE, INDEXED)
- `convener_name` (VARCHAR(128))
- `expert_member_name` (VARCHAR(128))
- `status` (VARCHAR(32), NOT NULL, DEFAULT `"PENDING_ASSIGNMENT"`)
- `report_url` (VARCHAR(512), NULLABLE)
- `report_notes` (TEXT, NULLABLE)
- `recommendation` (VARCHAR(64), NULLABLE) — `"RECOMMENDED_APPROVAL"`, `"RECOMMENDED_REJECTION"`, `"DEFICIENCY_NOTED"`
- `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)

#### 2.8 `notifications` & `alert_escalations`
- `notifications`:
  - `id` (Primary Key)
  - `user_id` (FK -> `users.id`, NULLABLE)
  - `institution_id` (FK -> `institutions.id`, NULLABLE)
  - `title` (VARCHAR(255), NOT NULL)
  - `message` (TEXT, NOT NULL)
  - `channel` (VARCHAR(32), DEFAULT `"IN_APP"`)
  - `level` (VARCHAR(32), DEFAULT `"INFO"`) — `"INFO"`, `"WARNING"`, `"DANGER"`, `"SUCCESS"`
  - `is_read` (BOOLEAN, DEFAULT FALSE)
  - `link_url` (VARCHAR(255))
  - `created_at` (TIMESTAMP WITH TIME ZONE)
- `alert_escalations`:
  - `id` (Primary Key)
  - `idempotency_key` (VARCHAR(128), UNIQUE, INDEXED)
  - `entity_type` (VARCHAR(64), NOT NULL) — `"APPLICATION"`, `"UNDERTAKING"`, `"DOCUMENT"`, `"EVC"`
  - `entity_id` (INTEGER, NOT NULL)
  - `trigger_type` (VARCHAR(64), NOT NULL) — `"SLA_APPROACHING"`, `"SLA_OVERDUE"`, `"EXPIRY_WARNING"`
  - `threshold_days` (INTEGER, NOT NULL)
  - `escalation_level` (VARCHAR(64), NOT NULL) — `"REMINDER_L1"`, `"ESCALATION_L1_RO"`, `"ESCALATION_L2_BO"`, `"ESCALATION_L3_MEMBER_SEC"`
  - `recipient_role` (VARCHAR(64))
  - `status` (VARCHAR(32), DEFAULT `"ACTIVE"`) — `"ACTIVE"`, `"ACKNOWLEDGED"`, `"RESOLVED"`
  - `created_at` (TIMESTAMP WITH TIME ZONE)

#### 2.9 `audit_events` & `rule_definitions`
- `audit_events`:
  - `id` (Primary Key)
  - `actor_id` (INTEGER, NULLABLE)
  - `actor_name` (VARCHAR(128))
  - `actor_role` (VARCHAR(64))
  - `action` (VARCHAR(64), NOT NULL) — E.g. `"STAGE_TRANSITION"`, `"DEFICIENCY_ISSUED"`, `"EVIDENCE_VERIFIED"`, `"EVC_SCHEDULED"`
  - `entity_type` (VARCHAR(64), NOT NULL)
  - `entity_id` (INTEGER, NOT NULL)
  - `details` (JSON / TEXT)
  - `ip_address` (VARCHAR(64))
  - `created_at` (TIMESTAMP WITH TIME ZONE, DEFAULT UTC)
- `rule_definitions`:
  - `id` (Primary Key)
  - `rule_code` (VARCHAR(64), UNIQUE, NOT NULL)
  - `name` (VARCHAR(128), NOT NULL)
  - `category` (VARCHAR(64), NOT NULL)
  - `version` (VARCHAR(16), NOT NULL, DEFAULT `"1.0.0"`)
  - `config_json` (TEXT, NOT NULL)
  - `is_active` (BOOLEAN, DEFAULT TRUE)
  - `updated_at` (TIMESTAMP WITH TIME ZONE)
