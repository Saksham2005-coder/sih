import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock,
  Send, Bot, Check, ShieldCheck, ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { ApplicationDetailResponse } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';

export const OfficerApplicationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user, activeRole } = useAuth();
  const [app, setApp] = useState<ApplicationDetailResponse | null>(null);
  const [caseBrief, setCaseBrief] = useState<any | null>(null);
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

  const loadData = async () => {
    if (!id) return;
    try {
      const data = await api.getApplicationDetail(Number(id));
      setApp(data);
      const brief = await api.getCaseBrief(Number(id));
      setCaseBrief(brief);
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
            className="p-1.5 rounded-lg border border-brand-border bg-white hover:bg-gray-50 text-brand-muted"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-brand-ink">{app.application_number}</h1>
              <StatusBadge status={app.current_stage} />
            </div>
            <p className="text-xs text-brand-muted">
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
        </div>
      </div>

      {/* Case Brief Assistant Box */}
      {caseBrief && (
        <div className="bg-gradient-to-r from-teal-900 to-brand-ink text-white rounded-xl p-5 shadow-sm border border-teal-800">
          <div className="flex items-center justify-between mb-2">
            <span className="flex items-center gap-2 text-xs font-bold text-teal-300 uppercase tracking-wider">
              <Bot className="w-4 h-4" /> Explainable Regulatory Synthesis
            </span>
            <span className="text-[10px] text-gray-300 bg-teal-800/60 px-2 py-0.5 rounded border border-teal-600/40">
              Deterministic Case Brief
            </span>
          </div>
          <p className="text-xs leading-relaxed text-gray-100">{caseBrief.synthesis}</p>
        </div>
      )}

      {/* Main Scrutiny Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Deficiencies & Cure Review */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-brand-border shadow-sm p-6">
            <div className="flex items-center justify-between pb-3 border-b border-brand-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#C5892B]" />
                  Deficiencies & Compliance Observations
                </h3>
                <p className="text-xs text-brand-muted">
                  Official statutory audit findings communicated to institution
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-gray-100 text-brand-ink">
                {openDeficiencies.length} Pending
              </span>
            </div>

            {(!app.deficiencies || app.deficiencies.length === 0) ? (
              <div className="p-8 text-center bg-brand-porcelain/40 rounded-lg border border-dashed border-brand-border">
                <CheckCircle className="w-8 h-8 text-brand-teal mx-auto mb-2" />
                <p className="text-xs font-semibold text-brand-ink">No deficiencies logged</p>
                <p className="text-[11px] text-brand-muted mt-0.5">
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
                        ? 'border-amber-200 bg-amber-50/20'
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
                            Required Document: <span className="font-semibold text-brand-ink">{def.required_document}</span>
                          </p>
                        )}
                      </div>

                      {def.status === 'OPEN' && (
                        <button
                          onClick={() => handleResolveDeficiency(def.id)}
                          className="px-3 py-1.5 rounded-lg bg-brand-teal hover:bg-brand-teal-dark text-white text-xs font-semibold shadow-sm shrink-0 flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" /> Sign-off as Resolved
                        </button>
                      )}
                    </div>

                    {/* Cure Submission */}
                    {def.cure_remarks && (
                      <div className="mt-3 pt-3 border-t border-gray-200 bg-white/70 p-3 rounded-lg text-xs">
                        <p className="font-semibold text-teal-800 flex items-center gap-1.5">
                          <CheckCircle className="w-4 h-4 text-brand-teal" /> Institution Rectification Response:
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
          <div className="bg-white rounded-xl border border-brand-border p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink pb-2 border-b border-brand-border">
              Scrutiny Governance Parameters
            </h4>
            <div className="text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-brand-muted">Institution:</span>
                <span className="font-semibold text-brand-ink">{app.institution_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-brand-muted">Region:</span>
                <span className="font-semibold text-brand-ink">{app.region}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-brand-border">
                <span className="text-brand-muted">Priority Score:</span>
                <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
              </div>
            </div>
          </div>

          {/* Workflow Stage Progression */}
          <div className="bg-white rounded-xl border border-brand-border p-5 shadow-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink pb-3 border-b border-brand-border mb-4">
              Stage Audit Progression
            </h4>
            <div className="space-y-4">
              {app.stages?.map((stage, idx) => (
                <div key={stage.id} className="relative pl-6 pb-2 text-xs">
                  {idx !== (app.stages?.length || 1) - 1 && (
                    <span className="absolute left-2.5 top-3 w-0.5 h-full bg-brand-border" />
                  )}
                  <span className="absolute left-1 top-1 w-3.5 h-3.5 rounded-full bg-brand-teal ring-4 ring-teal-50" />
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
    </div>
  );
};
