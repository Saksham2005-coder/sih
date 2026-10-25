from enum import Enum
from typing import Set, Dict, List, Optional
from fastapi import HTTPException, status, Depends
from app.models.user import User

class Permission(str, Enum):
    # Application permissions
    APPLICATION_READ = "application.read"
    APPLICATION_SUBMIT = "application.submit"
    APPLICATION_RESUBMIT = "application.resubmit"
    APPLICATION_SCRUTINY = "application.scrutiny"
    APPLICATION_DEFICIENCY_ISSUE = "application.deficiency_issue"
    APPLICATION_DEFICIENCY_CURE = "application.deficiency_cure"
    APPLICATION_DEFICIENCY_RESOLVE = "application.deficiency_resolve"
    APPLICATION_EVC_SCHEDULE = "application.evc_schedule"
    APPLICATION_EVC_REPORT = "application.evc_report"
    APPLICATION_COMMITTEE_REVIEW = "application.committee_review"
    APPLICATION_STATUTORY_DECISION = "application.statutory_decision"
    APPLICATION_CLOSE = "application.close"

    # Compliance Passport permissions
    COMPLIANCE_READ = "compliance.read"
    COMPLIANCE_SUBMIT = "compliance.submit"
    COMPLIANCE_VERIFY = "compliance.verify"

    # Documents & Expiries permissions
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_VERIFY = "document.verify"
    DOCUMENT_DOWNLOAD = "document.download"

    # EVC permissions
    EVC_VIEW = "evc.view"
    EVC_SCHEDULE = "evc.schedule"
    EVC_REPORT = "evc.report"

    # Alerts & Deadlines permissions
    ALERTS_VIEW = "alerts.view"
    ALERTS_SCAN = "alerts.scan"
    ALERTS_ACKNOWLEDGE = "alerts.acknowledge"

    # Rule Studio & System permissions
    RULES_VIEW = "rules.view"
    RULES_MANAGE = "rules.manage"
    USERS_MANAGE = "users.manage"
    AUDIT_READ = "audit.read"
    REPORTS_READ = "reports.read"

# Canonical Eight Roles
INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
REGIONAL_OFFICER = "REGIONAL_OFFICER"
BUREAU_OFFICER = "BUREAU_OFFICER"
COMMITTEE_MEMBER = "COMMITTEE_MEMBER"
EVC_COORDINATOR = "EVC_COORDINATOR"
COMPETENT_AUTHORITY = "COMPETENT_AUTHORITY"
SYSTEM_ADMIN = "SYSTEM_ADMIN"

ALL_ROLES = {
    INSTITUTION_ADMIN, COMPLIANCE_OFFICER, REGIONAL_OFFICER,
    BUREAU_OFFICER, COMMITTEE_MEMBER, EVC_COORDINATOR,
    COMPETENT_AUTHORITY, SYSTEM_ADMIN
}

