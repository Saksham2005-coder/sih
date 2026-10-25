# Limitations, Assumptions & Prototype Boundaries — ReguFlow 360
## Regulatory Integrity & Engineering Disclaimers
**SIH 2026 Problem Statement 26262**  
**Version:** 3.0.0 (Phase 4 Hardened)

---

### 1. Regulatory Status & Illustrative Rules
- **Illustrative Demo Norms**: The workflow stages, deficiency categories, SLA durations (e.g. 7-day scrutiny, 15-day cure window), and escalation intervals implemented in this prototype are illustrative demonstrations inspired by the AICTE Approval Process Handbook (APH). They must not be interpreted as legally binding statutory regulations.
- **Configurable Rule Studio**: In a production deployment, all workflow paths and SLA deadlines must be validated and gazetted by authorized AICTE regulatory committees before activation.

---

### 2. Technical Scope & Architecture Assumptions

#### 2.1 Storage & File Management
- In this prototype, submitted documents (PDFs, NOCs, Land Deeds) are saved securely in local persistent storage (`backend/uploads/`) with strict path sanitation, randomized file identifiers, authenticated stream endpoints (`GET /api/documents/download/{filename}`), and SHA-256 integrity checksums.
- In enterprise production, this storage module should interface directly with encrypted Cloud Object Storage (e.g. AWS S3 with Object Lock or Azure Blob Storage) with ClamAV/anti-malware scanning pipeline before acceptance.

#### 2.2 Notification Delivery Channels & Idempotent Escalations
- **Core In-App Persistence**: All in-app notifications and multi-tier escalations are authoritative, durable records stored directly in the database (`notifications` and `alert_escalations` tables). They do not rely on transient caches or active browser sessions.
- **Simulated External Delivery**: External SMS (e.g. CDAC/NIC SMS gateway) and SMTP email channels are designed with clean outbox/adapter interfaces (`delivery_channel="EMAIL"` or `"SMS"`, `delivery_status="SIMULATED"`). In the local prototype environment, external dispatches log structured simulation payloads without faking live transmission receipts. In production, these adapters can be swapped for real gateway SDKs without changing the underlying domain models or database transactions.
- **Autonomous Scheduling**: The background scheduler runs as an uncoupled singleton process in FastAPI lifespan, ensuring scans occur repeatedly even when no user or browser is connected. On-demand scans share the identical execution engine and cycle-aware idempotency keys.

#### 2.3 AI Case Brief Assistant & Fallback Mode
- The system includes a deterministic Case Brief synthesis engine that summarizes application milestones, resolved deficiencies, and verified evidence without requiring external paid LLM APIs.
- When an optional LLM API key (e.g. Google Gemini / OpenAI) is configured, the assistant provides natural language case syntheses with explicit citations to source records. If unconfigured, the deterministic case summary operates seamlessly.
- **Strict Guardrail**: The AI assistant has zero decision-making authority. It cannot alter stage transitions, approve applications, or bypass compliance requirements.

#### 2.4 Authentication, Session Management & Secrets
- Passwords in development seed data (`Password123!`) are provided strictly for demonstration and testing purposes.
- In production, authentication should integrate with Government of India Single Sign-On (Parichay / MeriPehchaan) and multi-factor authentication (MFA/TOTP).
- **Session Revocation**: JWT tokens carry a unique `jti` claim. Calling `POST /api/auth/logout` places the `jti` in the `revoked_tokens` table. In multi-instance production clusters, this table can be mirrored in an in-memory Redis cluster for sub-millisecond lookup latency.
#### 2.5 Document Integrity vs. Statutory Legal Authenticity
- A computed SHA-256 checksum provides bit-level tamper-evidence for stored bytes; it does not legally attest that a document is genuine, authentic, or verified by an issuing municipal or state authority. Verification sign-off by an authorized AICTE official remains a mandatory, non-automatable requirement.
- Multi-year documents (such as 33-year land deeds or building approvals) support continuous or non-expiring validity profiles without artificial expiration enforcement.
- A rejected document renewal retains historical archived versions and maintains the existing recorded validity date without silently extending expiration.
- Document and compliance uploads in this prototype enforce maximum file size (10MB), permitted extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`), and magic-byte header validation. In enterprise production, this must be augmented with an automated anti-malware and antivirus sandbox scan (e.g. ClamAV).

#### 2.6 Multi-Worker Background Scheduler Coordination (`SchedulerLease`)
- In multi-worker or multi-process Uvicorn deployments, multiple application instances could potentially attempt concurrent background deadline scans.
- In Phase 5, this is coordinated safely via distributed database leases (`scheduler_leases` table). An active worker acquires a lease for a designated duration (e.g. 120s) and maintains it via periodic heartbeats. Other workers skip duplicate execution when an active lease is held.
- For high-availability multi-region enterprise clusters, this database lease can be augmented with dedicated Kubernetes CronJob workers or a Redis distributed lock (Redlock).

#### 2.7 Deadline Calculation Boundaries & Timezones
- Deadlines with date-only granularity (e.g. statutory document expiry dates or annual compliance cycles) are evaluated against calendar day transitions in the `Asia/Kolkata` (IST) timezone (`now.astimezone(IST).date()`).
- Naive conversion of calendar dates to UTC midnight can cause false premature expiration at 00:00 UTC (05:30 IST). ReguFlow 360 explicitly differentiates calendar dates from timestamp datetimes to guarantee accurate day-boundary transitions.

#### 2.8 Explainable Priority Scores vs Statutory Regulatory Decisions
- The Explainable Priority score (0–100) is an operational triage tool designed to help human officers navigate heavy application queues.
- **Strict Regulatory Invariant**: Operational scores do NOT constitute legal determinations, statutory non-compliance findings, or automatic approvals/rejections. All statutory decisions require explicit human action by authorized regulatory officials.


