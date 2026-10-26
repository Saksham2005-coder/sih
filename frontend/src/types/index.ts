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
  permissions?: string[];
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
  version: number;
  submitted_at: string;
  approved_at?: string | null;
  rejected_at?: string | null;
  created_at: string;
  updated_at: string;
  open_deficiencies_count: number;
  evc_required?: boolean | null;
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
  file_size?: number | null;
  mime_type?: string | null;
  storage_key?: string | null;
  verification_status?: string | null;
  verified_by_id?: number | null;
  verified_at?: string | null;
  verification_notes?: string | null;
  remarks?: string | null;
  submitted_by_id?: number | null;
  submitted_at: string;
}

export interface ComplianceUndertaking {
  id: number;
  institution_id: number;
  institution_name?: string | null;
  application_id?: number | null;
  rule_code?: string | null;
  responsible_user_id?: number | null;
  reviewer_id?: number | null;
  evidence_type?: string | null;
  fulfilled_at?: string | null;
  effective_status?: string | null;
  title: string;
  category: string;
  description?: string | null;
  due_date: string;
  status: 'NOT_YET_DUE' | 'DUE_SOON' | 'PENDING_VERIFICATION' | 'UNDER_VERIFICATION' | 'CORRECTION_REQUIRED' | 'VERIFIED' | 'DEFICIENT' | 'OVERDUE';
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
  file_size?: number | null;
  mime_type?: string | null;
  storage_key?: string | null;
  renewal_reason?: string | null;
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
  application_id?: number | null;
  document_type: string;
  title: string;
  document_number?: string | null;
  issuing_authority?: string | null;
  valid_from?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  renewal_required?: boolean | null;
  effective_status?: string | null;
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
  coordinator_id?: number | null;
  convener_user_id?: number | null;
  expert_user_id?: number | null;
  completed_at?: string | null;
  completed_by_id?: number | null;
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
  recipient_role?: string | null;
  entity_type?: string | null;
  entity_id?: number | null;
  title: string;
  message: string;
  channel: string;
  delivery_channel?: string | null;
  delivery_status?: string | null;
  level: 'INFO' | 'WARNING' | 'DANGER' | 'SUCCESS';
  is_read: boolean;
  read_at?: string | null;
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
  region?: string | null;
  institution_id?: number | null;
  cycle_id?: string | null;
  rule_code?: string | null;
  rule_version?: string | null;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
  acknowledged_by_id?: number | null;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
  resolved_reason?: string | null;
  created_at: string;
}

export interface DeadlineEngineRunItem {
  id: number;
  run_id: string;
  trigger_mode: string;
  scanned_entities: number;
  reminders_created: number;
  escalations_created: number;
  duplicates_prevented: number;
  resolved_count: number;
  execution_time_ms: number;
  status: string;
  error_message?: string | null;
  created_at: string;
}

export interface DeadlineEngineStatus {
  is_running: boolean;
  scan_interval_seconds: number;
  last_run?: DeadlineEngineRunItem | null;
  total_runs: number;
  total_scanned: number;
  total_reminders: number;
  total_escalations: number;
  total_duplicates_prevented: number;
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
  institution_id?: number | null;
  region?: string | null;
  created_at: string;
}

export interface AuditExplorerData {
  items: AuditEventItem[];
  total: number;
  page: number;
  limit: number;
}

export interface RuleDefinitionItem {
  id: number;
  rule_code: string;
  name: string;
  category: string;
  version: string;
  config_json: string;
  is_active: boolean;
  status: 'DRAFT' | 'VALIDATED' | 'PUBLISHED' | 'RETIRED';
  description?: string | null;
  change_reason?: string | null;
  effective_from?: string | null;
  updated_at: string;
}

export interface RuleVersionHistoryItem {
  id: number;
  rule_id: number;
  rule_code: string;
  version: string;
  category: string;
  config_json: string;
  status: string;
  change_reason?: string | null;
  created_at: string;
}

