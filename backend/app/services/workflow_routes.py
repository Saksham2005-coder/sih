from typing import Dict, List, Optional
from app.core.rbac import (
    REGIONAL_OFFICER,
    BUREAU_OFFICER,
    COMPETENT_AUTHORITY,
    SYSTEM_ADMIN,
    INSTITUTION_ADMIN,
    COMPLIANCE_OFFICER,
    COMMITTEE_MEMBER,
    EVC_COORDINATOR
)
from app.schemas.demo import (
    WorkflowRouteDefinition,
    WorkflowStageDefinition,
    WorkflowTransitionDefinition,
    NonApplicableStageDefinition
)

# Canonical Authoritative Route Definitions derived strictly from workflow engine state machine
AUTHORITATIVE_ROUTES: Dict[str, WorkflowRouteDefinition] = {
    "ONLY_SCRUTINY": WorkflowRouteDefinition(
        route_code="ONLY_SCRUTINY",
        route_name="Standard Scrutiny Route (Extension of Approval)",
        description="Streamlined regulatory route for annual extension of approval (EOA) renewals. Evaluates infrastructure, faculty cadre, and regulatory undertakings through documentary scrutiny without physical EVC inspection.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & Draft Preparation",
                description="Institution compiles compliance disclosures, financial audits, and mandatory affidavits.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Formal Submission Filed",
                description="Application lodged with prescribed fees, awaiting initial verification and scrutiny queue entry.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="UNDER_SCRUTINY",
                label="Document Scrutiny in Progress",
                description="Regional Officer verifies land title, faculty cadre ratios, building completion stamps, and NBA/NAAC accreditations.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="DEFICIENCY_COMMUNICATED",
                label="Deficiency Memo Communicated",
                description="Regional Officer issues formal deficiency memo detailing defects to cure.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=15
            ),
            WorkflowStageDefinition(
                stage_code="RESUBMITTED",
                label="Deficiency Cure Lodged",
                description="Institution submits rectification affidavits and supplementary proofs for re-scrutiny.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                label="Scrutiny Signed-Off",
                description="Documentary scrutiny concluded with zero unresolved open deficiencies.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Statutory Decision Docket",
                description="Referred to Member Secretary / Council for final statutory order review.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Statutory Approval Granted",
                description="Final statutory order issued with verifiable cryptographic watermark and public verification QR.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal speaking order issued citing specific regulatory non-compliances.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True, description="Deficiency Return Loop: Issued when documentary defects are detected."),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True, description="Institutional Cure Submission."),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True, description="Scrutiny Verification of Cured Items."),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="SCRUTINY_COMPLETED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="SCRUTINY_COMPLETED", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[
            NonApplicableStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                stage_label="EVC Inspection Scheduling",
                statutory_reason="Statutory Exemption: Physical on-site Expert Visit Committee inspection is not applicable for standard annual Extension of Approval (EOA) applications under AICTE Approval Process Handbook (APH) Chapter II, Section 2.4.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4 (EOA Norms)"
            ),
            NonApplicableStageDefinition(
                stage_code="EVC_SCHEDULED",
                stage_label="EVC Inspection Scheduled",
                statutory_reason="Bypassed: Physical on-site inspection is not prescribed for regular non-contested EOA renewal applications.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4"
            ),
            NonApplicableStageDefinition(
                stage_code="EVC_COMPLETED",
                stage_label="EVC Inspection Completed",
                statutory_reason="Bypassed: Physical on-site inspection is not prescribed for regular non-contested EOA renewal applications.",
                aph_rule_reference="AICTE APH 2026-27 Ch. II Sec. 2.4"
            ),
            NonApplicableStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                stage_label="Standing Hearing Committee Review",
                statutory_reason="Not Applicable: Standing Hearing Committee (SHC/SAC) review is only convened when an institution appeals a rejected deficiency cure or when major structural non-compliance is referred by the Bureau.",
                aph_rule_reference="AICTE APH 2026-27 Ch. VIII Sec. 8.2 (Hearing Committee)"
            )
        ]
    ),
    "SCRUTINY_EVC": WorkflowRouteDefinition(
        route_code="SCRUTINY_EVC",
        route_name="Scrutiny + Expert Visit Committee (New Technical Institution)",
        description="Comprehensive regulatory route for new technical institutions and significant program expansions. Enforces both rigorous documentary scrutiny and mandatory physical Expert Visit Committee (EVC) verification.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & DPR Compilation",
                description="Institution prepares Detailed Project Report (DPR), land conversion deeds, master plan, and trust deed.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Application Lodged",
                description="Submitted to Regional Office with security deposit and technical fees.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="UNDER_SCRUTINY",
                label="Scrutiny of Land & Structural Norms",
                description="Scrutiny committee verifies land contiguity, barrier-free access plans, structural safety, and financial viability.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="DEFICIENCY_COMMUNICATED",
                label="Deficiency Memo Issued",
                description="Regional Officer communicates documentary defects; institution must cure within prescribed SLA.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=15
            ),
            WorkflowStageDefinition(
                stage_code="RESUBMITTED",
                label="Deficiency Cure Lodged",
                description="Institution submits rectification affidavits and supplementary proofs for re-scrutiny.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                label="Scrutiny Recommendation Signed",
                description="Scrutiny committee clears documentary criteria and refers application for physical inspection.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                label="EVC Inspection Scheduling",
                description="EVC Coordination Directorate selects verified subject experts with zero conflict of interest and schedules on-site visit.",
                permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="EVC_SCHEDULED",
                label="EVC Panel Confirmed",
                description="Inspection date fixed, panel members accepted invitations, institution alerted for physical verification.",
                permitted_roles=[EVC_COORDINATOR],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="EVC_COMPLETED",
                label="Physical Inspection & Report Filed",
                description="Experts verify physical laboratories, computing facilities, faculty presence, and upload geotagged mobile evidence.",
                permitted_roles=[COMMITTEE_MEMBER, EVC_COORDINATOR],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Final Approval Docket",
                description="Full inspection dossier and unanimous recommendation submitted to Member Secretary / Council.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Letter of Approval (LoA) Issued",
                description="Statutory Letter of Approval granted with student intake quotas and program affiliations.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal order issued stating specific deficiencies and appellate remedies.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="SCRUTINY_COMPLETED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="SCRUTINY_COMPLETED", to_stage="AWAITING_EVC_SCHEDULE", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_EVC_SCHEDULE", to_stage="EVC_SCHEDULED", permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="EVC_SCHEDULED", to_stage="EVC_COMPLETED", permitted_roles=[EVC_COORDINATOR, COMMITTEE_MEMBER]),
            WorkflowTransitionDefinition(from_stage="EVC_COMPLETED", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[
            NonApplicableStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                stage_label="Standing Hearing Committee Review",
                statutory_reason="Not Applicable: Clear unanimous EVC approval recommendation advances directly to the Competent Authority without requiring a hearing review.",
                aph_rule_reference="AICTE APH 2026-27 Ch. I Sec. 1.7 (Approval Procedure)"
            )
        ]
    ),
    "EVC_SAC_SHC": WorkflowRouteDefinition(
        route_code="EVC_SAC_SHC",
        route_name="EVC + SAC/SHC Appellate Hearing Track (Contested / Major Expansion)",
        description="Comprehensive regulatory route incorporating documentary scrutiny, physical EVC inspection, and Standing Appellate / Hearing Committee (SAC/SHC) evaluation for complex intake variations or appealed deficiencies.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & Proposal Preparation",
                description="Institution prepares expansion proposal, infrastructure additions, and supporting affidavits.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Application Lodged",
                description="Application lodged with prescribed fee deposit and supporting dossiers.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="UNDER_SCRUTINY",
                label="Preliminary Scrutiny",
                description="Regional Officer verifies eligibility, documentary compliances, and NOCs.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="DEFICIENCY_COMMUNICATED",
                label="Deficiency Memo Communicated",
                description="Deficiencies communicated during scrutiny or hearing requiring institutional remedy.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMMITTEE_MEMBER],
                sla_days=15
            ),
            WorkflowStageDefinition(
                stage_code="RESUBMITTED",
                label="Deficiency Cure Lodged",
                description="Institution files rectification affidavits and supplementary proofs.",
                permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                label="Scrutiny Sign-Off",
                description="Preliminary scrutiny concluded; referred to physical inspection.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                label="EVC Inspection Scheduling",
                description="EVC Coordination Directorate selects verified subject experts and fixes visit date.",
                permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="EVC_SCHEDULED",
                label="EVC Panel Confirmed",
                description="Inspection panel accepted invitations, institution alerted for physical verification.",
                permitted_roles=[EVC_COORDINATOR],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="EVC_COMPLETED",
                label="Physical Inspection Concluded",
                description="Inspection report submitted; referred for Standing Hearing Committee (SAC/SHC) review.",
                permitted_roles=[EVC_COORDINATOR, COMMITTEE_MEMBER],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                label="Standing Hearing Committee Review",
                description="SAC/SHC conducts oral hearing, evaluates institutional representations, and deliberates on compliance.",
                permitted_roles=[COMMITTEE_MEMBER, BUREAU_OFFICER, REGIONAL_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Final Decision Docket",
                description="Referred to Member Secretary / Council following hearing recommendation.",
                permitted_roles=[COMMITTEE_MEMBER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Statutory Approval Granted",
                description="Final approval granted with approved intake quota and binding conditions.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal rejection order issued citing findings of the Standing Hearing Committee.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="UNDER_SCRUTINY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="UNDER_SCRUTINY", to_stage="SCRUTINY_COMPLETED", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="SCRUTINY_COMPLETED", to_stage="AWAITING_EVC_SCHEDULE", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_EVC_SCHEDULE", to_stage="EVC_SCHEDULED", permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="EVC_SCHEDULED", to_stage="EVC_COMPLETED", permitted_roles=[EVC_COORDINATOR, COMMITTEE_MEMBER]),
            WorkflowTransitionDefinition(from_stage="EVC_COMPLETED", to_stage="AWAITING_SAC_CAC_REVIEW", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_SAC_CAC_REVIEW", to_stage="DEFICIENCY_COMMUNICATED", permitted_roles=[COMMITTEE_MEMBER, BUREAU_OFFICER], is_return_loop=True, description="Hearing Deficiency Return: SAC/SHC committee notes hearing deficiencies requiring institution cure."),
            WorkflowTransitionDefinition(from_stage="DEFICIENCY_COMMUNICATED", to_stage="RESUBMITTED", permitted_roles=[INSTITUTION_ADMIN, COMPLIANCE_OFFICER], is_return_loop=True),
            WorkflowTransitionDefinition(from_stage="RESUBMITTED", to_stage="AWAITING_SAC_CAC_REVIEW", permitted_roles=[COMMITTEE_MEMBER, BUREAU_OFFICER], is_return_loop=True, description="Resumption of SAC Hearing review following institutional cure."),
            WorkflowTransitionDefinition(from_stage="AWAITING_SAC_CAC_REVIEW", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[COMMITTEE_MEMBER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[]
    ),
    "ONLY_EVC": WorkflowRouteDefinition(
        route_code="ONLY_EVC",
        route_name="Direct EVC Inspection Route (Special / Directed Verification)",
        description="Accelerated direct inspection track bypassing preliminary document scrutiny. Prescribed for directed infrastructure verification, sudden compliance inspections, or unannounced laboratory audits.",
        stages=[
            WorkflowStageDefinition(
                stage_code="DRAFT",
                label="Filing & Proposal Submission",
                description="Institution files special verification dossier or institutional closure request.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="SUBMITTED",
                label="Direct Submission Lodged",
                description="Application lodged, directly qualifying for accelerated EVC scheduling.",
                permitted_roles=[INSTITUTION_ADMIN],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_EVC_SCHEDULE",
                label="EVC Inspection Scheduling",
                description="Direct routing to EVC scheduling queue without intermediate desk scrutiny.",
                permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="EVC_SCHEDULED",
                label="EVC Panel Confirmed",
                description="Panel formed, conflict clearance verified, and physical inspection scheduled.",
                permitted_roles=[EVC_COORDINATOR],
                sla_days=7
            ),
            WorkflowStageDefinition(
                stage_code="EVC_COMPLETED",
                label="Physical Inspection & Report Filed",
                description="On-site verification completed with geotagged mobile evidence and inspection report.",
                permitted_roles=[COMMITTEE_MEMBER, EVC_COORDINATOR],
                sla_days=5
            ),
            WorkflowStageDefinition(
                stage_code="AWAITING_COMPETENT_AUTHORITY",
                label="Statutory Decision Docket",
                description="Referred directly to Competent Authority on basis of completed EVC report.",
                permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER, COMPETENT_AUTHORITY],
                sla_days=10
            ),
            WorkflowStageDefinition(
                stage_code="APPROVED",
                label="Statutory Approval Granted",
                description="Final statutory order issued following successful direct inspection.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            ),
            WorkflowStageDefinition(
                stage_code="REJECTED",
                label="Statutory Rejection Order",
                description="Formal order issued stating specific deficiencies noted during inspection.",
                permitted_roles=[COMPETENT_AUTHORITY],
                is_terminal=True,
                sla_days=0
            )
        ],
        transitions=[
            WorkflowTransitionDefinition(from_stage="DRAFT", to_stage="SUBMITTED", permitted_roles=[INSTITUTION_ADMIN]),
            WorkflowTransitionDefinition(from_stage="SUBMITTED", to_stage="AWAITING_EVC_SCHEDULE", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_EVC_SCHEDULE", to_stage="EVC_SCHEDULED", permitted_roles=[EVC_COORDINATOR, REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="EVC_SCHEDULED", to_stage="EVC_COMPLETED", permitted_roles=[EVC_COORDINATOR, COMMITTEE_MEMBER]),
            WorkflowTransitionDefinition(from_stage="EVC_COMPLETED", to_stage="AWAITING_COMPETENT_AUTHORITY", permitted_roles=[REGIONAL_OFFICER, BUREAU_OFFICER]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="APPROVED", permitted_roles=[COMPETENT_AUTHORITY]),
            WorkflowTransitionDefinition(from_stage="AWAITING_COMPETENT_AUTHORITY", to_stage="REJECTED", permitted_roles=[COMPETENT_AUTHORITY])
        ],
        non_applicable_stages=[
            NonApplicableStageDefinition(
                stage_code="UNDER_SCRUTINY",
                stage_label="Document Scrutiny",
                statutory_reason="Bypassed: Special direct EVC route executes physical verification on-site without prior regional desk scrutiny.",
                aph_rule_reference="AICTE APH 2026-27 Ch. V Sec. 5.1 (Direct Inspection Track)"
            ),
            NonApplicableStageDefinition(
                stage_code="SCRUTINY_COMPLETED",
                stage_label="Scrutiny Completed",
                statutory_reason="Bypassed: Direct EVC track does not require desk scrutiny sign-off.",
                aph_rule_reference="AICTE APH 2026-27 Ch. V Sec. 5.1"
            ),
            NonApplicableStageDefinition(
                stage_code="AWAITING_SAC_CAC_REVIEW",
                stage_label="Standing Hearing Committee Review",
                statutory_reason="Not Applicable: Direct EVC report forwards directly to Competent Authority docket.",
                aph_rule_reference="AICTE APH 2026-27 Ch. I Sec. 1.7"
            )
        ]
    )
}

# Canonical Route Aliases for legacy and alternative application type codes
AUTHORITATIVE_ROUTES["EOA_ANNUAL"] = AUTHORITATIVE_ROUTES["ONLY_SCRUTINY"]
AUTHORITATIVE_ROUTES["NEW_INSTITUTION"] = AUTHORITATIVE_ROUTES["SCRUTINY_EVC"]
AUTHORITATIVE_ROUTES["INTAKE_VARIATION"] = AUTHORITATIVE_ROUTES["EVC_SAC_SHC"]
AUTHORITATIVE_ROUTES["CLOSURE_PROGRAM"] = AUTHORITATIVE_ROUTES["ONLY_EVC"]

def get_canonical_routes_registry() -> Dict[str, WorkflowRouteDefinition]:
    """Returns the four authoritative canonical routes."""
    return {
        "ONLY_SCRUTINY": AUTHORITATIVE_ROUTES["ONLY_SCRUTINY"],
        "SCRUTINY_EVC": AUTHORITATIVE_ROUTES["SCRUTINY_EVC"],
        "EVC_SAC_SHC": AUTHORITATIVE_ROUTES["EVC_SAC_SHC"],
        "ONLY_EVC": AUTHORITATIVE_ROUTES["ONLY_EVC"]
    }

def get_route_for_workflow_code(code: str) -> Optional[WorkflowRouteDefinition]:
    """Resolves route definition by template or application type code."""
    return AUTHORITATIVE_ROUTES.get(code)
