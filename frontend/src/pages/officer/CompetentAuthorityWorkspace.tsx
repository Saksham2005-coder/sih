import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Award, CheckCircle2, XCircle, AlertTriangle, FileText,
  ShieldCheck, RefreshCw, ArrowRight, Gavel, FileCheck2, Compass
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Application, CommandCentreData } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const CompetentAuthorityWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<CommandCentreData | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  // Decision Modal State
  const [decisionApp, setDecisionApp] = useState<Application | null>(null);
  const [orderType, setOrderType] = useState<'APPROVED' | 'REJECTED' | 'DEFICIENCY_COMMUNICATED'>('APPROVED');
  const [orderRemarks, setOrderRemarks] = useState('');
  const [executingOrder, setExecutingOrder] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ccRes, appList] = await Promise.all([
        api.getCommandCentre(),
        api.getApplications(),
      ]);
      setData(ccRes);
      setApplications(appList);
    } catch (err) {
      console.error('Failed to load competent authority data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!decisionApp) return;
    setExecutingOrder(true);
    try {
      await api.transitionApplication(decisionApp.id, {
        to_stage: orderType,
        remarks: orderRemarks || `Official statutory order issued by Competent Authority (${user?.full_name}): ${orderType}.`,
      });
      setDecisionApp(null);
      setOrderRemarks('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to issue statutory order');
    } finally {
      setExecutingOrder(false);
    }
  };

  const decisionQueue = applications.filter(a => a.current_stage === 'AWAITING_COMPETENT_AUTHORITY');
  const approvedApps = applications.filter(a => a.current_stage === 'APPROVED');
  const rejectedApps = applications.filter(a => a.current_stage === 'REJECTED');

  return (
    <div className="space-y-6">
      {/* Competent Authority Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-600 text-white">
              AICTE COMPETENT AUTHORITY
            </span>
            <span className="text-xs text-brand-muted">
              Office of the Member Secretary & Apex Council
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Statutory Decision Review & Order Issuance Command
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Authority: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (COMPETENT AUTHORITY) • Final Approval & Rejection Orders
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Decision Queue
        </button>
      </div>

      {/* Decision Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Cases Awaiting Decision"
          value={decisionQueue.length}
          subtext="All prerequisites completed"
          icon={<Gavel size={18} />}
          variant={decisionQueue.length > 0 ? 'amber' : 'default'}
        />
        <StatCard
          title="Statutory Approvals Granted"
          value={approvedApps.length}
          subtext="Orders issued in 2026-2027 cycle"
          icon={<CheckCircle2 size={18} />}
        />
        <StatCard
          title="Statutory Rejections"
          value={rejectedApps.length}
          subtext="Final rejection orders recorded"
          icon={<XCircle size={18} />}
          variant={rejectedApps.length > 0 ? 'red' : 'default'}
        />
        <StatCard
          title="Council Escalations (L3)"
          value={data?.summary?.active_escalations ?? 0}
          subtext="High-level matters referred to Council"
          icon={<Award size={18} />}
        />
      </div>

      {/* Primary Section: Cases Awaiting Competent Authority Decision */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Statutory Decision Queue (Cases Awaiting Final Order)</h3>
            <p className="text-xs text-brand-muted">Applications with verified scrutiny, EVC panel clearance, and Standing Committee recommendations</p>
          </div>
          <span className="text-xs font-bold text-[#99630D] dark:text-amber-200 bg-amber-50 dark:bg-amber-950/80 px-2.5 py-1 rounded-full border border-amber-300 dark:border-amber-700/80">
            {decisionQueue.length} Pending Statutory Order
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Application Type</th>
                <th className="px-6 py-3.5">Prerequisites Audited</th>
                <th className="px-6 py-3.5 text-right">Statutory Order Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {decisionQueue.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-brand-muted">
                    No applications currently awaiting Competent Authority statutory decision.
                  </td>
                </tr>
              ) : (
                decisionQueue.map((app) => (
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
                      <div className="space-y-1">
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-800 dark:text-emerald-200 bg-emerald-50 dark:bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-700/80">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> Scrutiny Verified
                        </span>
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-800 dark:text-emerald-200 bg-emerald-50 dark:bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-300 dark:border-emerald-700/80 ml-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> Committee Recommended
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setDecisionApp(app);
                          setOrderType('APPROVED');
                          setOrderRemarks(`Statutory approval order granted for Academic Year 2026-2027 by Member Secretary / Competent Authority. All APH norms verified.`);
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                      >
                        <Gavel className="w-3.5 h-3.5" /> Adjudicate & Issue Order
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Secondary Section: Historical Decisions in Current Cycle */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Statutory Orders Issued in Academic Cycle 2026-2027</h3>
            <p className="text-xs text-brand-muted">Signed statutory approval and rejection decisions on record</p>
          </div>
          <Link
            to="/officer/applications"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            All Historical Orders <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Application Type</th>
                <th className="px-6 py-3.5">Final Outcome</th>
                <th className="px-6 py-3.5 text-right">View Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {[...approvedApps, ...rejectedApps].slice(0, 5).map((app) => (
                <tr key={app.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                    {app.application_number}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{app.institution_name}</p>
                    <span className="text-[10px] text-brand-muted">{app.region}</span>
                  </td>
                  <td className="px-6 py-4 font-medium text-brand-ink">
                    {app.application_type.replace(/_/g, ' ')}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={app.current_stage} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/officer/applications/${app.id}`}
                      className="text-xs font-semibold text-brand-teal hover:underline transition-colors"
                    >
                      Inspect Order Dossier
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Adjudicate & Issue Order */}
      {decisionApp && (
        <Modal
          isOpen={true}
          onClose={() => setDecisionApp(null)}
          title={`Execute Statutory Order: ${decisionApp.application_number}`}
        >
          <form onSubmit={handleExecuteDecision} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Institution: {decisionApp.institution_name}</p>
              <p className="text-brand-muted">Type: {decisionApp.application_type.replace(/_/g, ' ')} • {decisionApp.academic_year}</p>
              <p className="font-mono text-[#99630D] dark:text-amber-400 font-semibold">Authority Mandate: Final Council Order (Irrevocable)</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1.5">Select Statutory Determination</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setOrderType('APPROVED');
                    setOrderRemarks(`Statutory approval order granted for Academic Year 2026-2027 by Member Secretary / Competent Authority. All APH norms verified.`);
                  }}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    orderType === 'APPROVED'
                      ? 'border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/40 ring-2 ring-emerald-600'
                      : 'border-brand-border hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <p className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> Grant Approval
                  </p>
                  <p className="text-[10px] text-brand-muted mt-1">Issue official Extension of Approval / New Institute Order.</p>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setOrderType('REJECTED');
                    setOrderRemarks(`Statutory rejection order issued by Competent Authority due to non-fulfillment of mandatory regulatory norms.`);
                  }}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    orderType === 'REJECTED'
                      ? 'border-rose-600 bg-rose-50/50 dark:bg-red-950/40 ring-2 ring-rose-600'
                      : 'border-brand-border hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <p className="font-bold text-rose-800 dark:text-red-300 flex items-center gap-1">
                    <XCircle className="w-4 h-4 text-rose-600 dark:text-red-400" /> Formal Rejection
                  </p>
                  <p className="text-[10px] text-brand-muted mt-1">Refuse approval under statutory powers with documented reasons.</p>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setOrderType('DEFICIENCY_COMMUNICATED');
                    setOrderRemarks(`Returned by Competent Authority for critical compliance rectification.`);
                  }}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    orderType === 'DEFICIENCY_COMMUNICATED'
                      ? 'border-amber-600 bg-amber-50/50 dark:bg-amber-950/40 ring-2 ring-amber-600'
                      : 'border-brand-border hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <p className="font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" /> Return for Cure
                  </p>
                  <p className="text-[10px] text-brand-muted mt-1">Return to institution for mandatory deficiency rectification.</p>
                </button>
              </div>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Official Statutory Order Text & Gazette Remarks</label>
              <textarea
                rows={4}
                required
                value={orderRemarks}
                onChange={(e) => setOrderRemarks(e.target.value)}
                placeholder="Enter official statutory order text, gazette notification remarks, and approved intake capacity..."
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white dark:bg-brand-surface-secondary text-brand-ink"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDecisionApp(null)}
                className="px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-100 dark:hover:bg-brand-surface-elevated font-semibold transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={executingOrder}
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm transition-colors duration-150"
              >
                {executingOrder ? 'Executing Statutory Order...' : 'Sign & Issue Statutory Order'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
export default CompetentAuthorityWorkspace;
