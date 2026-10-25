import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users, CheckCircle2, AlertTriangle, FileText,
  Compass, ArrowRight, Eye, RefreshCw, Send, ShieldCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Application, EVCInspection } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const CommitteeMemberWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [assignedApps, setAssignedApps] = useState<Application[]>([]);
  const [inspections, setInspections] = useState<EVCInspection[]>([]);
  const [loading, setLoading] = useState(true);

  // Review modal state
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [recommendationDecision, setRecommendationDecision] = useState<'AWAITING_COMPETENT_AUTHORITY' | 'DEFICIENCY_COMMUNICATED'>('AWAITING_COMPETENT_AUTHORITY');
  const [hearingRemarks, setHearingRemarks] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [apps, evcQueue] = await Promise.all([
        api.getApplications(),
        api.getEVCQueue(),
      ]);
      setAssignedApps(apps);
      setInspections(evcQueue);
    } catch (err) {
      console.error('Failed to load committee member data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApp) return;
    setSubmittingReview(true);
    try {
      await api.transitionApplication(selectedApp.id, {
        to_stage: recommendationDecision,
        remarks: hearingRemarks || `Standing Hearing Committee (SAC/CAC) review conducted by ${user?.full_name}. Recommendation: ${recommendationDecision}.`,
      });
      setSelectedApp(null);
      setHearingRemarks('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Review submission failed');
    } finally {
      setSubmittingReview(false);
    }
  };

  const hearingQueue = assignedApps.filter(a => a.current_stage === 'AWAITING_SAC_CAC_REVIEW');
  const assignedInspections = inspections.filter(i =>
    i.convener_name?.includes(user?.full_name || '') ||
    i.coordinator_id === user?.id ||
    i.status === 'REPORT_SUBMITTED'
  );

  return (
    <div className="space-y-6">
      {/* Workspace Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              STANDING HEARING COMMITTEE (SAC / CAC)
            </span>
            <span className="text-xs text-brand-muted">
              Role: <strong>Committee Review Panelist & Expert</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Committee Review & Hearing Command
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Member: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (COMMITTEE MEMBER) • Standing Scrutiny, EVC Panels & Hearing Observations
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Assigned Docket
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Cases Awaiting Committee Hearing"
          value={hearingQueue.length}
          subtext="AWAITING_SAC_CAC_REVIEW stage"
          icon={<Users size={18} />}
          variant={hearingQueue.length > 0 ? 'amber' : 'default'}
        />
        <StatCard
          title="Assigned EVC Inspections"
          value={assignedInspections.length}
          subtext="Convener or Expert panelist role"
          icon={<Compass size={18} />}
        />
        <StatCard
          title="Assigned Docket Cases"
          value={assignedApps.length}
          subtext="Permitted hearing purview"
          icon={<FileText size={18} />}
        />
        <StatCard
          title="Observations Submitted"
          value={inspections.filter(i => i.recommendation).length}
          subtext="EVC & hearing sign-offs"
          icon={<CheckCircle2 size={18} />}
        />
      </div>

      {/* Primary Hearing Queue */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Standing Hearing Committee (SAC/CAC) Review Queue</h3>
            <p className="text-xs text-brand-muted">Applications with completed regional scrutiny and EVC inspections awaiting formal committee recommendation</p>
          </div>
          <span className="text-xs font-semibold text-brand-teal bg-teal-50 dark:bg-teal-950/80 px-2.5 py-1 rounded-full border border-teal-200 dark:border-teal-700/80">
            {hearingQueue.length} Pending Hearing
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Application Type</th>
                <th className="px-6 py-3.5">Current Stage</th>
                <th className="px-6 py-3.5 text-right">Committee Review Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {hearingQueue.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-brand-muted">
                    No applications currently awaiting Standing Committee hearing.
                  </td>
                </tr>
              ) : (
                hearingQueue.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                    <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                      <Link to={`/officer/applications/${app.id}`} className="hover:text-brand-teal transition-colors">
                        {app.application_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{app.institution_name}</p>
                      <span className="text-[10px] text-brand-muted">{app.region || 'Western'} Region</span>
                    </td>
                    <td className="px-6 py-4 font-medium text-brand-ink">
                      {app.application_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.current_stage} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedApp(app)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                      >
                        <Send className="w-3.5 h-3.5" /> Submit Hearing Findings
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assigned EVC Inspections */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Assigned EVC Inspection Visits</h3>
            <p className="text-xs text-brand-muted">Panels where this committee member is designated as Convener or Subject Expert</p>
          </div>
          <Link
            to="/officer/evc"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            All EVC Inspections <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Convener & Expert</th>
                <th className="px-6 py-3.5">Inspection Status</th>
                <th className="px-6 py-3.5 text-right">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {assignedInspections.map((insp) => (
                <tr key={insp.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                    {insp.application_number}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.institution_name}</p>
                    <span className="text-[10px] text-brand-muted">{insp.region}</span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.convener_name || 'Convener Unassigned'}</p>
                    <p className="text-[10px] text-brand-muted">{insp.expert_member_name}</p>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={insp.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    {insp.recommendation ? (
                      <span className="text-xs font-bold text-brand-teal">
                        {insp.recommendation.replace(/_/g, ' ')}
                      </span>
                    ) : (
                      <Link
                        to="/officer/evc"
                        className="text-xs font-semibold text-brand-teal hover:underline"
                      >
                        File Inspection Report
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Submit Committee Review Recommendation */}
      {selectedApp && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedApp(null)}
          title={`Standing Committee Hearing Review: ${selectedApp.application_number}`}
        >
          <form onSubmit={handleExecuteReview} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Institution: {selectedApp.institution_name}</p>
              <p className="text-brand-muted">Application Type: {selectedApp.application_type.replace(/_/g, ' ')}</p>
              <p className="font-mono text-brand-teal">Current Stage: {selectedApp.current_stage}</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1.5">Committee Statutory Recommendation</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRecommendationDecision('AWAITING_COMPETENT_AUTHORITY')}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    recommendationDecision === 'AWAITING_COMPETENT_AUTHORITY'
                      ? 'border-brand-teal bg-teal-50/50 dark:bg-teal-950/40 ring-2 ring-brand-teal'
                      : 'border-brand-border hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <p className="font-bold text-brand-ink flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-brand-teal" /> Forward for Approval
                  </p>
                  <p className="text-[10px] text-brand-muted mt-1">
                    Recommend to Competent Authority for issuance of statutory approval order.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setRecommendationDecision('DEFICIENCY_COMMUNICATED')}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    recommendationDecision === 'DEFICIENCY_COMMUNICATED'
                      ? 'border-[#99630D] bg-amber-50/50 dark:bg-amber-950/40 ring-2 ring-[#99630D]'
                      : 'border-brand-border hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <p className="font-bold text-brand-ink flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-[#99630D] dark:text-amber-400" /> Return for Rectification
                  </p>
                  <p className="text-[10px] text-brand-muted mt-1">
                    Communicate deficiencies observed during committee hearing.
                  </p>
                </button>
              </div>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Formal Committee Hearing Observations & Rationale</label>
              <textarea
                rows={4}
                required
                value={hearingRemarks}
                onChange={(e) => setHearingRemarks(e.target.value)}
                placeholder="Enter itemized committee observations, hearing minutes, and unanimous recommendations..."
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white dark:bg-brand-surface-secondary text-brand-ink"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedApp(null)}
                className="px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-100 dark:hover:bg-brand-surface-elevated font-semibold transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingReview}
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm transition-colors duration-150"
              >
                {submittingReview ? 'Recording...' : 'Submit Committee Finding'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
export default CommitteeMemberWorkspace;
