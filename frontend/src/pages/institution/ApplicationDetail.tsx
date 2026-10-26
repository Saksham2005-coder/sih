import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock,
  Upload, Send, Bot, Shield, FileCheck, History
} from 'lucide-react';
import { api } from '../../api/client';
import { ApplicationDetailResponse, ApplicationLifecycleData } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';
import { StatutoryOrderModal } from '../../components/common/StatutoryOrderModal';

export const ApplicationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [app, setApp] = useState<ApplicationDetailResponse | null>(null);
  const [caseBrief, setCaseBrief] = useState<any | null>(null);
  const [lifecycleData, setLifecycleData] = useState<ApplicationLifecycleData | null>(null);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'AUDIT_TRAIL'>('OVERVIEW');
  const [loading, setLoading] = useState(true);
  const [cureModalOpen, setCureModalOpen] = useState(false);
  const [selectedDeficiencyId, setSelectedDeficiencyId] = useState<number | null>(null);
  const [cureRemarks, setCureRemarks] = useState('');
  const [cureFileUrl, setCureFileUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resubmitting, setResubmitting] = useState(false);
  const [orderModalOpen, setOrderModalOpen] = useState(false);

  const loadData = async () => {
    if (!id) return;
    try {
      const [data, brief, lifecycle] = await Promise.all([
        api.getApplicationDetail(Number(id)),
        api.getCaseBrief(Number(id)).catch(() => null),
        api.getApplicationAuditTrail(Number(id)).catch(() => null),
      ]);
      setApp(data);
      setCaseBrief(brief);
      setLifecycleData(lifecycle);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleOpenCureModal = (defId: number) => {
    setSelectedDeficiencyId(defId);
    setCureRemarks('');
    setCureFileUrl('/api/documents/download/cured_rectification_signed.pdf');
    setCureModalOpen(true);
  };

  const handleCureSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!app || !selectedDeficiencyId) return;
    setSubmitting(true);
    try {
      await api.cureDeficiency(app.id, selectedDeficiencyId, {
        cure_remarks: cureRemarks,
        cure_document_url: cureFileUrl,
      });
      setCureModalOpen(false);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to submit cure');
    } finally {
      setSubmitting(false);
    }
  };

  const handleResubmitApplication = async () => {
    if (!app) return;
    if (!confirm('Are you sure you want to resubmit this application to the Regional Officer for scrutiny verification?')) return;
    setResubmitting(true);
    try {
      await api.transitionApplication(app.id, {
        to_stage: 'RESUBMITTED',
        remarks: 'Institution has cured all itemized deficiencies with verified compliance documents attached.',
        expected_version: app.version,
      });
      loadData();
    } catch (err: any) {
      if (err.message?.includes('Conflict')) {
        alert('Conflict: Application was updated by another process. Refreshing latest state.');
        loadData();
      } else {
        alert(err.message || 'Resubmission failed');
      }
    } finally {
      setResubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-brand-muted">Loading application dossier...</div>;
  }

  if (!app) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm font-semibold text-brand-ink">Application not found</p>
        <Link to="/institution/applications" className="text-xs text-brand-teal mt-2 inline-block">
          Return to applications
        </Link>
      </div>
    );
  }

  const openDeficiencies = app.deficiencies?.filter((d) => d.status === 'OPEN') || [];
  const allOpenCured = openDeficiencies.every((d) => !!d.cure_remarks);

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/institution/applications"
            className="p-1.5 rounded-lg border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-brand-ink dark:text-brand-ink">{app.application_number}</h1>
              <StatusBadge status={app.current_stage} />
            </div>
            <p className="text-xs text-brand-muted dark:text-brand-muted">
              {app.institution_name} • {app.application_type.replace(/_/g, ' ')} ({app.academic_year})
            </p>
          </div>
        </div>

        {/* Resubmit Action Button if in DEFICIENCY_COMMUNICATED */}
        {app.current_stage === 'DEFICIENCY_COMMUNICATED' && (
          <button
            onClick={handleResubmitApplication}
            disabled={resubmitting || !allOpenCured}
            title={!allOpenCured ? 'Please provide cure remarks and documents for all open deficiencies first.' : ''}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-sm transition-colors ${
              allOpenCured
                ? 'bg-brand-teal hover:bg-brand-teal-dark text-white'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
            {resubmitting ? 'Resubmitting...' : 'Resubmit Application to Officer'}
          </button>
        )}

        {/* View Statutory Order Artifact Button for Approved/Rejected */}
        {(app.current_stage === 'APPROVED' || app.current_stage === 'REJECTED') && (
          <button
            onClick={() => setOrderModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors"
          >
            <FileText className="w-4 h-4" />
            View Official Statutory Order
          </button>
        )}
      </div>

      {/* View Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-brand-border dark:border-brand-border pb-2">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'OVERVIEW'
              ? 'bg-brand-ink text-white dark:bg-white dark:text-brand-ink shadow-sm'
              : 'text-brand-muted hover:text-brand-ink dark:hover:text-white bg-transparent'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Scrutiny & Application Dossier
        </button>
        <button
          onClick={() => setActiveTab('AUDIT_TRAIL')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'AUDIT_TRAIL'
              ? 'bg-brand-ink text-white dark:bg-white dark:text-brand-ink shadow-sm'
              : 'text-brand-muted hover:text-brand-ink dark:hover:text-white bg-transparent'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Operational Lifecycle Ledger & Audit Trail
          {lifecycleData && (
            <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-brand-teal text-white">
              {lifecycleData.timeline.length}
            </span>
          )}
        </button>
      </div>

      {/* Tab 2: Operational Lifecycle & Complete Audit Trail */}
      {activeTab === 'AUDIT_TRAIL' && (
        <div className="space-y-6">
          {/* Statutory Accountability Ledger Summary */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-brand-border dark:border-brand-border gap-2">
              <div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink flex items-center gap-2">
                  <Shield className="w-4 h-4 text-brand-teal" />
                  Statutory Operational Audit Trail & Lifecycle Ledger
                </h3>
                <p className="text-xs text-brand-muted dark:text-brand-muted">
                  Immutable chronological ledger of all filings, deficiency memos, cures, inspections, escalations, and statutory decisions.
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200 dark:border-teal-900 self-start sm:self-auto">
                {lifecycleData?.timeline.length || 0} Chronological Events Persisted
              </span>
            </div>

            {/* Regulatory Evaluation Reference */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-2 pt-1 text-center text-xs">
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">1. Who Acted?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">Actor Name & Role</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">2. Record Changed?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">Entity Type & ID</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">3. State Transition?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">Previous &rarr; Resulting</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">4. Action Rationale?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">Mandatory Remarks</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">5. Rule / Version?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">APH Clause Reference</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">6. Action Outcome?</span>
                <span className="text-brand-ink dark:text-brand-ink font-medium mt-0.5 block">Accepted / Cured / Granted</span>
              </div>
            </div>
          </div>

          {/* Chronological Timeline */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-ink pb-2 border-b border-brand-border dark:border-brand-border flex justify-between items-center">
              <span>Chronological Operational Events ({lifecycleData?.timeline.length || 0} Records)</span>
              <span className="text-brand-muted text-[10px] font-normal">Sorted Chronologically</span>
            </h4>

            {(!lifecycleData || lifecycleData.timeline.length === 0) ? (
              <div className="p-8 text-center text-xs text-brand-muted">
                No lifecycle events recorded for this application.
              </div>
            ) : (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-brand-border dark:before:bg-brand-border">
                {lifecycleData.timeline.map((event, idx) => {
                  const eventDate = new Date(event.timestamp);
                  const isApproved = event.outcome_status === 'APPROVED';
                  const isRejected = event.outcome_status === 'REJECTED';
                  const isDeficiency = event.event_type.includes('DEFICIENCY');
                  const isEvc = event.event_type.includes('EVC');
                  const isEscalation = event.event_type.includes('ESCALATION');

                  return (
                    <div key={idx} className="relative text-xs">
                      {/* Timeline dot */}
                      <span className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full ring-4 ${
                        isApproved ? 'bg-teal-600 ring-teal-100 dark:ring-teal-900' :
                        isRejected ? 'bg-red-600 ring-red-100 dark:ring-red-900' :
                        isDeficiency ? 'bg-amber-500 ring-amber-100 dark:ring-amber-900' :
                        isEvc ? 'bg-indigo-600 ring-indigo-100 dark:ring-indigo-900' :
                        isEscalation ? 'bg-red-500 ring-red-100 dark:ring-red-900' :
                        'bg-brand-teal ring-teal-50 dark:ring-teal-950'
                      }`} />

                      <div className="p-4 rounded-xl border border-brand-border dark:border-brand-border bg-brand-porcelain/30 dark:bg-brand-surface-elevated/40 space-y-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-brand-ink dark:text-brand-ink">
                              {event.event_type.replace(/_/g, ' ')}
                            </span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white dark:bg-brand-surface border border-brand-border text-brand-muted">
                              {event.entity_type} #{event.entity_id}
                            </span>
                            {event.outcome_status && (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isApproved ? 'bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300' :
                                isRejected ? 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300' :
                                isDeficiency ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300' :
                                'bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200'
                              }`}>
                                Outcome: {event.outcome_status.replace(/_/g, ' ')}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] font-mono text-brand-muted">
                            {eventDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })} at {eventDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })} UTC
                          </span>
                        </div>

                        {/* Actor & State Details */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 text-[11px] pt-1">
                          <div>
                            <span className="text-brand-muted">Actor:</span>{' '}
                            <span className="font-semibold text-brand-ink dark:text-brand-ink">{event.actor_name || 'System Daemon'}</span>{' '}
                            <span className="text-[10px] text-brand-muted">({event.actor_role?.replace(/_/g, ' ') || 'SYSTEM'})</span>
                          </div>
                          <div>
                            <span className="text-brand-muted">State Transition:</span>{' '}
                            <span className="font-mono text-[10px] text-brand-ink dark:text-brand-ink">
                              {event.previous_state || 'INITIAL'} &rarr; {event.resulting_state}
                            </span>
                          </div>
                          <div>
                            <span className="text-brand-muted">Rule / Policy:</span>{' '}
                            <span className="text-brand-ink dark:text-brand-ink font-medium">{event.rule_or_version_applied || 'Standard APH Workflow'}</span>
                          </div>
                        </div>

                        {/* Reason / Remarks */}
                        {event.reason_or_remarks && (
                          <div className="mt-2 p-2.5 rounded bg-white dark:bg-brand-surface border border-brand-border text-xs text-brand-ink dark:text-brand-ink">
                            <span className="font-semibold text-brand-muted uppercase text-[9px] block mb-0.5">Recorded Reason & Observations:</span>
                            {event.reason_or_remarks}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 1: Overview & Scrutiny */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
      {/* Case Brief Assistant Box */}
      {caseBrief && (
        <div className="bg-gradient-to-r from-teal-900 to-brand-ink text-white rounded-xl p-5 shadow-sm border border-teal-800">
          <div className="flex items-center justify-between mb-2">
            <span className="flex items-center gap-2 text-xs font-bold text-teal-300 uppercase tracking-wider">
              <Bot className="w-4 h-4" /> Case Brief Assistant
            </span>
            <span className="text-[10px] text-gray-300 bg-teal-800/60 px-2 py-0.5 rounded border border-teal-600/40">
              Deterministic Regulatory Engine
            </span>
          </div>
          <p className="text-xs leading-relaxed text-gray-100">{caseBrief.synthesis}</p>
          <div className="mt-3 pt-3 border-t border-teal-800/80 flex flex-wrap gap-4 text-[11px] text-teal-200">
            <span>Milestones: {caseBrief.milestones_count}</span>
            <span>Total Deficiencies: {caseBrief.total_deficiencies}</span>
            <span>Cured: {caseBrief.cured_deficiencies}</span>
            <span>Urgency Index: {caseBrief.priority_index}/100</span>
          </div>
        </div>
      )}

      {/* Main Grid: Deficiencies & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Deficiencies & Scrutiny Observations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deficiency Memo Card */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm p-6 transition-colors">
            <div className="flex items-center justify-between pb-3 border-b border-brand-border dark:border-brand-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  Itemized Scrutiny Deficiencies
                </h3>
                <p className="text-xs text-brand-muted dark:text-brand-muted">
                  Official observations recorded by AICTE Scrutiny Committee
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-brand-porcelain dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink border border-brand-border/60 dark:border-brand-border">
                {app.deficiencies?.length || 0} Total Items
              </span>
            </div>

            {(!app.deficiencies || app.deficiencies.length === 0) ? (
              <div className="p-8 text-center bg-brand-porcelain/40 rounded-lg border border-dashed border-brand-border">
                <CheckCircle className="w-8 h-8 text-brand-teal mx-auto mb-2" />
                <p className="text-xs font-semibold text-brand-ink">Zero Deficiencies Communicated</p>
                <p className="text-[11px] text-brand-muted mt-0.5">
                  This application has cleared preliminary scrutiny parameters.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {app.deficiencies.map((def) => (
                  <div
                    key={def.id}
                    className={`p-4 rounded-xl border transition-all ${
                      def.status === 'OPEN'
                        ? 'border-amber-200 bg-amber-50/30'
                        : 'border-teal-200 bg-teal-50/20'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-brand-ink uppercase tracking-wider">
                            [{def.category}]
                          </span>
                          <StatusBadge status={def.status} />
                        </div>
                        <p className="text-xs text-brand-ink mt-2 font-medium">{def.description}</p>
                        {def.required_document && (
                          <p className="text-[11px] text-brand-muted mt-1">
                            Prescribed Cure Document: <span className="font-semibold text-brand-ink">{def.required_document}</span>
                          </p>
                        )}
                      </div>

                      {def.status === 'OPEN' && (
                        <button
                          onClick={() => handleOpenCureModal(def.id)}
                          className="px-3 py-1.5 rounded-lg bg-[#C5892B] hover:bg-amber-700 text-white text-xs font-semibold shadow-sm shrink-0"
                        >
                          {def.cure_remarks ? 'Update Cure' : 'Submit Cure'}
                        </button>
                      )}
                    </div>

                    {/* Show cure submission if recorded */}
                    {def.cure_remarks && (
                      <div className="mt-3 pt-3 border-t border-gray-200 bg-white/60 p-3 rounded-lg text-xs">
                        <p className="font-semibold text-teal-800 flex items-center gap-1.5">
                          <FileCheck className="w-4 h-4 text-brand-teal" /> Institution Rectification Explanation:
                        </p>
                        <p className="text-brand-muted mt-1">{def.cure_remarks}</p>
                        {def.cure_document_url && (
                          <div className="mt-2">
                            <a
                              href={def.cure_document_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
                            >
                              <FileText className="w-3.5 h-3.5" /> View Attached Cure Evidence Document
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Timeline & Metadata */}
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm space-y-3 transition-colors">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-ink pb-2 border-b border-brand-border dark:border-brand-border">
              Regulatory Dossier Metadata
            </h4>
            <div className="text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-brand-muted dark:text-brand-muted">Academic Year:</span>
                <span className="font-semibold text-brand-ink dark:text-brand-ink">{app.academic_year}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brand-muted dark:text-brand-muted">Application Type:</span>
                <span className="font-semibold text-brand-ink dark:text-brand-ink">{app.application_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brand-muted dark:text-brand-muted">Regional Office:</span>
                <span className="font-semibold text-brand-ink dark:text-brand-ink">{app.region || 'Western'}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-brand-border dark:border-brand-border">
                <span className="text-brand-muted dark:text-brand-muted">Priority Urgency:</span>
                <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
              </div>
            </div>
          </div>

          {/* Workflow Stage Timeline */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm transition-colors">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-ink pb-3 border-b border-brand-border dark:border-brand-border mb-4">
              Stage Progression Timeline
            </h4>
            <div className="space-y-4">
              {app.stages?.map((stage, idx) => (
                <div key={stage.id} className="relative pl-6 pb-2 text-xs">
                  {/* Vertical line connecting nodes */}
                  {idx !== (app.stages?.length || 1) - 1 && (
                    <span className="absolute left-2.5 top-3 w-0.5 h-full bg-brand-border dark:bg-brand-border" />
                  )}
                  {/* Node icon */}
                  <span className="absolute left-1 top-1 w-3.5 h-3.5 rounded-full bg-brand-teal ring-4 ring-teal-50 dark:ring-brand-teal/20" />
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-brand-ink">{stage.to_stage.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] text-brand-muted">
                        {new Date(stage.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </span>
                    </div>
                    <p className="text-[11px] text-brand-muted mt-0.5">
                      By: {stage.actor_name || 'System'} ({stage.actor_role?.replace(/_/g, ' ')})
                    </p>
                    {stage.remarks && (
                      <p className="text-xs text-brand-ink/80 bg-brand-porcelain p-2 rounded mt-1.5 border border-brand-border">
                        {stage.remarks}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      </div>
      )}

      {/* Deficiency Cure Submission Modal */}
      <Modal
        isOpen={cureModalOpen}
        onClose={() => setCureModalOpen(false)}
        title="Submit Deficiency Rectification"
        subtitle="Provide explanation and attach supporting statutory evidence for scrutiny review"
      >
        <form onSubmit={handleCureSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Rectification Explanation & Notes
            </label>
            <textarea
              required
              rows={4}
              value={cureRemarks}
              onChange={(e) => setCureRemarks(e.target.value)}
              placeholder="Detail the corrections made, authority seals obtained, or regulatory provisions satisfied..."
              className="w-full border border-brand-border rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Attach Supporting Cure Document URL / File Reference
            </label>
            <input
              type="text"
              value={cureFileUrl}
              onChange={(e) => setCureFileUrl(e.target.value)}
              className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal font-mono text-[11px]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setCureModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-dark shadow-sm"
            >
              {submitting ? 'Saving...' : 'Save Rectification'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Statutory Order Modal */}
      {app && (
        <StatutoryOrderModal
          isOpen={orderModalOpen}
          onClose={() => setOrderModalOpen(false)}
          applicationId={app.id}
          applicationNumber={app.application_number}
          applicationStage={app.current_stage}
          onOrderChanged={loadData}
        />
      )}
    </div>
  );
};
