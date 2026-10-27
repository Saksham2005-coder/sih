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

export interface EVCExpert {
  id: number;
  user_id?: number | null;
  name: string;
  email: string;
  phone?: string | null;
  designation: string;
  expertise_categories: string[];
  specializations: string[];
  current_institution: string;
  institution_id?: number | null;
  parent_organization?: string | null;
  district?: string | null;
  region: string;
  is_active: boolean;
  availability_status: 'AVAILABLE' | 'ENGAGED' | 'UNAVAILABLE' | 'ON_LEAVE' | string;
  declared_conflicts?: Array<{
    institution_id?: number;
    institution_name?: string;
    reason: string;
  }>;
  prior_inspections?: Array<{
    institution_id?: number;
    institution_name?: string;
    inspection_date: string;
    role?: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface COIRuleResult {
  rule_code: string;
  rule_name: string;
  status: 'PASSED' | 'FAILED';
  details: string;
}

export interface COICheckResult {
  expert_id: number;
  expert_name: string;
  current_institution: string;
  is_prohibited: boolean;
  can_override: boolean;
  summary: string;
  rules_checked: COIRuleResult[];
  assessed_at: string;
}

export interface EVCPanelAssignment {
  id: number;
  inspection_id: number;
  expert_id: number;
  expert_name?: string | null;
  expert_email?: string | null;
  expert_institution?: string | null;
  panel_role: 'CONVENER' | 'EXPERT_MEMBER' | string;
  status: 'PROPOSED' | 'INVITED' | 'ACCEPTED' | 'DECLINED' | 'CONFLICTED' | 'REASSIGNED' | string;
  invited_at?: string | null;
  responded_at?: string | null;
  decline_reason?: string | null;
  coi_check_result?: Record<string, any> | null;
  override_applied: boolean;
  override_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EVCFieldEvidence {
  id: number;
  inspection_id: number;
  checklist_item_code: string;
  requirement_title: string;
  observation_notes: string;
  status: 'COMPLIANT' | 'DEFICIENT' | 'NOT_APPLICABLE' | 'PENDING_REVIEW' | string;
  file_url?: string | null;
  file_hash?: string | null;
  file_name?: string | null;
  file_size_bytes?: number | null;
  evidence_type: 'PHOTO' | 'DOCUMENT' | 'GEO_TAG' | 'VIDEO' | string;
  captured_by_id?: number | null;
  captured_at: string;
  latitude?: number | null;
  longitude?: number | null;
  location_accuracy_meters?: number | null;
  location_capture_source?: string | null;
  location_permission_granted: boolean;
  created_at: string;
  updated_at: string;
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
  panel_status?: 'PENDING_PANEL' | 'INVITATIONS_DISPATCHED' | 'PANEL_CONFIRMED' | 'REASSIGNMENT_REQUIRED' | string;
  check_in_at?: string | null;
  check_in_lat?: number | null;
  check_in_lon?: number | null;
  check_in_accuracy?: number | null;
  check_in_source?: string | null;
  virtual_meeting_url?: string | null;
  virtual_recording_url?: string | null;
  report_url?: string | null;
  report_notes?: string | null;
  recommendation?: string | null;
  created_at: string;
  updated_at: string;
  panel_assignments?: EVCPanelAssignment[];
  field_evidence?: EVCFieldEvidence[];
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

export interface StatutoryOrderData {
  id: number;
  application_id: number;
  application_number: string;
  institution_id: number;
  institution_name: string;
  order_number: string;
  decision: 'APPROVED' | 'REJECTED';
  status: 'ACTIVE' | 'SUPERSEDED' | 'REVOKED';
  version: number;
  order_date: string;
  decision_recorded_at: string;
  issued_by_id?: number | null;
  issued_by_name: string;
  issued_by_designation: string;
  decision_remarks: string;
  conditions: Array<{
    rule_code?: string;
    title: string;
    category?: string;
    due_date?: string;
    status?: string;
  }>;
  reference_identifiers: Record<string, any>;
  pdf_filename: string;
  pdf_storage_key: string;
  pdf_url: string;
  checksum_sha256: string;
  verification_token: string;
  verification_url: string;
  template_version: string;
  signature_status: 'UNSIGNED_PROTOTYPE' | 'AWAITING_AUTHORIZED_SIGNATURE' | 'SIGNED_BY_CONFIGURED_PROVIDER' | 'SIGNATURE_VERIFICATION_FAILED';
  signing_provider: string;
  signing_metadata: Record<string, any>;
  signature_disclaimer: string;
  is_revoked: boolean;
  revoked_at?: string | null;
  revocation_reason?: string | null;
  superseded_by_order_id?: number | null;
  superseded_at?: string | null;
  superseding_reason?: string | null;
  created_at: string;
}

export interface StatutoryOrderPublicVerificationData {
  is_authentic: boolean;
  verification_status: 'VERIFIED_AUTHENTIC' | 'TAMPERED_HASH_MISMATCH' | 'REVOKED' | 'SUPERSEDED' | 'NOT_FOUND';
  artifact_hash_match: boolean;
  order_number: string;
  application_number: string;
  institution_name: string;
  regional_office: string;
  decision: 'APPROVED' | 'REJECTED';
  order_date: string;
  version: number;
  status: 'ACTIVE' | 'SUPERSEDED' | 'REVOKED';
  order_status?: string;
  is_revoked: boolean;
  revocation_reason?: string | null;
  superseded_by?: string | null;
  checksum_sha256: string;
  signature_status: string;
  signing_provider: string;
  signature_disclaimer: string;
  regulatory_disclaimer?: string;
  status_details: string;
  verified_at: string;
}

export interface OrderArtifactVerifyUploadData {
  is_valid: boolean;
  is_match: boolean;
  verification_status: 'AUTHENTIC_MATCH' | 'NO_MATCH_FOUND' | 'TAMPERED_OR_UNREGISTERED';
  integrity_status?: string;
  order_number?: string | null;
  matched_order_number?: string | null;
  decision?: string | null;
  version?: number | null;
  institution_name?: string | null;
  computed_checksum_sha256: string;
  stored_checksum_sha256?: string | null;
  message: string;
}

export interface NotificationOutboxItem {
  id: number;
  idempotency_key: string;
  correlation_id: string;
  event_type: string;
  entity_type: string;
  entity_id: number;
  institution_id?: number | null;
  region?: string | null;
  recipient_role?: string | null;
  recipient_user_id?: number | null;
  recipient_email?: string | null;
  recipient_phone?: string | null;
  channel: 'EMAIL' | 'SMS' | 'IN_APP';
  template_code: string;
  subject: string;
  body_text: string;
  body_html?: string | null;
  link_url?: string | null;
  status: 'QUEUED' | 'PROCESSING' | 'ACCEPTED_BY_PROVIDER' | 'SIMULATED' | 'NOT_CONFIGURED' | 'RETRY_SCHEDULED' | 'DEAD_LETTER' | 'FAILED';
  attempt_count: number;
  max_attempts: number;
  next_retry_at?: string | null;
  last_attempt_at?: string | null;
  last_error_category?: string | null;
  last_error_message?: string | null;
  provider_message_id?: string | null;
  provider_response?: string | null;
  sent_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationOutboxSummary {
  total: number;
  queued: number;
  processing: number;
  accepted_by_provider: number;
  simulated: number;
  not_configured: number;
  retry_scheduled: number;
  dead_letter: number;
  failed: number;
}

export interface ChannelHealthStatus {
  channel: string;
  transport: string;
  is_configured: boolean;
  status: string;
  details: Record<string, any>;
}

export interface NotificationChannelStatus {
  channels: ChannelHealthStatus[];
  active_sse_subscribers: number;
}

export interface NotificationUnreadCount {
  unread_count: number;
  total_count: number;
}

export interface LiveSSEEventSummary {
  event_type: string;
  title: string;
  message: string;
  level: string;
  entity_type?: string | null;
  entity_id?: number | null;
  link_url?: string | null;
  timestamp: string;
  institution_id?: number | null;
  recipient_role?: string | null;
}

// Judge Demonstration Centre & Live Workflow Explorer Types
export interface DemoPersonaInfo {
  name: string;
  email: string;
  role: string;
  rationale: string;
}

export interface DemoScenarioItem {
  scenario_id: string;
  scenario_number: number;
  title: string;
  subtitle: string;
  route_code: string;
  application_number: string;
  application_id: number;
  current_stage: string;
  priority_score: number;
  recommended_persona: DemoPersonaInfo;
  target_url: string;
  key_evaluation_points: string[];
}

export interface WorkflowStageDefinition {
  stage_code: string;
  label: string;
  description: string;
  permitted_roles: string[];
  is_terminal?: boolean;
  sla_days: number;
}

export interface WorkflowTransitionDefinition {
  from_stage: string;
  to_stage: string;
  permitted_roles: string[];
  is_return_loop?: boolean;
  description?: string;
}

export interface NonApplicableStageDefinition {
  stage_code: string;
  stage_label: string;
  statutory_reason: string;
  aph_rule_reference: string;
}

export interface WorkflowRouteDefinition {
  route_code: string;
  route_name: string;
  description: string;
  stages: WorkflowStageDefinition[];
  transitions: WorkflowTransitionDefinition[];
  non_applicable_stages: NonApplicableStageDefinition[];
}

export interface SLATrackingDetail {
  stage: string;
  days_elapsed: number;
  configured_sla_days: number;
  sla_status: 'ON_TRACK' | 'APPROACHING_BREACH' | 'BREACHED';
  is_breached: boolean;
  rule_citation: string;
  rule_code?: string | null;
  rule_version?: string | null;
  is_illustrative_policy?: boolean;
  calculation_basis?: string | null;
}

export interface PriorityFactorItem {
  factor: string;
  points: number;
  category: string;
}

export interface PriorityBreakdownDetail {
  total_score: number;
  baseline_points: number;
  factors: PriorityFactorItem[];
  recommended_action: string;
  policy_version: string;
  is_deterministic: boolean;
}

export interface ExplainabilityResponse {
  application: {
    id: number;
    application_number: string;
    institution_id: number;
    institution_name: string;
    region: string;
    academic_year: string;
    application_type: string;
    workflow_template_code: string;
    current_stage: string;
    priority_score: number;
    version: number;
    evc_required: boolean;
    submitted_at?: string | null;
    updated_at?: string | null;
    approved_at?: string | null;
    rejected_at?: string | null;
  };
  sla_tracking: SLATrackingDetail;
  deficiency_summary: {
    total_count: number;
    open_count: number;
    cured_count: number;
    resolved_count: number;
    items: Array<{
      id: number;
      category: string;
      description: string;
      required_document?: string | null;
      status: string;
      cure_remarks?: string | null;
      has_cure_file: boolean;
    }>;
  };
  evc_prerequisites: {
    evc_required: boolean;
    has_inspection: boolean;
    inspection_id?: number | null;
    inspection_status: string;
    inspection_mode?: string | null;
    panel_confirmed: boolean;
    panel_members_count: number;
    report_recommendation?: string | null;
  };
  document_compliance: {
    total_documents: number;
    active_documents: number;
    expiring_soon_documents: number;
    expired_documents: number;
    total_undertakings: number;
    due_soon_undertakings: number;
    overdue_undertakings: number;
    verified_undertakings: number;
  };
  priority_breakdown: PriorityBreakdownDetail;
  escalations_and_alerts: Array<{
    id: number;
    escalation_level: string;
    rule_code: string;
    recipient_role: string;
    is_acknowledged: boolean;
    created_at?: string | null;
    idempotency_key: string;
  }>;
  audit_events: Array<{
    id: number;
    action: string;
    actor_name: string;
    actor_role: string;
    timestamp?: string | null;
    details: any;
  }>;
}

export interface DemoResetResponse {
  scenario_id: string;
  application_number: string;
  reset_stage: string;
  message: string;
  timestamp: string;
}

export interface DemoTelemetryResponse {
  demo_mode: boolean;
  scheduler_status: string;
  scan_interval_seconds: number;
  last_deadline_scan?: {
    run_id: string;
    trigger_mode: string;
    scanned_at: string;
    duration_ms: number;
    obligations_scanned: number;
    alerts_generated: number;
    escalations_generated: number;
  } | null;
  notification_transport: {
    email_provider: string;
    sms_provider: string;
    transport_mode: string;
    description: string;
  };
  active_scheduler_leases?: {
    holder_id: string;
    acquired_at?: string | null;
    expires_at: string;
    is_active: boolean;
  } | null;
}



