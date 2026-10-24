# Limitations, Assumptions & Prototype Boundaries — ReguFlow 360
## Regulatory Integrity & Engineering Disclaimers
**SIH 2026 Problem Statement 26262**  
**Version:** 1.0.0

---

### 1. Regulatory Status & Illustrative Rules
- **Illustrative Demo Norms**: The workflow stages, deficiency categories, SLA durations (e.g. 7-day scrutiny, 15-day cure window), and escalation intervals implemented in this prototype are illustrative demonstrations inspired by the AICTE Approval Process Handbook (APH). They must not be interpreted as legally binding statutory regulations.
- **Configurable Rule Studio**: In a production deployment, all workflow paths and SLA deadlines must be validated and gazetted by authorized AICTE regulatory committees before activation.

---

### 2. Technical Scope & Architecture Assumptions

#### 2.1 Storage & File Management
- In this prototype, submitted documents (PDFs, NOCs, Land Deeds) are saved securely in local persistent storage (`backend/uploads/`) with strict path sanitation, randomized file identifiers, and SHA-256 integrity checksums.
- In enterprise production, this storage module should interface directly with encrypted Cloud Object Storage (e.g. AWS S3 with Object Lock or Azure Blob Storage) with ClamAV/anti-malware scanning pipeline before acceptance.

#### 2.2 Notification Delivery Channels
- Real-time in-app notifications and durable escalation logs are fully implemented and stored in the database.
- External SMS (e.g. CDAC/NIC SMS gateway) and SMTP email dispatches are simulated with structured event logging to ensure that lack of third-party SMS/email API credentials does not impede local execution.

#### 2.3 AI Case Brief Assistant & Fallback Mode
- The system includes a deterministic Case Brief synthesis engine that summarizes application milestones, resolved deficiencies, and verified evidence without requiring external paid LLM APIs.
- When an optional LLM API key (e.g. Google Gemini / OpenAI) is configured, the assistant provides natural language case syntheses with explicit citations to source records. If unconfigured, the deterministic case summary operates seamlessly.
- **Strict Guardrail**: The AI assistant has zero decision-making authority. It cannot alter stage transitions, approve applications, or bypass compliance requirements.

#### 2.4 Authentication & Secrets
- Passwords in development seed data (`Password123!`) are provided strictly for demonstration and testing purposes.
- In production, authentication should integrate with Government of India Single Sign-On (Parichay / MeriPehchaan) and multi-factor authentication (MFA/TOTP).
