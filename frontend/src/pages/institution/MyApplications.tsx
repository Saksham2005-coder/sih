import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, FileText, ArrowRight } from 'lucide-react';
import { api } from '../../api/client';
import { Application } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';

export const MyApplications: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [appType, setAppType] = useState('EOA_ANNUAL');
  const [academicYear, setAcademicYear] = useState('2026-2027');
  const [submitting, setSubmitting] = useState(false);

  const fetchApps = async () => {
    try {
      const data = await api.getApplications({
        stage: stageFilter || undefined,
        search: search || undefined,
      });
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, [stageFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchApps();
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const templateMap: Record<string, { template: string; evc: boolean }> = {
        EOA_ANNUAL: { template: 'ONLY_SCRUTINY', evc: false },
        NEW_INSTITUTION: { template: 'SCRUTINY_EVC', evc: true },
        INTAKE_VARIATION: { template: 'EVC_SAC_SHC', evc: true },
        CLOSURE_PROGRAM: { template: 'ONLY_EVC', evc: true },
      };
      const routeConfig = templateMap[appType] || { template: appType, evc: false };

      await api.createApplication({
        application_type: appType,
        academic_year: academicYear,
        workflow_template_code: routeConfig.template,
        evc_required: routeConfig.evc,
      });
      setIsModalOpen(false);
      fetchApps();
    } catch (err: any) {
      alert(err.message || 'Failed to file application');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-ink">My Regulatory Applications</h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Manage approvals, Extension of Approval (EoA), and intake variations
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-dark text-white text-xs font-semibold shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" /> File New Application
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white dark:bg-brand-surface p-4 rounded-xl border border-brand-border dark:border-brand-border shadow-sm flex flex-col sm:flex-row gap-3 justify-between items-center transition-colors">
        <form onSubmit={handleSearch} className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-brand-muted dark:text-brand-muted" />
          <input
            type="text"
            placeholder="Search by application number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-brand-teal"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-brand-muted dark:text-brand-muted shrink-0" />
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal w-full sm:w-auto"
          >
            <option value="">All Workflow Stages</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="UNDER_SCRUTINY">Under Scrutiny</option>
            <option value="DEFICIENCY_COMMUNICATED">Deficiency Cure Required</option>
            <option value="RESUBMITTED">Resubmitted</option>
            <option value="AWAITING_EVC_SCHEDULE">Awaiting EVC</option>
            <option value="EVC_SCHEDULED">EVC Scheduled</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border dark:border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Category</th>
                <th className="px-6 py-3.5">Academic Cycle</th>
                <th className="px-6 py-3.5">Workflow Stage</th>
                <th className="px-6 py-3.5">Operational Urgency</th>
                <th className="px-6 py-3.5">Deficiencies</th>
                <th className="px-6 py-3.5">Submission Date</th>
                <th className="px-6 py-3.5 text-right">Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 dark:divide-brand-border">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-brand-muted dark:text-brand-muted">
                    No matching applications found.
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-brand-porcelain/50 dark:hover:bg-brand-surface-elevated/50 transition-colors">
                    <td className="px-6 py-4 font-semibold text-brand-ink dark:text-brand-ink">
                      {app.application_number}
                    </td>
                    <td className="px-6 py-4 text-brand-muted dark:text-brand-muted">
                      {app.application_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 text-brand-muted dark:text-brand-muted">{app.academic_year}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.current_stage} />
                    </td>
                    <td className="px-6 py-4">
                      <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
                    </td>
                    <td className="px-6 py-4">
                      {app.open_deficiencies_count > 0 ? (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800/40">
                          {app.open_deficiencies_count} Open
                        </span>
                      ) : (
                        <span className="text-emerald-700 dark:text-emerald-400 text-xs font-medium">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-brand-muted dark:text-brand-muted">
                      {new Date(app.submitted_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/institution/applications/${app.id}`}
                        className="text-xs font-semibold text-brand-teal hover:underline inline-flex items-center gap-1"
                      >
                        Inspect <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Application Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="File Regulatory Application"
        subtitle="Submit statutory application under AICTE Approval Process Handbook (APH) guidelines"
      >
        <form onSubmit={handleCreate} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Application Category
            </label>
            <select
              value={appType}
              onChange={(e) => setAppType(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-brand-teal"
            >
              <option value="EOA_ANNUAL">Extension of Approval (EoA) — Annual Cycle [Route: Only Scrutiny]</option>
              <option value="NEW_INSTITUTION">Establishment of New Technical Program / Institution [Route: Scrutiny + EVC]</option>
              <option value="INTAKE_VARIATION">Increase in Intake / Emerging Areas [Route: EVC + SAC/SHC Hearing]</option>
              <option value="CLOSURE_PROGRAM">Closure of Program / Relocation [Route: Only EVC]</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Academic Cycle
            </label>
            <input
              type="text"
              value={academicYear}
              disabled
              className="w-full border border-brand-border dark:border-brand-border rounded-lg px-3 py-2 text-xs bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted"
            />
          </div>

          <div className="p-3 bg-teal-50 dark:bg-brand-teal/15 border border-teal-200 dark:border-brand-teal/30 rounded-lg text-teal-900 dark:text-teal-200 text-[11px]">
            <p className="font-semibold">Statutory Compliance Note:</p>
            <p className="mt-0.5">
              Filing this application will initialize the regulatory SLA clock and assign it to the Regional Office for scrutiny. Ensure land lease and safety certificates are active.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 border border-brand-border dark:border-brand-border rounded-lg text-brand-ink dark:text-brand-ink font-semibold hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-hover shadow-sm transition-colors"
            >
              {submitting ? 'Submitting...' : 'Confirm & Submit Application'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
