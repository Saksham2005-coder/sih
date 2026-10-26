import {
  User, TokenResponse, Application, ApplicationDetailResponse,
  ComplianceUndertaking, DocumentRecord, EVCInspection,
  NotificationItem, AlertEscalationItem, AuditEventItem,
  RuleDefinitionItem, OperationalSummary,
  CaseBriefData, RuleVersionHistoryItem, RuleValidateResponse,
  RuleSimulateResponse, AuditExplorerData, CommandCentreData,
  SlaAdherenceData, EvcAnalyticsData, ComplianceAnalyticsData,
  DocumentAnalyticsData, EscalationsAnalyticsData,
  RegionalPerformanceData, ApplicationLifecycleData,
  DocumentAnalysisData, DocumentAnalysisReviewRequest
} from '../types';

const API_BASE = '/api';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('reguflow_token');
  const headers: HeadersInit = {
    'Accept': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Health
  getHealth: () => request<{ status: string; service: string; version: string; database: string }>('/health'),

  // Auth
  login: (email: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),
  getMe: () => request<User>('/auth/me'),
  logout: () =>
    request<{ message: string }>('/auth/logout', {
      method: 'POST',
    }),
  switchActiveRole: (role: string) =>
    request<User>('/auth/switch-active-role', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    }),
  getDemoUsers: () => request<{ demo_users: any[] }>('/auth/demo-users'),

  // Applications
  getApplications: (params?: { stage?: string; application_type?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.stage) query.set('stage', params.stage);
    if (params?.application_type) query.set('application_type', params.application_type);
    if (params?.search) query.set('search', params.search);
    return request<Application[]>(`/applications?${query.toString()}`);
  },
  getApplicationDetail: (id: number) => request<ApplicationDetailResponse>(`/applications/${id}`),
  createApplication: (payload: { application_type: string; academic_year: string; workflow_template_code?: string; evc_required?: boolean }) =>
    request<Application>('/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  transitionApplication: (id: number, payload: { to_stage: string; remarks?: string; expected_version?: number }) =>
    request<ApplicationDetailResponse>(`/applications/${id}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  issueDeficiency: (id: number, payload: { category: string; description: string; required_document?: string }) =>
    request<any>(`/applications/${id}/deficiencies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  cureDeficiency: (id: number, deficiencyId: number, payload: { cure_remarks: string; cure_document_url?: string }) =>
    request<any>(`/applications/${id}/cure-deficiency/${deficiencyId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  resolveDeficiency: (id: number, deficiencyId: number) =>
    request<any>(`/applications/${id}/resolve-deficiency/${deficiencyId}`, {
      method: 'POST',
    }),
  getCaseBrief: (id: number) => request<CaseBriefData>(`/applications/${id}/case-brief`),
  getApplicationAuditTrail: (id: number) => request<ApplicationLifecycleData>(`/applications/${id}/audit-trail`),

  // Compliance
  getUndertakings: (params?: { status_filter?: string; category?: string }) => {
    const query = new URLSearchParams();
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    if (params?.category) query.set('category', params.category);
    return request<ComplianceUndertaking[]>(`/compliance/undertakings?${query.toString()}`);
  },
  submitComplianceEvidence: (undertakingId: number, formData: FormData) =>
    request<any>(`/compliance/undertakings/${undertakingId}/submit-evidence`, {
      method: 'POST',
      body: formData,
    }),
  verifyCompliance: (undertakingId: number, payload: { status: string; notes?: string }) =>
    request<any>(`/compliance/undertakings/${undertakingId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Documents
  getDocuments: (params?: { document_type?: string; status_filter?: string }) => {
    const query = new URLSearchParams();
    if (params?.document_type) query.set('document_type', params.document_type);
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    return request<DocumentRecord[]>(`/documents?${query.toString()}`);
  },
  renewDocument: (documentId: number, formData: FormData) =>
    request<any>(`/documents/${documentId}/renew`, {
      method: 'POST',
      body: formData,
    }),
  verifyDocumentVersion: (documentId: number, versionId: number, payload: { verification_status: string; verification_notes?: string }) =>
    request<any>(`/documents/${documentId}/verify-version/${versionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  getDocumentAnalyses: (params?: { status?: string; institution_id?: number; document_record_id?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.institution_id) query.set('institution_id', String(params.institution_id));
    if (params?.document_record_id) query.set('document_record_id', String(params.document_record_id));
    return request<DocumentAnalysisData[]>(`/documents/analysis?${query.toString()}`);
  },
  getDocumentAnalysis: (id: number) =>
    request<DocumentAnalysisData>(`/documents/analysis/${id}`),
  getDocumentAnalysisByVersion: (versionId: number) =>
    request<DocumentAnalysisData>(`/documents/analysis/by-version/${versionId}`),
  triggerDocumentAnalysis: (payload: { document_record_id?: number; document_version_id?: number; force_retry?: boolean }) =>
    request<DocumentAnalysisData>('/documents/analysis/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  reviewDocumentAnalysis: (id: number, payload: DocumentAnalysisReviewRequest) =>
    request<DocumentAnalysisData>(`/documents/analysis/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // EVC
  getEVCQueue: () => request<EVCInspection[]>('/evc/queue'),
  scheduleEVC: (payload: { application_id: number; inspection_type: string; scheduled_date: string; convener_name: string; expert_member_name: string }) =>
    request<EVCInspection>('/evc/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  submitEVCReport: (inspectionId: number, payload: { report_url: string; report_notes: string; recommendation: string }) =>
    request<EVCInspection>(`/evc/${inspectionId}/submit-report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Alerts & Deadlines
  getNotifications: (params?: { unread_only?: boolean; level?: string; entity_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.unread_only) query.set('unread_only', 'true');
    if (params?.level) query.set('level', params.level);
    if (params?.entity_type) query.set('entity_type', params.entity_type);
    return request<NotificationItem[]>(`/alerts/notifications?${query.toString()}`);
  },
  getEscalations: (params?: { status_filter?: string; entity_type?: string; escalation_level?: string }) => {
    const query = new URLSearchParams();
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    if (params?.entity_type) query.set('entity_type', params.entity_type);
    if (params?.escalation_level) query.set('escalation_level', params.escalation_level);
    return request<AlertEscalationItem[]>(`/alerts/escalations?${query.toString()}`);
  },
  runDeadlineScan: () => request<any>('/alerts/run-scan', { method: 'POST' }),
  acknowledgeEscalation: (id: number, remarks?: string) =>
    request<any>(`/alerts/${id}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ remarks }),
    }),
  markNotificationRead: (id: number) => request<any>(`/alerts/notifications/${id}/read`, { method: 'POST' }),
  getEngineStatus: () => request<any>('/alerts/engine-status'),

  // Rules & Governance
  getRules: () => request<RuleDefinitionItem[]>('/rules'),
  getRuleHistory: (ruleCode: string) => request<RuleVersionHistoryItem[]>(`/rules/${ruleCode}/history`),
  validateRule: (ruleCode: string, configJson: string) =>
    request<RuleValidateResponse>(`/rules/${ruleCode}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config_json: configJson }),
    }),
  simulateRule: (ruleCode: string, payload: { config_json?: string; application_id?: number }) =>
    request<RuleSimulateResponse>(`/rules/${ruleCode}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  publishRule: (ruleCode: string, payload: { config_json: string; version: string; change_reason: string }) =>
    request<RuleDefinitionItem>(`/rules/${ruleCode}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  updateRule: (ruleCode: string, payload: { config_json: string; version?: string; is_active?: boolean; status?: string; description?: string; change_reason?: string }) =>
    request<RuleDefinitionItem>(`/rules/${ruleCode}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  // Audit Explorer
  getAuditTrail: (params?: { entity_type?: string; action?: string }) => {
    const query = new URLSearchParams();
    if (params?.entity_type) query.set('entity_type', params.entity_type);
    if (params?.action) query.set('action', params.action);
    return request<AuditExplorerData>(`/audit?${query.toString()}`).then(res => res.items);
  },
  getAuditExplorer: (params?: {
    entity_type?: string;
    entity_id?: number;
    action?: string;
    actor_role?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.entity_type) query.set('entity_type', params.entity_type);
    if (params?.entity_id) query.set('entity_id', params.entity_id.toString());
    if (params?.action) query.set('action', params.action);
    if (params?.actor_role) query.set('actor_role', params.actor_role);
    if (params?.search) query.set('search', params.search);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.limit) query.set('limit', params.limit.toString());
    return request<AuditExplorerData>(`/audit?${query.toString()}`);
  },

  // Reports & Command Centre
  getOperationalSummary: (params?: { region?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<OperationalSummary>(`/reports/summary?${query.toString()}`);
  },
  getCommandCentre: () => request<CommandCentreData>('/reports/command-centre'),
  getSlaAdherence: (params?: { region?: string; stage?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.stage) query.set('stage', params.stage);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<SlaAdherenceData>(`/reports/sla-adherence?${query.toString()}`);
  },
  getEvcAnalytics: (params?: { region?: string; inspection_type?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.inspection_type) query.set('inspection_type', params.inspection_type);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<EvcAnalyticsData>(`/reports/evc-analytics?${query.toString()}`);
  },
  getComplianceAnalytics: (params?: { region?: string; status_filter?: string; category?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    if (params?.category) query.set('category', params.category);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<ComplianceAnalyticsData>(`/reports/compliance-analytics?${query.toString()}`);
  },
  getDocumentAnalytics: (params?: { region?: string; status_filter?: string; document_type?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    if (params?.document_type) query.set('document_type', params.document_type);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<DocumentAnalyticsData>(`/reports/document-analytics?${query.toString()}`);
  },
  getEscalationsAnalytics: (params?: { region?: string; status_filter?: string; escalation_level?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.region) query.set('region', params.region);
    if (params?.status_filter) query.set('status_filter', params.status_filter);
    if (params?.escalation_level) query.set('escalation_level', params.escalation_level);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<EscalationsAnalyticsData>(`/reports/escalations-analytics?${query.toString()}`);
  },
  getRegionalPerformance: (params?: { date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return request<RegionalPerformanceData>(`/reports/regional-performance?${query.toString()}`);
  },
  getReportCsvUrl: (reportType: string, params?: { region?: string; stage?: string; date_from?: string; date_to?: string }) => {
    const query = new URLSearchParams();
    query.set('report_type', reportType);
    if (params?.region) query.set('region', params.region);
    if (params?.stage) query.set('stage', params.stage);
    if (params?.date_from) query.set('date_from', params.date_from);
    if (params?.date_to) query.set('date_to', params.date_to);
    return `/api/reports/export-csv?${query.toString()}`;
  },
};

