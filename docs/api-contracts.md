# API Contracts & OpenAPI Specification — ReguFlow 360
## RESTful Endpoints, Schemas, and Response Envelopes
**SIH 2026 Problem Statement 26262**  
**Version:** 2.0.0 (Phase 2 Hardened)

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
- `GET /api/applications/{id}`: Detailed application dossier, stages timeline, assigned scrutiny officer, priority score, monotonic `version`, and deficiencies.
- `POST /api/applications/{id}/transition`: Advance or return application stage (`to_stage`, `remarks`, `expected_version`). Validates state preconditions, separation of duties, and optimistic version lock. Returns `409 Conflict` on stale version.
- `POST /api/applications/{id}/deficiencies`: Issue deficiency items (Authorized Regional/Bureau Officer only).
- `POST /api/applications/{id}/cure-deficiency`: Upload cure document and remarks for a deficiency (`INSTITUTION_ADMIN` or `COMPLIANCE_OFFICER` only).

#### 2.3 Compliance Passport (`/api/compliance`)
- `GET /api/compliance/undertakings`: List undertakings for an institution with status filters (`OVERDUE`, `DUE_SOON`, `PENDING_VERIFICATION`, `VERIFIED`).
- `POST /api/compliance/undertakings`: Define a new time-bound undertaking.
- `POST /api/compliance/undertakings/{id}/submit-evidence`: Submit compliance proof document (creates version, calculates SHA-256).
- `POST /api/compliance/undertakings/{id}/verify`: Verify or reject submitted evidence with official notes (`REGIONAL_OFFICER` or `BUREAU_OFFICER` within regional scope).

#### 2.4 Document Lifecycle & Renewals (`/api/documents`)
- `GET /api/documents`: List tracked statutory documents (Land Lease, Fire NOC, Building Plan).
- `POST /api/documents`: Register a new document record.
- `POST /api/documents/{id}/renew`: Submit renewal document version with new expiry date.
- `POST /api/documents/{id}/verify-version/{version_id}`: AICTE Officer verification sign-off within regional scope.
- `GET /api/documents/download/{filename}`: Safe, authenticated download endpoint with path-traversal prevention.

#### 2.5 EVC Management (`/api/evc`)
- `GET /api/evc/queue`: List applications pending inspection scheduling or inspection reports.
- `POST /api/evc/schedule`: Form panel (convener, expert), set inspection date, mode (`PHYSICAL_ONSITE` / `VIRTUAL_REMOTE`). Scoped to authorized region.
- `POST /api/evc/{id}/submit-report`: Upload signed committee inspection findings and recommendation (`RECOMMENDED_APPROVAL`, etc.).

#### 2.6 Alerts, Deadlines & Escalations (`/api/alerts`)
- `GET /api/alerts`: List notifications and active escalations for the current user/tenant.
- `POST /api/alerts/run-scan`: Trigger idempotent deadline and escalation evaluation pass.
- `POST /api/alerts/{id}/acknowledge`: Mark escalation acknowledged by an authorized officer.

#### 2.7 Rule Studio & Audit Trail (`/api/rules`, `/api/audit`, `/api/reports`)
- `GET /api/rules`: List configurable workflow templates and SLA thresholds.
- `POST /api/rules`: Create or update a versioned rule set (`SYSTEM_ADMIN` only).
- `GET /api/audit`: Query append-only audit trail with entity and actor filters (`audit.read` permission required).
- `GET /api/reports/summary`: Aggregate operational metrics (stage distribution, pendency ageing, compliance rates).
- `GET /api/health`: Health status endpoint returning database connection status and server timestamp.
