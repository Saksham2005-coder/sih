import {
  User, TokenResponse, Application, ApplicationDetailResponse,
  ComplianceUndertaking, DocumentRecord, EVCInspection,
  NotificationItem, AlertEscalationItem, AuditEventItem,
  RuleDefinitionItem, OperationalSummary
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
  createApplication: (payload: { application_type: string; academic_year: string }) =>
    request<Application>('/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  transitionApplication: (id: number, payload: { to_stage: string; remarks?: string }) =>
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
  getCaseBrief: (id: number) => request<any>(`/applications/${id}/case-brief`),

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
  getNotifications: () => request<NotificationItem[]>('/alerts/notifications'),
  getEscalations: () => request<AlertEscalationItem[]>('/alerts/escalations'),
  runDeadlineScan: () => request<any>('/alerts/run-scan', { method: 'POST' }),
  acknowledgeEscalation: (id: number) => request<any>(`/alerts/${id}/acknowledge`, { method: 'POST' }),
  markNotificationRead: (id: number) => request<any>(`/alerts/notifications/${id}/read`, { method: 'POST' }),

  // Rules & Audit
  getRules: () => request<RuleDefinitionItem[]>('/rules'),
  updateRule: (ruleCode: string, payload: { config_json: string; version?: string; is_active?: boolean }) =>
    request<RuleDefinitionItem>(`/rules/${ruleCode}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  getAuditTrail: (params?: { entity_type?: string; action?: string }) => {
    const query = new URLSearchParams();
    if (params?.entity_type) query.set('entity_type', params.entity_type);
    if (params?.action) query.set('action', params.action);
    return request<AuditEventItem[]>(`/audit?${query.toString()}`);
  },

  // Reports
  getOperationalSummary: () => request<OperationalSummary>('/reports/summary'),
};
