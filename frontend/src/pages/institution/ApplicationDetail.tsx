import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock,
  Upload, Send, Bot, Shield, FileCheck
} from 'lucide-react';
import { api } from '../../api/client';
import { ApplicationDetailResponse } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';

export const ApplicationDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [app, setApp] = useState<ApplicationDetailResponse | null>(null);
  const [caseBrief, setCaseBrief] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [cureModalOpen, setCureModalOpen] = useState(false);
  const [selectedDeficiencyId, setSelectedDeficiencyId] = useState<number | null>(null);
  const [cureRemarks, setCureRemarks] = useState('');
  const [cureFileUrl, setCureFileUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resubmitting, setResubmitting] = useState(false);

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
      </div>

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
    </div>
  );
};
