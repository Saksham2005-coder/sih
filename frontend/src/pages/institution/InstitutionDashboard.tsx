import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, AlertTriangle, CheckSquare, Clock, ArrowRight, ShieldCheck, Calendar } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Application, ComplianceUndertaking, DocumentRecord } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { StatCard } from '../../components/common/StatCard';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { ComplianceOfficerWorkspace } from './ComplianceOfficerWorkspace';

export const InstitutionDashboard: React.FC = () => {
  const { user, isComplianceOfficer } = useAuth();

  if (isComplianceOfficer) {
    return <ComplianceOfficerWorkspace />;
  }

  const [applications, setApplications] = useState<Application[]>([]);
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [apps, under, docs] = await Promise.all([
          api.getApplications(),
          api.getUndertakings(),
          api.getDocuments(),
        ]);
        setApplications(apps);
        setUndertakings(under);
        setDocuments(docs);
      } catch (err) {
        console.error('Failed to load institution dashboard data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalDeficiencies = applications.reduce((acc, app) => acc + (app.open_deficiencies_count || 0), 0);
  const urgentUndertakings = undertakings.filter(u => u.status === 'OVERDUE' || u.status === 'DUE_SOON').length;
  const expiringDocs = documents.filter(d => d.status === 'EXPIRING_SOON' || d.status === 'EXPIRED').length;

  const deficientApp = applications.find(a => a.current_stage === 'DEFICIENCY_COMMUNICATED');

  return (
    <div className="space-y-6">
      {/* Institution Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 dark:bg-[#143633] text-brand-teal dark:text-[#39C6B4] border border-teal-300 dark:border-[#225650]">
              AICTE APPROVED
            </span>
            <span className="text-xs text-brand-text-muted">PID: {user?.institution_id === 2 ? '1-7782104' : '1-3324901'}</span>
          </div>
          <h1 className="text-xl font-bold text-brand-text-primary mt-1">
            {user?.institution_name || 'Technical Institution Workspace'}
          </h1>
          <p className="text-xs text-brand-text-secondary mt-0.5">
            {user?.region || (user?.institution_id === 2 ? 'Northern' : 'Western')} Region • Academic Year 2026-2027 Regulatory Filing Cycle
          </p>
        </div>

        <Link
          to="/institution/applications"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-action hover:bg-brand-action-hover text-white text-xs font-semibold shadow-sm transition-colors duration-150"
        >
          <FileText className="w-4 h-4" /> View My Applications
        </Link>
      </div>

      {/* Critical Action Banner if Deficiency Communicated */}
      {deficientApp && (
        <div className="bg-amber-50 dark:bg-[#352A18] border border-amber-300 dark:border-[#5C4520] rounded-xl p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-100 dark:bg-[#483318] rounded-lg text-[#99630D] dark:text-[#F2C96D] shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-brand-text-primary">
                  Statutory Deficiency Cure Required — Application {deficientApp.application_number}
                </h4>
                <p className="text-xs text-brand-text-secondary mt-1">
                  Regional Officer has communicated {deficientApp.open_deficiencies_count} itemized deficiencies. Please review the deficiency memo and upload cure documentation within the statutory cure window.
                </p>
              </div>
            </div>

            <Link
              to={`/institution/applications/${deficientApp.id}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#99630D] hover:bg-amber-800 dark:bg-[#C5892B] dark:hover:bg-[#A8721F] text-white text-xs font-semibold shadow-sm shrink-0 transition-colors duration-150"
            >
              Cure & Resubmit <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Operational Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Applications"
          value={applications.length}
          subtext="Under statutory review"
          icon={<FileText className="w-5 h-5" />}
        />
        <StatCard
          title="Open Deficiencies"
          value={totalDeficiencies}
          subtext="Requiring institutional cure"
          variant={totalDeficiencies > 0 ? 'amber' : 'default'}
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <StatCard
          title="Compliance Undertakings"
          value={urgentUndertakings}
          subtext="Due soon or overdue"
          variant={urgentUndertakings > 0 ? 'red' : 'default'}
          icon={<CheckSquare className="w-5 h-5" />}
        />
        <StatCard
          title="Expiring Documents"
          value={expiringDocs}
          subtext="Land deed / Fire NOC"
          variant={expiringDocs > 0 ? 'amber' : 'default'}
          icon={<Clock className="w-5 h-5" />}
        />
      </div>

      {/* Applications Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Regulatory Filings & Progress</h3>
            <p className="text-xs text-brand-muted">Current academic cycle application stages</p>
          </div>
          <Link
            to="/institution/applications"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            All Applications <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3">Application Number</th>
                <th className="px-6 py-3">Type</th>
                <th className="px-6 py-3">Current Stage</th>
                <th className="px-6 py-3">Priority Urgency</th>
                <th className="px-6 py-3">Deficiencies</th>
                <th className="px-6 py-3">Last Updated</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-brand-muted">
                    No active regulatory applications found.
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                    <td className="px-6 py-4 font-semibold text-brand-ink">
                      {app.application_number}
                    </td>
                    <td className="px-6 py-4 text-brand-muted font-medium">
                      {app.application_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.current_stage} />
                    </td>
                    <td className="px-6 py-4">
                      <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
                    </td>
                    <td className="px-6 py-4">
                      {app.open_deficiencies_count > 0 ? (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 dark:bg-[#352A18] text-[#99630D] dark:text-[#F2C96D] border border-amber-300 dark:border-[#5C4520]">
                          {app.open_deficiencies_count} Open
                        </span>
                      ) : (
                        <span className="text-teal-700 dark:text-[#39C6B4] text-xs font-semibold">Clear</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-brand-muted">
                      {new Date(app.updated_at).toLocaleDateString('en-IN', {
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
                        Dossier <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Compliance Passport Preview Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Urgent Undertakings */}
        <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-brand-border mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
              <CheckSquare className="w-4 h-4 text-brand-teal" />
              Compliance Passport Undertakings
            </h4>
            <Link to="/institution/compliance" className="text-xs font-semibold text-brand-teal hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {undertakings.slice(0, 3).map((u) => (
              <div key={u.id} className="p-3 rounded-lg border border-brand-border bg-brand-porcelain/30 dark:bg-brand-surface-secondary/50 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-brand-ink line-clamp-1">{u.title}</p>
                  <p className="text-[11px] text-brand-muted mt-0.5">
                    Due: {new Date(u.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </p>
                </div>
                <StatusBadge status={u.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Document Validity Expiry */}
        <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-brand-border mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-[#C5892B] dark:text-amber-400" />
              Prescribed Document Validity & Renewals
            </h4>
            <Link to="/institution/documents" className="text-xs font-semibold text-brand-teal hover:underline">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {documents.slice(0, 3).map((d) => (
              <div key={d.id} className="p-3 rounded-lg border border-brand-border bg-brand-porcelain/30 dark:bg-brand-surface-secondary/50 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-brand-ink line-clamp-1">{d.title}</p>
                  <p className="text-[11px] text-brand-muted mt-0.5">
                    Expiry: {d.expiry_date ? new Date(d.expiry_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Continuous'}
                  </p>
                </div>
                <StatusBadge status={d.status} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
