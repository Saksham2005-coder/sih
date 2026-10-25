# API Contracts & OpenAPI Specification — ReguFlow 360
## RESTful Endpoints, Schemas, and Response Envelopes
**SIH 2026 Problem Statement 26262**  
**Version:** 4.0.0 (Phase 4 Completed)

---

### 1. Global Standard Response Format
All JSON responses follow a predictable structure:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "meta": {
    "timestamp": "2026-10-25T02:00:00Z",
    "total": 12,
    "page": 1,
    "limit": 20
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN_INSTITUTION_ACCESS",
    "message": "Access denied: User does not belong to the target institution",
    "details": []
  }
}
```

Standard error codes:
- `AUTHENTICATION_REQUIRED` (HTTP 401)
- `TOKEN_EXPIRED` (HTTP 401)
- `TOKEN_REVOKED` (HTTP 401)
- `INVALID_CREDENTIALS` (HTTP 401)
- `ACCOUNT_DEACTIVATED` (HTTP 403)
- `PERMISSION_DENIED` (HTTP 403)
- `FORBIDDEN_INSTITUTION_ACCESS` (HTTP 403)
- `FORBIDDEN_REGIONAL_ACCESS` (HTTP 403)
- `NOT_FOUND` (HTTP 404)
- `STALE_STATE_CONFLICT` (HTTP 409)
- `ILLEGAL_TRANSITION` (HTTP 400)
- `OPEN_DEFICIENCIES_EXIST` (HTTP 400)
- `UNCURED_DEFICIENCIES_REMAIN` (HTTP 400)
- `REMARKS_REQUIRED` (HTTP 400)
- `FILE_TOO_LARGE` (HTTP 413)
- `UNSUPPORTED_MEDIA_TYPE` (HTTP 415)
- `INVALID_FILE_SIGNATURE` (HTTP 400)
- `EVC_COMPLETION_REQUIRED` (HTTP 400)
- `NOTES_REQUIRED` (HTTP 400)

---

### 2. Core API Endpoints

#### 2.1 Authentication & Profile (`/api/auth`)
- `POST /api/auth/login`: Authenticate with email and password. Returns JWT token, user profile, permitted roles, active role, institution details, and effective permissions.
- `GET /api/auth/me`: Fetch current authenticated user, active role, and institution scope.
- `POST /api/auth/logout`: Revoke active session token. Stores token `jti` in `revoked_tokens` table.
- `POST /api/auth/switch-active-role`: Switch active operational role among verified assigned roles for the current user. Validates role membership on backend.
- `GET /api/auth/demo-users`: Seeded demo persona list. Gated strictly: returns `403 Forbidden` if `DEMO_MODE=false` or `ENVIRONMENT=production`.

#### 2.2 Applications Lifecycle (`/api/applications`)
- `GET /api/applications`: List applications with filters (`stage`, `region`, `academic_year`, `search`, `page`, `limit`). Scoped strictly by institution for institution users and regional boundary for ROs.
- `POST /api/applications`: Create a new regulatory application (`INSTITUTION_ADMIN` only).
- `GET /api/applications/{id}`: Detailed application dossier, stages timeline, assigned scrutiny officer, priority score, monotonic `version`, `evc_required` flag, and deficiencies.
- `POST /api/applications/{id}/transition`: Advance or return application stage (`to_stage`, `remarks`, `expected_version`). Validates state preconditions, mandatory EVC prerequisites, separation of duties, and optimistic version lock. Returns `409 Conflict` on stale version.
- `POST /api/applications/{id}/deficiencies`: Issue deficiency items (Authorized Regional/Bureau Officer only).
- `POST /api/applications/{id}/cure-deficiency`: Upload cure document and remarks for a deficiency (`INSTITUTION_ADMIN` or `COMPLIANCE_OFFICER` only).

#### 2.3 Compliance Passport (`/api/compliance`)
- `GET /api/compliance/undertakings`: List undertakings for an institution with status filters (`OVERDUE`, `DUE_SOON`, `PENDING_VERIFICATION`, `UNDER_VERIFICATION`, `CORRECTION_REQUIRED`, `VERIFIED`, `DEFICIENT`, `NOT_YET_DUE`).
- `POST /api/compliance/undertakings`: Define a new time-bound undertaking with structured fields (`rule_code`, `due_date`, `evidence_type`).
- `POST /api/compliance/undertakings/{id}/submit-evidence`: Submit compliance proof document (multipart form: validates file size <= 10MB, extension, magic bytes, computes SHA-256, cleans up orphans on DB failure). Transitions status to `PENDING_VERIFICATION`.
- `POST /api/compliance/undertakings/{id}/verify`: Verify, request correction, or mark deficient with mandatory official notes (`REGIONAL_OFFICER` or `BUREAU_OFFICER` within regional scope; self-verification blocked).

#### 2.4 Document Lifecycle & Secure Storage (`/api/documents`)
- `GET /api/documents`: List tracked statutory documents (Land Lease, Fire NOC, Building Plan) with validity dates and version histories.
- `POST /api/documents`: Register a new document record.
- `POST /api/documents/{id}/renew`: Submit renewal document version with new expiry date. Validates file integrity, stores securely, preserves preceding versions.
- `POST /api/documents/{id}/verify-version/{version_id}`: AICTE Officer verification sign-off within regional scope. Rejection preserves original validity without extending expiry.
- `GET /api/documents/download/{filename}`: Safe, authenticated download endpoint with path-traversal prevention and resource-level access scope verification.
- `GET /api/documents/{document_id}/download/{version_id}`: Resource-scoped authenticated document version download.

#### 2.5 EVC Management (`/api/evc`)
- `GET /api/evc/queue`: List applications eligible for inspection scheduling (filtering non-EVC applications and enforcing route eligibility) or awaiting inspection reports.
- `POST /api/evc/schedule`: Form panel (convener, expert), set inspection date, mode (`PHYSICAL_ONSITE` / `VIRTUAL_REMOTE`). Enforces future date validation, panel completeness, and regional jurisdiction.
- `POST /api/evc/{id}/submit-report`: Upload signed committee inspection findings and recommendation (`RECOMMENDED_APPROVAL`, `DEFICIENCY_NOTED`, `RECOMMENDED_REJECTION`). Transitions application to `EVC_COMPLETED` without prematurely approving.

#### 2.6 Alerts, Deadlines & Escalations (`/api/alerts`)
- `GET /api/alerts`: Aggregate payload containing both user/tenant notifications and active escalations (backward-compatible).
- `GET /api/alerts/notifications`: List notifications with query parameters (`is_read`, `channel`, `page`, `limit`). Tenant-scoped for institutions; role-targeted and broadcast-scoped for AICTE officers. Response metadata includes total and unread counts.
- `POST /api/alerts/notifications/{id}/read`: Mark a single notification as read. Enforces strict ownership checks (user or institution scope).
- `POST /api/alerts/notifications/mark-all-read`: Mark all scoped notifications as read for current user/institution.
- `GET /api/alerts/escalations`: List active and historical escalations with query parameters (`status`, `entity_type`, `page`, `limit`). Regional Officers are strictly restricted to escalations within their assigned region or unassigned regional scope (`region == current_user.region`). Bureau Officers, Competent Authority, and System Admins access national scope.
- `POST /api/alerts/escalations/{id}/acknowledge`: Mark escalation acknowledged with optional officer follow-up remarks (`AcknowledgeEscalationRequest`). Validates regional jurisdiction guard (cross-region returns `403 Forbidden`) and appends an immutable audit event.
- `GET /api/alerts/engine-status`: Operational telemetry endpoint returning `is_running`, `scan_interval_seconds`, `last_run` summary (items examined, reminders, escalations, duplicates prevented, execution time), and lifetime aggregate statistics (`total_runs`, `total_reminders_created`, `total_escalations_created`).
- `POST /api/alerts/run-scan`: Trigger an on-demand, multi-vector deadline and escalation scan pass. Protected by RBAC (`rules.manage` or `application.transition` permission required). Records run metadata in `deadline_engine_runs` table and returns `DeadlineEngineRunResponse`.

#### 2.7 Rule Studio & Audit Trail (`/api/rules`, `/api/audit`, `/api/reports`)
- `GET /api/rules`: List configurable workflow templates and SLA thresholds.
- `POST /api/rules`: Create or update a versioned rule set (`SYSTEM_ADMIN` only).
- `GET /api/audit`: Query append-only audit trail with entity and actor filters (`audit.read` permission required).
- `GET /api/reports/summary`: Aggregate operational metrics (stage distribution, pendency ageing, compliance rates).
- `GET /api/health`: Health status endpoint returning database connection status and server timestamp.
