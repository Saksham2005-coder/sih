# Limitations, Assumptions & Prototype Boundaries — ReguFlow 360
## Regulatory Integrity & Engineering Disclaimers
**SIH 2026 Problem Statement 26262**  
**Version:** 4.0.0 (Remediation 3 Production-Safety Hardened & Release Integrity Verified)

---

### 1. Regulatory Status & Illustrative Rules
- **Illustrative Demo Norms**: The workflow stages, deficiency categories, SLA durations (e.g. 7-day scrutiny, 15-day cure window), and escalation intervals implemented in this prototype are illustrative demonstrations inspired by the AICTE Approval Process Handbook (APH). They must not be interpreted as legally binding statutory regulations.
- **Configurable Rule Studio**: In a production deployment, all workflow paths and SLA deadlines must be validated and gazetted by authorized AICTE regulatory committees before activation.

---

### 2. Technical Scope & Architecture Assumptions

#### 2.1 Storage & File Management
- In this prototype, submitted documents (PDFs, NOCs, Land Deeds) are saved securely in local persistent storage (`backend/uploads/`) with strict path sanitation, randomized file identifiers, authenticated stream endpoints (`GET /api/documents/download/{filename}`), and SHA-256 integrity checksums.
- In enterprise production, this storage module should interface directly with encrypted Cloud Object Storage (e.g. AWS S3 with Object Lock or Azure Blob Storage) with ClamAV/anti-malware scanning pipeline before acceptance.

#### 2.2 Transactional Outbox, Reliable Delivery & Notification Boundaries
- **Transactional Outbox Persistence**: All notification dispatch intents are atomically enqueued inside the originating business database transaction into `notification_outbox`. This guarantees zero lost notifications between application commits and external dispatch workers.
- **Provider Evidence Distinction**: 
  - Successful SMTP transmission marks the outbox record as `ACCEPTED_BY_PROVIDER` (not falsely `DELIVERED`), acknowledging that an SMTP server response (status 250) confirms acceptance by the MTA relay, not confirmed delivery to a human recipient's inbox.
  - When SMTP credentials (`SMTP_HOST`, `SMTP_PORT`) are not configured, dispatches are explicitly marked `NOT_CONFIGURED` rather than feigning successful delivery.
  - The SMS Provider is engineered as an adapter boundary for future CDAC / NIC AICTE SMS Gateway integration. Until an official gateway URL and API credentials are provided, outbox records are transparently marked `SIMULATED` in development or `NOT_CONFIGURED` in production. Live carrier delivery is never falsely asserted.
- **Retry with Bounded Exponential Backoff**: The outbox worker retries transient failures with exponential backoff (e.g. 60s, 120s, 240s, 480s) up to 4 attempts before transitioning to `DEAD_LETTER`. Authorized administrators can review failure causes and initiate manual retries via `POST /api/notifications/outbox/{id}/retry`.
- **Real-Time Server-Sent Events (SSE)**: Authenticated SSE stream (`/api/notifications/stream`) delivers live operational summaries to subscribed browsers with 15-second heartbeat (`: ping`) keep-alives and strict user/tenant/regional scoping. If SSE connections drop or are blocked by enterprise firewalls, the frontend seamlessly degrades to interval polling (`/api/notifications/unread-count`).
- **Autonomous Scheduling & Zero Duplicates**: The background scheduler executes repeated deadline and outbox dispatch cycles. Scans use database-level idempotency keys (`OUTBOX:{entity_type}:{entity_id}:{channel}:{event_type}...`) ensuring zero duplicate alerts or redundant dispatches on repeat scans.

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

#### 2.9 Production-Safety Deployment Hardening & Fail-Closed Invariants
- **Fail-Closed Startup**: In production mode (`ENVIRONMENT=production`), the backend validates that `SECRET_KEY` is present, at least 32 characters, and does not match any development default or pattern. Startup refuses to initialize if `DEBUG=True`, `DEMO_MODE=True`, or if `DATABASE_URL` is SQLite or contains development passwords. Validation error messages never print or leak secret keys.
- **Zero Demo Seeding**: Automatic database seeding of synthetic accounts and test applications is strictly forbidden in production. Calling `seed_database()` in production raises an immediate runtime error.
- **Network Isolation**: The development Docker Compose setup binds PostgreSQL strictly to loopback `127.0.0.1:5432:5432` to prevent unintended host LAN/WAN exposure. The dedicated `docker-compose.prod.yml` configuration completely omits published database ports.

#### 2.10 Workflow Route Invariants & Statutory Decision Safeguard
- **Only Scrutiny Route**: Applications under the "Only Scrutiny" route (such as routine Extension of Approval renewals) bypass EVC inspection because physical inspection is not prescribed. Upon scrutiny sign-off (`SCRUTINY_COMPLETED`), the application advances directly to `AWAITING_COMPETENT_AUTHORITY`.
- **Preservation of Explicit Human Decision**: Bypassing EVC does **NOT** grant automatic statutory approval. Final statutory approval or rejection strictly requires an explicit, recorded decision by the Competent Authority (`member.sec@aicte.gov.in`). No scheduler, report generator, AI summary, or officer can bypass this final statutory requirement.

#### 2.11 Statutory Decision Order Generation & Digital Signature Provider Boundary
- **Persisted Regulatory Dossier**: Generated decision documents are rooted strictly in persisted database records (`StatutoryOrder` entity in `statutory_orders` table). The generator cannot invent statutory clauses, conditions, reference numbers, or CA remarks.
- **Explicit Digital Signature State**: The platform does not fabricate fake PKI certificates or simulate legally binding cryptographic signatures without authorized credentials. Generated decision documents are explicitly classified as `UNSIGNED_PROTOTYPE` with transparent UI and document disclosures.
- **Integration Boundary for Authorized Signing Providers**: Under Section 10 of the AICTE Act and the Information Technology Act, 2000, official legally binding statutory orders require signing via a licensed Certifying Authority (CCA) e-Sign provider (e.g., eMudhra, CDAC, NSDL) or Class-3 Hardware Security Module (HSM) tokens. An abstract `DigitalSignatureProvider` interface defines this boundary (`sign_document`, `verify_signature`). The system transitions from `UNSIGNED_PROTOTYPE` to `SIGNED_BY_CONFIGURED_PROVIDER` only when real credentials and active signing gateways are provisioned.
- **Cryptographic Provenance vs. Legal Signature**: Embedded QR codes point to a public-safe verification endpoint (`/api/orders/verify/{token}`) that confirms artifact provenance against the registered SHA-256 database digest. The QR code serves as an instant reference integrity check and does not substitute for a statutory digital signature.