export interface RuleValidateResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface RuleSimulateResponse {
  rule_code: string;
  version: string;
  simulation_results: Record<string, any>;
  dry_run_disclaimer: string;
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

export interface PriorityActionItem {
  application_id: number;
  application_number: string;
  institution_name: string;
  region: string;
  current_stage: string;
  priority_score: number;
  priority_tier: string;
  priority_factors: string[];
  days_in_stage: number;
  open_deficiencies_count: number;
  recommended_action: string;
  action_link: string;
}

export interface RecentActivityItem {
  id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  actor_name?: string | null;
  actor_role?: string | null;
  details?: string | null;
  created_at: string;
}

export interface CommandCentreData {
  summary: OperationalSummary;
  bottlenecks: {
    repeated_returns_count: number;
    verification_backlog_undertakings: number;
    verification_backlog_documents: number;
    unscheduled_evc_count: number;
    average_stage_ageing_days: number;
  };
  priority_queue: PriorityActionItem[];
  recent_activity: RecentActivityItem[];
  role_scope: string;
  jurisdiction?: string | null;
}

export interface SlaAdherenceData {
  total_cases_analyzed: number;
  within_sla_count: number;
  within_sla_percentage: number;
  breached_sla_count: number;
  breached_sla_percentage: number;
  stage_sla_breakdown: Array<{
    stage: string;
    case_count: number;
    average_days: number;
    breached_count: number;
    within_count: number;
  }>;
}

export interface EvcAnalyticsData {
  total_inspections: number;
  eligible_count?: number;
  scheduled_count: number;
  completed_count: number;
  recommendations: Record<string, number>;
  inspection_types: Record<string, number>;
  filtered_region?: string | null;
}

export interface ComplianceAnalyticsData {
  total_undertakings: number;
  verified_count: number;
  pending_verification_count: number;
  correction_required_count: number;
  overdue_count: number;
  compliance_percentage: number;
  category_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  filtered_region?: string | null;
}

export interface DocumentAnalyticsData {
  total_documents: number;
  active_count: number;
  expiring_soon_count: number;
  renewal_submitted_count: number;
  expired_count: number;
  validity_compliance_percentage: number;
  type_breakdown: Record<string, number>;
  filtered_region?: string | null;
}

export interface EscalationsAnalyticsData {
  total_escalations: number;
  active_count: number;
  acknowledged_count: number;
  resolved_count: number;
  tier_breakdown: Record<string, number>;
  trigger_breakdown: Record<string, number>;
  filtered_region?: string | null;
}

export interface RegionalPerformanceItem {
  region: string;
  total_applications: number;
  pending_scrutiny: number;
  in_evc: number;
  approved: number;
  rejected: number;
  avg_turnaround_days: number;
  sla_compliance_rate: number;
  active_escalations: number;
}

export interface RegionalPerformanceData {
  regions: RegionalPerformanceItem[];
  national_avg_turnaround_days: number;
  national_sla_compliance_rate: number;
}

export interface ApplicationAuditTrailItem {
  id?: number | null;
  timestamp: string;
  event_type: string;
  actor_name?: string | null;
  actor_role?: string | null;
  actor_id?: number | null;
  previous_state?: string | null;
  resulting_state?: string | null;
  reason_or_remarks?: string | null;
  rule_or_version_applied?: string | null;
  outcome_status?: string | null;
  entity_type: string;
  entity_id: number;
  metadata?: any;
}

export interface ApplicationLifecycleData {
  application_id: number;
  application_number: string;
  institution_name: string;
  region: string;
  current_stage: string;
  academic_year: string;
  workflow_template_code: string;
  version: number;
  timeline: ApplicationAuditTrailItem[];
}

export interface CaseBriefData {
  application_id: number;
  application_number: string;
  institution_name: string;
  region: string;
  current_stage: string;
  priority_score: number;
  provenance: string;
  generated_at: string;
  summary_paragraphs: string[];
  suggested_administrative_draft: string;
  evidence_milestones: Array<{
    stage_id: number;
    from_stage?: string | null;
    to_stage: string;
    actor_name: string;
    actor_role: string;
    remarks: string;
    timestamp?: string | null;
  }>;
  evidence_deficiencies: Array<{
    deficiency_id: number;
    category: string;
    description: string;
    status: string;
    required_document?: string | null;
    cure_document_url?: string | null;
    cure_remarks?: string | null;
    cured_at?: string | null;
    issued_at?: string | null;
  }>;
  evidence_undertakings: Array<{
    undertaking_id: number;
    title: string;
    category: string;
    status: string;
    due_date?: string | null;
    evidence_submitted: boolean;
    evidence_version?: number | null;
    evidence_checksum_sha256?: string | null;
    verified_at?: string | null;
  }>;
  evidence_evc?: {
    evc_id: number;
    inspection_type: string;
    status: string;
    scheduled_date: string;
    convener_name: string;
    expert_member_name: string;
    recommendation: string;
    report_notes: string;
    completed_at?: string | null;
  } | null;
  evidence_escalations: Array<{
    escalation_id: number;
    level: string;
    status: string;
    recipient_role: string;
    created_at?: string | null;
    resolved_at?: string | null;
  }>;
  regulatory_disclaimer: string;
}

export interface ExtractedFieldCandidate {
  value?: string | null;
  confidence: number;
  source_page?: number | null;
  source_excerpt?: string | null;
  field_label?: string | null;
}

export interface CrossCheckFinding {
  field: string;
  rule_code: string;
  status: 'MATCH' | 'POSSIBLE_MISMATCH' | 'MISSING_EVIDENCE' | 'EXTRACTION_UNAVAILABLE' | 'HUMAN_REVIEW_REQUIRED';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  entered_value?: string | null;
  extracted_value?: string | null;
  source_page?: number | null;
  source_excerpt?: string | null;
  description: string;
}

export interface DocumentAnalysisData {
  id: number;
  document_record_id?: number | null;
  document_version_id?: number | null;
  compliance_evidence_id?: number | null;
  institution_id: number;
  institution_name?: string | null;
  status: 'QUEUED' | 'PROCESSING' | 'REVIEW_REQUIRED' | 'CONFIRMED' | 'FAILED';
  idempotency_key: string;
  extraction_engine: string;
  engine_version: string;
  ocr_applied: boolean;
  ocr_provider: string;
  file_name: string;
  file_size?: number | null;
  checksum_sha256: string;
  page_count: number;
  has_text_layer: boolean;
  is_scanned: boolean;
  extracted_fields: Record<string, ExtractedFieldCandidate>;
  cross_check_findings: CrossCheckFinding[];
  overall_confidence: number;
  summary_findings?: string | null;
  error_message?: string | null;
  reviewer_decision?: 'CONFIRMED' | 'CORRECTED' | 'REJECTED' | null;
  reviewed_by_id?: number | null;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  reviewer_remarks?: string | null;
  corrected_fields?: Record<string, any> | null;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentAnalysisReviewRequest {
  decision: 'CONFIRMED' | 'CORRECTED' | 'REJECTED';
  reviewer_remarks: string;
  corrected_fields?: Record<string, any> | null;
  apply_to_record?: boolean;
}

