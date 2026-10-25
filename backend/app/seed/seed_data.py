import json
from datetime import datetime, date, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.institution import Institution
from app.models.user import User, UserRole
from app.models.application import Application, ApplicationStage, Deficiency
from app.models.compliance import ComplianceUndertaking, ComplianceEvidence
from app.models.document import DocumentRecord, DocumentVersion
from app.models.evc import EVCInspection
from app.models.alert import Notification, AlertEscalation
from app.models.audit import AuditEvent
from app.models.rule import RuleDefinition
from app.services.deadline_service import generate_idempotency_key

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Institution).count() > 0:
            print("Database already seeded. Skipping initial seeding.")
            return

        print("Seeding ReguFlow 360 database with synthetic regulatory records...")

        now = datetime.now(timezone.utc)
        today = date.today()

        # 1. Institutions
        inst1 = Institution(
            code="1-3324901",
            name="Apex Institute of Technology & Management",
            category="ENGINEERING_AND_TECHNOLOGY",
            state="Maharashtra",
            region="Western",
            address="Plot 44, Knowledge City, Bandra Kurla Complex, Mumbai - 400051",
            contact_email="admin@apex.edu.in",
            contact_phone="+91-22-26543210"
        )
        inst2 = Institution(
            code="1-7782104",
            name="Northern Institute of Engineering & Research",
            category="ENGINEERING_AND_TECHNOLOGY",
            state="Delhi",
            region="Northern",
            address="Sector 12, Institutional Area, Rohini, New Delhi - 110085",
            contact_email="admin@nier.edu.in",
            contact_phone="+91-11-27891234"
        )
        db.add_all([inst1, inst2])
        db.flush()

        # 2. Users
        default_pwd = get_password_hash("Password123!")
        
        users_data = [
            ("admin@apex.edu.in", "Dr. Arvind Kulkarni", inst1.id, None, ["INSTITUTION_ADMIN"]),
            ("compliance@apex.edu.in", "Prof. Sneha Patil", inst1.id, None, ["COMPLIANCE_OFFICER"]),
            ("admin@nier.edu.in", "Dr. Harpreet Singh", inst2.id, None, ["INSTITUTION_ADMIN"]),
            ("ro.western@aicte.gov.in", "Shri Suresh Deshmukh", None, "Western", ["REGIONAL_OFFICER"]),
            ("evc.coord@aicte.gov.in", "Dr. Vikram Sethi", None, "Western", ["EVC_COORDINATOR"]),
            ("bo.approval@aicte.gov.in", "Dr. Meenakshi Raman", None, "National", ["BUREAU_OFFICER"]),
            ("committee.member@aicte.gov.in", "Prof. R. C. Mathur", None, "National", ["COMMITTEE_MEMBER"]),
            ("member.sec@aicte.gov.in", "Dr. K. Balasubramanian", None, "National", ["COMPETENT_AUTHORITY"]),
            ("sysadmin@aicte.gov.in", "System Administrator", None, "National", ["SYSTEM_ADMIN"]),
        ]

        created_users = {}
        for email, name, inst_id, region, roles in users_data:
            u = User(
                email=email,
                hashed_password=default_pwd,
                full_name=name,
                institution_id=inst_id,
                region=region,
                is_active=True
            )
            db.add(u)
            db.flush()
            for r in roles:
                ur = UserRole(user_id=u.id, role=r)
                db.add(ur)
            created_users[email] = u

        db.flush()

        # 3. Applications
        # App 1: Apex EOA with Deficiency
        app1 = Application(
            application_number="AICTE-2026-EOA-98124",
            institution_id=inst1.id,
            academic_year="2026-2027",
            application_type="EOA_ANNUAL",
            workflow_template_code="EOA_ANNUAL",
            current_stage="DEFICIENCY_COMMUNICATED",
            priority_score=75,
            submitted_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=4)
        )
        # App 2: Apex New Program awaiting EVC
        app2 = Application(
            application_number="AICTE-2026-NEW-44102",
            institution_id=inst1.id,
            academic_year="2026-2027",
            application_type="NEW_INSTITUTION",
            workflow_template_code="NEW_INSTITUTION",
            current_stage="AWAITING_EVC_SCHEDULE",
            evc_required=True,
            priority_score=60,
            submitted_at=now - timedelta(days=22),
            updated_at=now - timedelta(days=2)
        )
        # App 3: Northern EOA Under Scrutiny
        app3 = Application(
            application_number="AICTE-2026-EOA-55910",
            institution_id=inst2.id,
            academic_year="2026-2027",
            application_type="EOA_ANNUAL",
            workflow_template_code="EOA_ANNUAL",
            current_stage="UNDER_SCRUTINY",
            priority_score=40,
            submitted_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=3)
        )
        # App 4: Northern Intake Variation Approved
        app4 = Application(
            application_number="AICTE-2026-INT-11209",
            institution_id=inst2.id,
            academic_year="2026-2027",
            application_type="INTAKE_VARIATION",
            workflow_template_code="INTAKE_VARIATION",
            current_stage="APPROVED",
            priority_score=15,
            submitted_at=now - timedelta(days=35),
            approved_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5)
        )
        db.add_all([app1, app2, app3, app4])
        db.flush()

        # 4. Timeline Stages for App 1
        s1 = ApplicationStage(
            application_id=app1.id,
            from_stage="DRAFT",
            to_stage="SUBMITTED",
            actor_id=created_users["admin@apex.edu.in"].id,
            actor_role="INSTITUTION_ADMIN",
            actor_name="Dr. Arvind Kulkarni",
            remarks="Annual Extension of Approval application filed with prescribed fees.",
            created_at=now - timedelta(days=18)
        )
        s2 = ApplicationStage(
            application_id=app1.id,
            from_stage="SUBMITTED",
            to_stage="UNDER_SCRUTINY",
            actor_id=created_users["ro.western@aicte.gov.in"].id,
            actor_role="REGIONAL_OFFICER",
            actor_name="Shri Suresh Deshmukh",
            remarks="Scrutiny commenced for infrastructure norms and faculty cadre compliance.",
            created_at=now - timedelta(days=12)
        )
        s3 = ApplicationStage(
            application_id=app1.id,
            from_stage="UNDER_SCRUTINY",
            to_stage="DEFICIENCY_COMMUNICATED",
            actor_id=created_users["ro.western@aicte.gov.in"].id,
            actor_role="REGIONAL_OFFICER",
            actor_name="Shri Suresh Deshmukh",
            remarks="Deficiency memo issued regarding municipal fire stamp and computer engineering cadre ratio.",
            created_at=now - timedelta(days=4)
        )
        db.add_all([s1, s2, s3])

        # 5. Deficiencies for App 1
        d1 = Deficiency(
            application_id=app1.id,
            category="INFRASTRUCTURE",
            description="Updated Form B Fire Safety NOC missing municipal fire brigade seal and date.",
            required_document="Fire_Safety_NOC_Updated.pdf",
            status="OPEN",
            created_at=now - timedelta(days=4)
        )
        d2 = Deficiency(
            application_id=app1.id,
            category="FACULTY_CADRE",
            description="Cadre ratio in Computer Engineering is 1:2.4 instead of required 1:2.0 norm.",
            required_document="Cadre_Ratio_Rectification_Affidavit.pdf",
            status="OPEN",
            created_at=now - timedelta(days=4)
        )
        db.add_all([d1, d2])

        # 6. Compliance Undertakings
        u1 = ComplianceUndertaking(
            institution_id=inst1.id,
            application_id=app1.id,
            title="Establishment of Barrier-Free Access Ramps & Dedicated Elevator",
            category="ACCESSIBILITY",
            description="Mandatory accessibility compliance as per Divyangjan norms across academic blocks.",
            due_date=now + timedelta(days=12),
            rule_code="APH-2026-CH2-RAMP",
            evidence_type="ARCHITECTURAL_AFFIDAVIT",
            status="DUE_SOON",
            created_at=now - timedelta(days=45)
        )
        u2 = ComplianceUndertaking(
            institution_id=inst1.id,
            application_id=app1.id,
            title="Installation of Specialized Robotics & Green Tech Laboratory Equipment",
            category="INFRASTRUCTURE",
            description="Commissioning of 15 advanced robotics testing workstations.",
            due_date=now - timedelta(days=5),
            rule_code="APH-2026-CH4-ROBOTICS",
            evidence_type="PROCUREMENT_INVOICE",
            status="OVERDUE",
            created_at=now - timedelta(days=60)
        )
        u3 = ComplianceUndertaking(
            institution_id=inst2.id,
            application_id=app3.id,
            title="Submission of Annual Financial Audit & Fee Regulatory Committee Conformity",
            category="FINANCIAL_AUDIT",
            description="Submission of statutory audited balance sheet for FY 2025-2026.",
            due_date=now + timedelta(days=45),
            rule_code="APH-2026-CH6-FINANCIAL",
            evidence_type="AUDITED_BALANCE_SHEET",
            status="NOT_YET_DUE",
            created_at=now - timedelta(days=20)
        )
        u4 = ComplianceUndertaking(
            institution_id=inst2.id,
            application_id=app4.id,
            title="Faculty Biometric & AI-Assisted Attendance Integration",
            category="FACULTY",
            description="Direct API integration with state regulatory monitoring dashboard.",
            due_date=now - timedelta(days=30),
            rule_code="APH-2026-CH3-BIOMETRIC",
            evidence_type="INTEGRATION_CERTIFICATE",
            status="VERIFIED",
            fulfilled_at=now - timedelta(days=10),
            verified_at=now - timedelta(days=10),
            verified_by_id=created_users["ro.western@aicte.gov.in"].id,
            created_at=now - timedelta(days=90)
        )
        db.add_all([u1, u2, u3, u4])
        db.flush()

        # Evidence for verified undertaking
        ev4 = ComplianceEvidence(
            undertaking_id=u4.id,
            version=1,
            file_name="Biometric_Integration_Certificate_NIER.pdf",
            file_url="/api/documents/download/sample_biometric_cert.pdf",
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            remarks="API integration verified and tested with AICTE regional node.",
            submitted_by_id=created_users["admin@nier.edu.in"].id,
            submitted_at=now - timedelta(days=12),
            verification_status="VERIFIED",
            verified_by_id=created_users["ro.western@aicte.gov.in"].id,
            verified_at=now - timedelta(days=10),
            verification_notes="API handshake verified with regional node."
        )
        db.add(ev4)

        # 7. Document Records & Versions
        doc1 = DocumentRecord(
            institution_id=inst1.id,
            application_id=app1.id,
            document_type="LAND_LEASE_DEED",
            title="33-Year Registered Land Lease Deed (Khasra No. 412/1)",
            document_number="REG-MH-2021-99812",
            issuing_authority="Sub-Registrar Pune",
            issue_date=today - timedelta(days=365 * 32 + 320),
            valid_from=today - timedelta(days=365 * 33),
            expiry_date=today + timedelta(days=45), # Expiring in 45 days
            renewal_required=True,
            status="EXPIRING_SOON",
            current_version=1,
            created_at=now - timedelta(days=120)
        )
        doc2 = DocumentRecord(
            institution_id=inst1.id,
            application_id=app1.id,
            document_type="FIRE_SAFETY_NOC",
            title="Municipal Fire Brigade Safety NOC (Form B)",
            document_number="FIRE-MUM-2025-0192",
            issuing_authority="Municipal Fire Brigade",
            issue_date=today - timedelta(days=375),
            valid_from=today - timedelta(days=375),
            expiry_date=today - timedelta(days=10), # Expired 10 days ago
            renewal_required=True,
            status="EXPIRED",
            current_version=1,
            created_at=now - timedelta(days=120)
        )
        doc3 = DocumentRecord(
            institution_id=inst2.id,
            application_id=app3.id,
            document_type="BUILDING_STABILITY",
            title="Structural Stability & Occupancy Certificate",
            document_number="PWD-DL-2023-4419",
            issuing_authority="Central PWD Delhi",
            issue_date=today - timedelta(days=700),
            valid_from=today - timedelta(days=700),
            expiry_date=today + timedelta(days=365 * 10),
            renewal_required=False,
            status="ACTIVE",
            current_version=1,
            created_at=now - timedelta(days=200)
        )
        db.add_all([doc1, doc2, doc3])
        db.flush()

        v1 = DocumentVersion(
            document_record_id=doc1.id,
            version=1,
            file_name="Apex_Land_Lease_Deed_Registered.pdf",
            file_url="/api/documents/download/sample_land_lease.pdf",
            storage_key="sample_land_lease.pdf",
            file_size=1048576,
            mime_type="application/pdf",
            checksum_sha256="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            uploaded_by_id=created_users["admin@apex.edu.in"].id,
            uploaded_at=now - timedelta(days=120),
            verification_status="VERIFIED",
            verified_by_id=created_users["ro.western@aicte.gov.in"].id,
            verified_at=now - timedelta(days=110),
            verification_notes="Initial 33-year deed verified during 2021 regulatory cycle."
        )
        v2 = DocumentVersion(
            document_record_id=doc2.id,
            version=1,
            file_name="Apex_Fire_NOC_2025.pdf",
            file_url="/api/documents/download/sample_fire_noc.pdf",
            storage_key="sample_fire_noc.pdf",
            file_size=524288,
            mime_type="application/pdf",
            checksum_sha256="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            uploaded_by_id=created_users["admin@apex.edu.in"].id,
            uploaded_at=now - timedelta(days=120),
            verification_status="REJECTED",
            verified_by_id=created_users["ro.western@aicte.gov.in"].id,
            verified_at=now - timedelta(days=4),
            verification_notes="Form B missing municipal seal. Renewal required."
        )
        db.add_all([v1, v2])

        # 8. EVC Inspection for App 2
        evc1 = EVCInspection(
            application_id=app2.id,
            inspection_type="PHYSICAL_ONSITE",
            scheduled_date=None,
            convener_name=None,
            expert_member_name=None,
            coordinator_id=created_users["evc.coord@aicte.gov.in"].id,
            status="PENDING_ASSIGNMENT",
            created_at=now - timedelta(days=2)
        )
        db.add(evc1)

        # 9. Rule Studio Definitions
        rules = [
            RuleDefinition(
                rule_code="RULE_SCRUTINY_SLA",
                name="Application Scrutiny SLA Window",
                category="DEADLINE",
                version="1.0.0",
                config_json=json.dumps({"sla_days": 7, "escalation_target": "REGIONAL_OFFICER", "is_illustrative_demo": True})
            ),
            RuleDefinition(
                rule_code="RULE_DEFICIENCY_CURE",
                name="Deficiency Cure & Resubmission Window",
                category="DEADLINE",
                version="1.0.0",
                config_json=json.dumps({"cure_window_days": 15, "grace_period_days": 3, "escalation_target": "BUREAU_OFFICER", "is_illustrative_demo": True})
            ),
            RuleDefinition(
                rule_code="RULE_EVC_SCHEDULE",
                name="EVC Panel Scheduling SLA",
                category="DEADLINE",
                version="1.0.0",
                config_json=json.dumps({"max_scheduling_days": 10, "min_panel_size": 2, "is_illustrative_demo": True})
            ),
            RuleDefinition(
                rule_code="RULE_LEASE_EXPIRY_ALERT",
                name="Land Lease & Document Expiry Notification Thresholds",
                category="COMPLIANCE",
                version="1.0.0",
                config_json=json.dumps({"warning_threshold_days": [60, 30, 15, 7], "is_illustrative_demo": True})
            ),
        ]
        db.add_all(rules)

        # 10. Initial Escalations and Notifications
        esc_key = generate_idempotency_key("UNDERTAKING", u2.id, "SLA_OVERDUE", 5, "ESCALATION_L1_RO", "REGIONAL_OFFICER")
        esc1 = AlertEscalation(
            idempotency_key=esc_key,
            entity_type="UNDERTAKING",
            entity_id=u2.id,
            trigger_type="SLA_OVERDUE",
            threshold_days=5,
            escalation_level="ESCALATION_L1_RO",
            recipient_role="REGIONAL_OFFICER",
            status="ACTIVE",
            created_at=now - timedelta(days=2)
        )
        db.add(esc1)

        n1 = Notification(
            institution_id=inst1.id,
            title="CRITICAL: Deficiency Memo Issued for AICTE-2026-EOA-98124",
            message="Regional Officer has communicated 2 deficiency items. Statutory cure deadline active.",
            level="DANGER",
            link_url=f"/applications/{app1.id}",
            created_at=now - timedelta(days=4)
        )
        n2 = Notification(
            institution_id=inst1.id,
            title="Renewal Warning: 33-Year Land Lease Deed Expiring Soon",
            message="Land lease deed expires in 45 days. Please initiate renewal or sub-lease extension.",
            level="WARNING",
            link_url="/documents",
            created_at=now - timedelta(days=5)
        )
        db.add_all([n1, n2])

        # 11. Initial Audit Logs
        a1 = AuditEvent(
            actor_id=created_users["sysadmin@aicte.gov.in"].id,
            actor_name="System Administrator",
            actor_role="SYSTEM_ADMIN",
            action="SYSTEM_INITIALIZED",
            entity_type="SYSTEM",
            entity_id=0,
            details=json.dumps({"academic_cycle": "2026-2027", "platform": "ReguFlow 360", "environment": "Demonstration"}),
            created_at=now - timedelta(days=30)
        )
        db.add(a1)

        db.commit()
        print("Database successfully seeded with comprehensive demo records.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
