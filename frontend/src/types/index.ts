export interface User {
  id: number;
  email: string;
  full_name: string;
  institution_id?: number | null;
  region?: string | null;
  is_active: boolean;
  roles: string[];
  active_role?: string | null;
  institution_name?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApplicationStage {
  id: number;
  application_id: number;
  from_stage?: string | null;
  to_stage: string;
  actor_id?: number | null;
  actor_role?: string | null;
  actor_name?: string | null;
  remarks?: string | null;
  created_at: string;
}

export interface Deficiency {
  id: number;
  application_id: number;
  category: string;
  description: string;
  required_document?: string | null;
  status: 'OPEN' | 'CURED' | 'WAIVED';
  cure_document_url?: string | null;
  cure_remarks?: string | null;
  cured_at?: string | null;
  resolved_by_officer_id?: number | null;
  created_at: string;
}

export interface Application {
  id: number;
  application_number: string;
  institution_id: number;
  institution_name?: string | null;
  region?: string | null;
  academic_year: string;
  application_type: string;
  workflow_template_code: string;
  current_stage: string;
  scrutiny_officer_id?: number | null;
  priority_score: number;
  priority_factors?: {
    score: number;
    tier: string;
    factors: string[];
    calculated_at: string;
  } | null;
  submitted_at: string;
  approved_at?: string | null;
  rejected_at?: string | null;
  created_at: string;
  updated_at: string;
  open_deficiencies_count: number;
  stages?: ApplicationStage[];
  deficiencies?: Deficiency[];
}

export type ApplicationDetailResponse = Application;

export interface ComplianceEvidence {
  id: number;
  undertaking_id: number;
  version: number;
  file_name: string;
  file_url: string;
  checksum_sha256: string;
  remarks?: string | null;
  submitted_by_id?: number | null;
  submitted_at: string;
}

export interface ComplianceUndertaking {
  id: number;
  institution_id: number;
  institution_name?: string | null;
  title: string;
  category: string;
  description?: string | null;
  due_date: string;
  status: 'NOT_YET_DUE' | 'DUE_SOON' | 'PENDING_VERIFICATION' | 'VERIFIED' | 'DEFICIENT' | 'OVERDUE';
  verified_at?: string | null;
  verified_by_id?: number | null;
  created_at: string;
  evidences: ComplianceEvidence[];
}

export interface DocumentVersion {
  id: number;
  document_record_id: number;
  version: number;
  file_name: string;
  file_url: string;
  checksum_sha256: string;
  uploaded_by_id?: number | null;
  uploaded_at: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  verified_by_id?: number | null;
  verified_at?: string | null;
  verification_notes?: string | null;
}

export interface DocumentRecord {
  id: number;
  institution_id: number;
  institution_name?: string | null;
  document_type: string;
  title: string;
  document_number?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  status: 'ACTIVE' | 'EXPIRING_SOON' | 'RENEWAL_SUBMITTED' | 'VERIFIED' | 'EXPIRED';
  current_version: number;
  created_at: string;
  versions: DocumentVersion[];
}

export interface EVCInspection {
  id: number;
  application_id: number;
  application_number?: string | null;
  institution_id?: number | null;
  institution_name?: string | null;
  region?: string | null;
  inspection_type: string;
  scheduled_date?: string | null;
  convener_name?: string | null;
  expert_member_name?: string | null;
  status: string;
  report_url?: string | null;
  report_notes?: string | null;
  recommendation?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationItem {
  id: number;
  user_id?: number | null;
  institution_id?: number | null;
  title: string;
  message: string;
  channel: string;
  level: 'INFO' | 'WARNING' | 'DANGER' | 'SUCCESS';
  is_read: boolean;
  link_url?: string | null;
  created_at: string;
}

export interface AlertEscalationItem {
  id: number;
  idempotency_key: string;
  entity_type: string;
  entity_id: number;
  trigger_type: string;
  threshold_days: number;
  escalation_level: string;
  recipient_role: string;
  recipient_user_id?: number | null;
  status: string;
  acknowledged_by_id?: number | null;
  acknowledged_at?: string | null;
  created_at: string;
}

export interface AuditEventItem {
  id: number;
  actor_id?: number | null;
  actor_name?: string | null;
  actor_role?: string | null;
  action: string;
  entity_type: string;
  entity_id: number;
  details?: string | null;
  ip_address?: string | null;
  created_at: string;
}

export interface RuleDefinitionItem {
  id: number;
  rule_code: string;
  name: string;
  category: string;
  version: string;
  config_json: string;
  is_active: boolean;
  updated_at: string;
}

export interface OperationalSummary {
  total_applications: number;
  pending_scrutiny: number;
  deficiency_cure_required: number;
  awaiting_evc: number;
  evc_scheduled: number;
  approved: number;
  rejected: number;
  total_undertakings: number;
  overdue_undertakings: number;
  expiring_documents: number;
  active_escalations: number;
  stage_breakdown: Record<string, number>;
  regional_breakdown: Record<string, number>;
}
