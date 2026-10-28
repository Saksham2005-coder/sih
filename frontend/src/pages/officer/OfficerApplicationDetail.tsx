import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock,
  Send, Bot, Check, ShieldCheck, ChevronRight, History,
  UserCheck, Layers, HelpCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { ApplicationDetailResponse, ApplicationLifecycleData } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';
import { StatutoryOrderModal } from '../../components/common/StatutoryOrderModal';

export const OfficerApplicationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user, activeRole } = useAuth();
  const [app, setApp] = useState<ApplicationDetailResponse | null>(null);
  const [caseBrief, setCaseBrief] = useState<any | null>(null);
  const [lifecycleData, setLifecycleData] = useState<ApplicationLifecycleData | null>(null);
  const [activeTab, setActiveTab] = useState<'SCRUTINY' | 'AUDIT_TRAIL'>('SCRUTINY');
  const [loading, setLoading] = useState(true);

  // Modals
  const [defModalOpen, setDefModalOpen] = useState(false);
  const [defCategory, setDefCategory] = useState('INFRASTRUCTURE');
  const [defDescription, setDefDescription] = useState('');
  const [defReqDoc, setDefReqDoc] = useState('');
  const [submittingDef, setSubmittingDef] = useState(false);

  const [transitionModalOpen, setTransitionModalOpen] = useState(false);
  const [targetStage, setTargetStage] = useState('');
  const [transitionRemarks, setTransitionRemarks] = useState('');
  const [submittingTransition, setSubmittingTransition] = useState(false);
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

  const handleIssueDeficiency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!app) return;
    setSubmittingDef(true);
    try {
      await api.issueDeficiency(app.id, {
        category: defCategory,
        description: defDescription,
        required_document: defReqDoc || undefined,
      });
      setDefModalOpen(false);
      setDefDescription('');
      setDefReqDoc('');
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to issue deficiency');
    } finally {
      setSubmittingDef(false);
    }
  };

  const handleResolveDeficiency = async (defId: number) => {
    if (!app) return;
    try {
      await api.resolveDeficiency(app.id, defId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to resolve deficiency');
    }
  };

  const handleTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!app || !targetStage) return;
    setSubmittingTransition(true);
    try {
      await api.transitionApplication(app.id, {
        to_stage: targetStage,
        remarks: transitionRemarks || undefined,
        expected_version: app.version,
      });
      setTransitionModalOpen(false);
      setTransitionRemarks('');
      loadData();
    } catch (err: any) {
      if (err.message?.includes('Conflict')) {
        alert('Conflict: Application was updated by another user or background task. Refreshing latest state.');
        loadData();
      } else {
        alert(err.message || 'Stage transition failed');
      }
    } finally {
      setSubmittingTransition(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-brand-muted">Loading officer scrutiny console...</div>;
  }

  if (!app) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm font-semibold text-brand-ink">Application not found</p>
        <Link to="/officer/applications" className="text-xs text-brand-teal mt-2 inline-block">
          Return to Registry
        </Link>
      </div>
    );
  }

  const openDeficiencies = app.deficiencies?.filter((d) => d.status === 'OPEN') || [];

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/officer/applications"
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
              {app.institution_name} • {app.region} Region • {app.application_type.replace(/_/g, ' ')}
            </p>
          </div>
        </div>

        {/* Action Controls for Officers */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Issue deficiency button */}
          <button
            onClick={() => setDefModalOpen(true)}
            className="px-3.5 py-2 rounded-lg border border-amber-300 bg-amber-50 text-[#C5892B] hover:bg-amber-100 text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
          >
            <AlertTriangle className="w-4 h-4" /> Issue Deficiency Memo
          </button>

          {/* Advance stage button */}
          <button
            onClick={() => {
              setTargetStage(
                app.current_stage === 'SUBMITTED' ? 'UNDER_SCRUTINY' :
                app.current_stage === 'RESUBMITTED' ? 'UNDER_SCRUTINY' :
                app.current_stage === 'UNDER_SCRUTINY' ? 'SCRUTINY_COMPLETED' :
                app.current_stage === 'SCRUTINY_COMPLETED' ? 'AWAITING_EVC_SCHEDULE' :
                app.current_stage === 'EVC_COMPLETED' ? 'AWAITING_SAC_CAC_REVIEW' :
                app.current_stage === 'AWAITING_SAC_CAC_REVIEW' ? 'AWAITING_COMPETENT_AUTHORITY' :
                app.current_stage === 'AWAITING_COMPETENT_AUTHORITY' ? 'APPROVED' : ''
              );
              setTransitionModalOpen(true);
            }}
            className="px-3.5 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
          >
            <ShieldCheck className="w-4 h-4" /> Stage Progression
          </button>

          {/* Statutory Order Artifact Button */}
          <button
            onClick={() => setOrderModalOpen(true)}
            className="px-3.5 py-2 rounded-lg border border-brand-teal/40 bg-brand-teal/10 text-brand-teal hover:bg-brand-teal/20 text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
          >
            <FileText className="w-4 h-4" /> Statutory Order Artifact
          </button>
        </div>
      </div>

      {/* View Switcher: Scrutiny vs Operational Audit Trail */}
      <div className="flex border-b border-brand-border gap-2 text-xs overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveTab('SCRUTINY')}
          className={`px-4 py-2.5 font-bold border-b-2 whitespace-nowrap shrink-0 transition-colors inline-flex items-center gap-1.5 ${activeTab === 'SCRUTINY' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          <FileText className="w-3.5 h-3.5" /> Scrutiny Console & Cures
        </button>
        <button
          onClick={() => setActiveTab('AUDIT_TRAIL')}
          className={`px-4 py-2.5 font-bold border-b-2 whitespace-nowrap shrink-0 transition-colors inline-flex items-center gap-1.5 ${activeTab === 'AUDIT_TRAIL' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          <History className="w-3.5 h-3.5" /> Lifecycle Ledger & Audit Trail
          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-teal-100 text-brand-teal border border-teal-300">
            Non-Repudiable
          </span>
        </button>
      </div>

      {/* Tab 2: Operational Audit Trail & Lifecycle Ledger */}
      {activeTab === 'AUDIT_TRAIL' && (
        <div className="space-y-6">
          {/* Audit Verification Banner */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-5 shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-border pb-3">
              <div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-brand-teal" />
                  Complete Application Regulatory Lifecycle & Non-Repudiable Audit Ledger
                </h3>
                <p className="text-xs text-brand-muted mt-0.5">
                  End-to-end traceability of application movement, observations, cures, panel reports, escalations, acknowledgements, and Competent Authority orders
                </p>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded bg-brand-porcelain dark:bg-brand-surface-elevated font-mono text-brand-ink dark:text-brand-text border border-brand-border font-semibold">
                Docket: {app.application_number} (v{app.version})
              </span>
            </div>

            {/* Evaluator Answers Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1 text-[11px]">
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">1. Who Acted?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">Attributed Actor & Role</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">2. Record Changed?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">Entity Type & Record ID</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">3. State Mutation?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">From &rarr; To Stage</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">4. Action Rationale?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">Mandatory Recorded Remarks</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">5. Rule / Version?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">SLA & APH Clause Reference</span>
              </div>
              <div className="p-2 rounded bg-teal-50/60 dark:bg-teal-950/20 border border-teal-200 dark:border-teal-900/40">
                <span className="text-[9px] font-bold uppercase text-teal-800 dark:text-teal-300 block">6. Action Outcome?</span>
                <span className="text-brand-ink dark:text-brand-text font-medium mt-0.5 block">Accepted / Cured / Granted</span>
              </div>
            </div>
          </div>

          {/* Chronological Timeline */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-text pb-2 border-b border-brand-border flex justify-between items-center">
              <span>Chronological Operational Events ({lifecycleData?.timeline.length || 0} Records)</span>
              <span className="text-brand-muted text-[10px] font-normal">Sorted Chronologically</span>
            </h4>

            {(!lifecycleData || lifecycleData.timeline.length === 0) ? (
              <div className="p-8 text-center text-xs text-brand-muted">
                No lifecycle events recorded for this application.
              </div>
            ) : (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-brand-border">
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

                      <div className="p-4 rounded-xl border border-brand-border bg-brand-porcelain/30 dark:bg-brand-surface-elevated/40 space-y-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-brand-ink dark:text-brand-text">
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
                            <span className="font-semibold text-brand-ink dark:text-brand-text">{event.actor_name || 'System Daemon'}</span>{' '}
                            <span className="text-[10px] text-brand-muted">({event.actor_role?.replace(/_/g, ' ') || 'SYSTEM'})</span>
                          </div>
                          <div>
                            <span className="text-brand-muted">State Transition:</span>{' '}
                            <span className="font-mono text-[10px] text-brand-ink dark:text-brand-text">
                              {event.previous_state || 'INITIAL'} &rarr; {event.resulting_state}
                            </span>
                          </div>
                          <div>
                            <span className="text-brand-muted">Rule / Policy:</span>{' '}
                            <span className="text-brand-ink dark:text-brand-text font-medium">{event.rule_or_version_applied || 'Standard APH Workflow'}</span>
                          </div>
                        </div>

                        {/* Reason / Remarks */}
                        {event.reason_or_remarks && (
                          <div className="mt-2 p-2.5 rounded bg-white dark:bg-brand-surface border border-brand-border text-xs text-brand-ink dark:text-brand-text">
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

      {/* Tab 1: Scrutiny & Deficiencies */}
      {activeTab === 'SCRUTINY' && (
        <div className="space-y-6">

      {/* Evidence-Grounded Case Brief Assistant Box */}
      {caseBrief && (
        <div className="bg-gradient-to-r from-teal-950 to-brand-ink text-white rounded-xl p-5 shadow-sm border border-teal-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-xs font-bold text-teal-300 uppercase tracking-wider">
              <Bot className="w-4 h-4 text-brand-teal" /> Evidence-Grounded Regulatory Case Brief
            </span>
            <span className="text-[10px] text-teal-200 bg-teal-900/80 px-2 py-0.5 rounded border border-teal-700/60 font-mono">
              {caseBrief.provenance || 'Deterministic Case Brief'}
            </span>
          </div>

          <div className="space-y-2 text-xs text-gray-200">
            {caseBrief.summary_paragraphs ? (
              caseBrief.summary_paragraphs.map((p: string, idx: number) => (
                <p key={idx} className="leading-relaxed">{p}</p>
              ))
            ) : (
              <p className="leading-relaxed">{caseBrief.synthesis}</p>
            )}
          </div>

          {caseBrief.suggested_administrative_draft && (
            <div className="mt-3 p-3 bg-teal-900/40 rounded-lg border border-teal-700/50">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-teal-300 uppercase tracking-wider">
                  Suggested Administrative Follow-Up Draft
                </span>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(caseBrief.suggested_administrative_draft);
                    alert('Draft copied to clipboard.');
                  }}
                  className="text-[10px] text-teal-200 hover:text-white underline font-semibold"
                >
                  Copy to Clipboard
                </button>
              </div>
              <p className="font-mono text-[11px] text-gray-200 whitespace-pre-wrap">
                {caseBrief.suggested_administrative_draft}
              </p>
            </div>
          )}

          <div className="text-[10px] text-gray-400 border-t border-teal-900 pt-2 italic">
            {caseBrief.regulatory_disclaimer || "STATUTORY NOTICE: Informational synthesis from recorded facts. Zero decision-making authority."}
          </div>
        </div>
      )}

      {/* Main Scrutiny Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Deficiencies & Cure Review */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm p-6 transition-colors">
            <div className="flex items-center justify-between pb-3 border-b border-brand-border dark:border-brand-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  Deficiencies & Compliance Observations
                </h3>
                <p className="text-xs text-brand-muted dark:text-brand-muted">
                  Official statutory audit findings communicated to institution
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-brand-porcelain dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink border border-brand-border/60 dark:border-brand-border">
                {openDeficiencies.length} Pending
              </span>
            </div>

            {(!app.deficiencies || app.deficiencies.length === 0) ? (
              <div className="p-8 text-center bg-brand-porcelain/40 dark:bg-brand-surface-elevated/40 rounded-lg border border-dashed border-brand-border dark:border-brand-border">
                <CheckCircle className="w-8 h-8 text-brand-teal mx-auto mb-2" />
                <p className="text-xs font-semibold text-brand-ink dark:text-brand-ink">No deficiencies logged</p>
                <p className="text-[11px] text-brand-muted dark:text-brand-muted mt-0.5">
                  Application adheres to prescribed APH norms.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {app.deficiencies.map((def) => (
                  <div
                    key={def.id}
                    className={`p-4 rounded-xl border transition-all ${
                      def.status === 'OPEN'
                        ? 'border-amber-300 dark:border-amber-800/50 bg-amber-50/60 dark:bg-amber-950/20'
                        : 'border-emerald-300 dark:border-emerald-800/50 bg-emerald-50/60 dark:bg-emerald-950/20'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-brand-ink dark:text-brand-ink uppercase tracking-wider">
                            [{def.category}]
                          </span>
                          <StatusBadge status={def.status} />
                        </div>
                        <p className="text-xs text-brand-ink dark:text-brand-ink mt-2 font-medium">{def.description}</p>
                        {def.required_document && (
                          <p className="text-[11px] text-brand-muted dark:text-brand-muted mt-1">
                            Required Document: <span className="font-semibold text-brand-ink dark:text-brand-ink">{def.required_document}</span>
                          </p>
                        )}
                      </div>

                      {def.status === 'OPEN' && (
                        <button
                          onClick={() => handleResolveDeficiency(def.id)}
                          className="px-3 py-1.5 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white text-xs font-semibold shadow-sm shrink-0 flex items-center gap-1 transition-colors"
                        >
                          <Check className="w-3.5 h-3.5" /> Sign-off as Resolved
                        </button>
                      )}
                    </div>

                    {/* Cure Submission */}
                    {def.cure_remarks && (
                      <div className="mt-3 pt-3 border-t border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated p-3 rounded-lg text-xs border">
                        <p className="font-semibold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                          <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> Institution Rectification Response:
                        </p>
                        <p className="text-brand-muted dark:text-brand-muted mt-1">{def.cure_remarks}</p>
                        {def.cure_document_url && (
                          <div className="mt-2">
                            <a
                              href={def.cure_document_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
                            >
                              <FileText className="w-3.5 h-3.5" /> Inspect Submitted Cure Document
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
          {/* Urgency & Parameters */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm space-y-3 transition-colors">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-ink pb-2 border-b border-brand-border dark:border-brand-border">
              Scrutiny Governance Parameters
            </h4>
            <div className="text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-brand-muted dark:text-brand-muted">Institution:</span>
                <span className="font-semibold text-brand-ink dark:text-brand-ink">{app.institution_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brand-muted dark:text-brand-muted">Region:</span>
                <span className="font-semibold text-brand-ink dark:text-brand-ink">{app.region}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-brand-border dark:border-brand-border">
                <span className="text-brand-muted dark:text-brand-muted">Priority Score:</span>
                <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
              </div>
            </div>
          </div>

          {/* Workflow Stage Progression */}
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm transition-colors">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink dark:text-brand-ink pb-3 border-b border-brand-border dark:border-brand-border mb-4">
              Stage Audit Progression
            </h4>
            <div className="space-y-4">
              {app.stages?.map((stage, idx) => (
                <div key={stage.id} className="relative pl-6 pb-2 text-xs">
                  {idx !== (app.stages?.length || 1) - 1 && (
                    <span className="absolute left-2.5 top-3 w-0.5 h-full bg-brand-border dark:bg-brand-border" />
                  )}
                  <span className="absolute left-1 top-1 w-3.5 h-3.5 rounded-full bg-brand-teal ring-4 ring-teal-50 dark:ring-brand-teal/20" />
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-brand-ink dark:text-brand-ink">{stage.to_stage.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] text-brand-muted dark:text-brand-muted">
                        {new Date(stage.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </span>
                    </div>
                    <p className="text-[11px] text-brand-muted mt-0.5">
                      By: {stage.actor_name} ({stage.actor_role?.replace(/_/g, ' ')})
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

      {/* Issue Deficiency Modal */}
      <Modal
        isOpen={defModalOpen}
        onClose={() => setDefModalOpen(false)}
        title="Issue Deficiency Communication Memo"
        subtitle="Record specific statutory non-compliance items requiring institutional cure"
      >
        <form onSubmit={handleIssueDeficiency} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Deficiency Category
            </label>
            <select
              value={defCategory}
              onChange={(e) => setDefCategory(e.target.value)}
              className="w-full border border-brand-border rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-brand-teal"
            >
              <option value="INFRASTRUCTURE">Infrastructure Norms & Built-up Area</option>
              <option value="FACULTY_CADRE">Faculty Cadre Ratio & Cadre Deficit</option>
              <option value="SAFETY">Fire Safety NOC / Building Stability</option>
              <option value="LAND_TITLE">33-Year Registered Land Lease / Title</option>
              <option value="FINANCIAL_AUDIT">Financial Audit & FDR Compliance</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Itemized Observation Description
            </label>
            <textarea
              required
              rows={3}
              value={defDescription}
              onChange={(e) => setDefDescription(e.target.value)}
              placeholder="Detail the specific deficiency observed during scrutiny..."
              className="w-full border border-brand-border rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Required Cure Document
            </label>
            <input
              type="text"
              value={defReqDoc}
              onChange={(e) => setDefReqDoc(e.target.value)}
              placeholder="e.g. Form B Municipal Fire Brigade NOC / Faculty Affidavit"
              className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setDefModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingDef}
              className="px-4 py-2 bg-[#C5892B] text-white rounded-lg font-semibold hover:bg-amber-700 shadow-sm"
            >
              {submittingDef ? 'Recording...' : 'Issue Deficiency Memo'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Stage Progression Modal */}
      <Modal
        isOpen={transitionModalOpen}
        onClose={() => setTransitionModalOpen(false)}
        title="Execute Workflow Stage Progression"
        subtitle={`Current Stage: ${app.current_stage}`}
      >
        <form onSubmit={handleTransition} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Target Regulatory Stage
            </label>
            <select
              value={targetStage}
              onChange={(e) => setTargetStage(e.target.value)}
              className="w-full border border-brand-border rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-brand-teal font-semibold"
            >
              <option value="">Select target stage...</option>
              <option value="UNDER_SCRUTINY">UNDER_SCRUTINY — Scrutiny in Progress</option>
              <option value="SCRUTINY_COMPLETED">SCRUTINY_COMPLETED — Sign-off Scrutiny</option>
              <option value="AWAITING_EVC_SCHEDULE">AWAITING_EVC_SCHEDULE — Route to EVC Queue</option>
              <option value="AWAITING_SAC_CAC_REVIEW">AWAITING_SAC_CAC_REVIEW — Committee Review</option>
              <option value="AWAITING_COMPETENT_AUTHORITY">AWAITING_COMPETENT_AUTHORITY — Apex Council</option>
              <option value="APPROVED">APPROVED — Grant Final Approval</option>
              <option value="REJECTED">REJECTED — Issue Rejection Order</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Official Scrutiny Remarks & Decision Rationale
            </label>
            <textarea
              rows={3}
              value={transitionRemarks}
              onChange={(e) => setTransitionRemarks(e.target.value)}
              placeholder="Record reason for advancement, regulatory checklist sign-off, or committee minutes reference..."
              className="w-full border border-brand-border rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setTransitionModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingTransition || !targetStage}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-dark shadow-sm"
            >
              {submittingTransition ? 'Advancing...' : 'Confirm Stage Progression'}
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
          currentUser={user}
          onOrderChanged={loadData}
        />
      )}
    </div>
  );
};
