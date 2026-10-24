# API Contracts & OpenAPI Specification — ReguFlow 360
## RESTful Endpoints, Schemas, and Response Envelopes
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. Global Standard Response Format
All JSON responses follow a predictable structure.

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
    "code": "PERMISSION_DENIED",
    "message": "Institution user cannot perform final statutory approval",
    "details": []
  }
}
```

---

### 2. Core API Endpoints

#### 2.1 Authentication & Profile (`/api/auth`)
- `POST /api/auth/login`: Authenticate with email and password. Returns JWT token, user profile, permitted roles, and institution details.
- `GET /api/auth/me`: Fetch current authenticated user, active roles, and institution scope.
- `POST /api/auth/switch-active-role`: Switch active operational role among assigned user roles.

#### 2.2 Applications Lifecycle (`/api/applications`)
- `GET /api/applications`: List applications with filters (`stage`, `region`, `academic_year`, `search`, `page`, `limit`). Scoped by tenant for institution users.
- `POST /api/applications`: Create a new regulatory application (Institution Admin only).
- `GET /api/applications/{id}`: Detailed application dossier, stages timeline, assigned scrutiny officer, priority score, and deficiencies.
- `POST /api/applications/{id}/transition`: Advance or return application stage (`to_stage`, `remarks`).
- `POST /api/applications/{id}/deficiencies`: Issue deficiency items (Regional/Bureau Officer only).
- `POST /api/applications/{id}/cure-deficiency`: Upload cure document and remarks for a deficiency (Institution only).

#### 2.3 Compliance Passport (`/api/compliance`)
- `GET /api/compliance/undertakings`: List undertakings for an institution with status filters (`OVERDUE`, `DUE_SOON`, `PENDING_VERIFICATION`, `VERIFIED`).
- `POST /api/compliance/undertakings`: Define a new time-bound undertaking.
- `POST /api/compliance/undertakings/{id}/submit-evidence`: Submit compliance proof document (creates version, calculates SHA-256).
- `POST /api/compliance/undertakings/{id}/verify`: Verify or reject submitted evidence with official notes.

#### 2.4 Document Lifecycle & Renewals (`/api/documents`)
- `GET /api/documents`: List tracked statutory documents (Land Lease, Fire NOC, Building Plan).
- `POST /api/documents`: Register a new document record.
- `POST /api/documents/{id}/renew`: Submit renewal document version with new expiry date.
- `POST /api/documents/{id}/verify-version/{version_id}`: AICTE Officer verification sign-off.
- `GET /api/documents/download/{version_id}`: Safe download endpoint serving authorized document streams.

#### 2.5 EVC Management (`/api/evc`)
- `GET /api/evc/queue`: List applications pending inspection scheduling or inspection reports.
- `POST /api/evc/schedule`: Form panel (convener, expert), set inspection date, mode (`PHYSICAL_ONSITE` / `VIRTUAL_REMOTE`).
- `POST /api/evc/{id}/submit-report`: Upload signed committee inspection findings and recommendation.

#### 2.6 Alerts, Deadlines & Escalations (`/api/alerts`)
- `GET /api/alerts`: List notifications and active escalations for the current user/tenant.
- `POST /api/alerts/run-scan`: Trigger idempotent deadline and escalation evaluation pass.
- `POST /api/alerts/{id}/acknowledge`: Mark escalation acknowledged by an officer.

#### 2.7 Rule Studio & Audit Trail (`/api/rules`, `/api/audit`, `/api/reports`)
- `GET /api/rules`: List configurable workflow templates and SLA thresholds.
- `POST /api/rules`: Create or update a versioned rule set.
- `GET /api/audit`: Query append-only audit trail with entity and actor filters.
- `GET /api/reports/summary`: Aggregate operational metrics (stage distribution, pendency ageing, compliance rates).
- `GET /api/health`: Health status endpoint returning database connection status and server timestamp.