# Role to Explicit Permissions Mapping (Canonical RBAC Matrix)
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    INSTITUTION_ADMIN: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_SUBMIT,
        Permission.APPLICATION_RESUBMIT,
        Permission.APPLICATION_DEFICIENCY_CURE,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_SUBMIT,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.ALERTS_VIEW,
        Permission.REPORTS_READ,
    },
    COMPLIANCE_OFFICER: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_RESUBMIT,
        Permission.APPLICATION_DEFICIENCY_CURE,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_SUBMIT,
        Permission.DOCUMENT_UPLOAD,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.ALERTS_VIEW,
    },
    REGIONAL_OFFICER: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_SCRUTINY,
        Permission.APPLICATION_DEFICIENCY_ISSUE,
        Permission.APPLICATION_DEFICIENCY_RESOLVE,
        Permission.APPLICATION_EVC_SCHEDULE,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_VERIFY,
        Permission.DOCUMENT_VERIFY,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.EVC_SCHEDULE,
        Permission.ALERTS_VIEW,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.RULES_VIEW,
        Permission.AUDIT_READ,
        Permission.REPORTS_READ,
    },
    BUREAU_OFFICER: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_SCRUTINY,
        Permission.APPLICATION_DEFICIENCY_ISSUE,
        Permission.APPLICATION_DEFICIENCY_RESOLVE,
        Permission.APPLICATION_EVC_SCHEDULE,
        Permission.APPLICATION_COMMITTEE_REVIEW,
        Permission.COMPLIANCE_READ,
        Permission.COMPLIANCE_VERIFY,
        Permission.DOCUMENT_VERIFY,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.EVC_SCHEDULE,
        Permission.ALERTS_VIEW,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.RULES_VIEW,
        Permission.AUDIT_READ,
        Permission.REPORTS_READ,
    },
    COMMITTEE_MEMBER: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_EVC_REPORT,
        Permission.APPLICATION_COMMITTEE_REVIEW,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.EVC_REPORT,
        Permission.ALERTS_VIEW,
        Permission.RULES_VIEW,
    },
    EVC_COORDINATOR: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_EVC_SCHEDULE,
        Permission.APPLICATION_EVC_REPORT,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.EVC_SCHEDULE,
        Permission.EVC_REPORT,
        Permission.ALERTS_VIEW,
        Permission.RULES_VIEW,
    },
    COMPETENT_AUTHORITY: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_STATUTORY_DECISION,
        Permission.APPLICATION_CLOSE,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.ALERTS_VIEW,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.RULES_VIEW,
        Permission.AUDIT_READ,
        Permission.REPORTS_READ,
    },
    SYSTEM_ADMIN: {
        Permission.APPLICATION_READ,
        Permission.APPLICATION_CLOSE,
        Permission.DOCUMENT_DOWNLOAD,
        Permission.EVC_VIEW,
        Permission.ALERTS_VIEW,
        Permission.ALERTS_SCAN,
        Permission.ALERTS_ACKNOWLEDGE,
        Permission.RULES_VIEW,
        Permission.RULES_MANAGE,
        Permission.USERS_MANAGE,
        Permission.AUDIT_READ,
        Permission.REPORTS_READ,
    },
}

def get_user_effective_permissions(user: User) -> Set[str]:
    """Calculate the union of all permissions granted to a user across assigned roles."""
    permissions: Set[str] = set()
    for role_obj in user.roles:
        role_name = role_obj.role
        if role_name in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role_name])
    return permissions

def user_has_permission(user: User, permission: str) -> bool:
    """Check if user has an explicit permission."""
    effective = get_user_effective_permissions(user)
    return permission in effective

def check_institution_scope(user: User, target_institution_id: int):
    """
    Enforces multi-tenant isolation.
    Institution users cannot access or mutate resources of another institution.
    """
    user_roles = [r.role for r in user.roles]
    is_officer = any(r in [
        REGIONAL_OFFICER, BUREAU_OFFICER, COMMITTEE_MEMBER,
        EVC_COORDINATOR, COMPETENT_AUTHORITY, SYSTEM_ADMIN
    ] for r in user_roles)

    if not is_officer:
        if user.institution_id != target_institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot access or modify records of another institution."
            )

def check_regional_scope(user: User, target_region: Optional[str]):
    """
    Enforces regional boundary scoping.
    Regional Officers can only mutate cases within their assigned region.
    National roles (Bureau Officer, Competent Authority, System Admin) bypass regional scope.
    """
    user_roles = [r.role for r in user.roles]
    
    # If the user is a Regional Officer without higher national operational roles
    if REGIONAL_OFFICER in user_roles and not any(r in [BUREAU_OFFICER, COMPETENT_AUTHORITY, SYSTEM_ADMIN] for r in user_roles):
        if user.region and target_region and user.region.lower() != target_region.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Case is registered under '{target_region}' Region, which is outside your assigned region '{user.region}'."
            )

def check_case_assignment(user: User, assigned_user_id: Optional[int], assigned_role: Optional[str] = None):
    """
    For roles with assigned case requirements (such as Committee Members on hearing panels).
    """
    user_roles = [r.role for r in user.roles]
    if COMMITTEE_MEMBER in user_roles and not any(r in [BUREAU_OFFICER, COMPETENT_AUTHORITY, SYSTEM_ADMIN] for r in user_roles):
        if assigned_user_id is not None and assigned_user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not assigned to this case review panel."
            )
