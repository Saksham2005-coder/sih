import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, AlertTriangle, Compass, CheckCircle2, ShieldAlert,
  BarChart3, RefreshCw, ArrowRight, Play, Clock, AlertOctagon,
  TrendingUp, Activity, CheckSquare, Layers, Eye
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { CommandCentreData, PriorityActionItem } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';

export const OfficerDashboard: React.FC = () => {
  const { user, activeRole } = useAuth();
  const [data, setData] = useState<CommandCentreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<PriorityActionItem | null>(null);

  const loadData = async () => {
    try {
      const res = await api.getCommandCentre();
      setData(res);
    } catch (err) {
      console.error('Failed to load command centre data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.runDeadlineScan();
      setScanResult(
        `Scan Complete: ${res.scanned_entities} scanned, ${res.reminders_created} reminders, ${res.escalations_created} escalations, ${res.duplicates_prevented} duplicate triggers prevented (${res.execution_time_ms}ms).`
      );
      loadData();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const summary = data?.summary;
  const bottlenecks = data?.bottlenecks;

  return (
    <div className="space-y-6">
      {/* Officer Command Banner */}
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              AICTE REGULATORY COMMAND CENTRE
            </span>
            <span className="text-xs text-brand-muted">
              Scope: <strong className="text-brand-ink">{data?.jurisdiction || (user?.region ? `${user.region} Region` : 'National Apex')}</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Operational Regulatory Command Centre
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Persona: <span className="font-semibold text-brand-teal">{activeRole?.replace(/_/g, ' ')}</span> • Live Case Routing & Statutory Oversight
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={handleRunScan}
            disabled={scanning}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-ink text-white text-xs font-semibold hover:bg-gray-800 shadow-sm transition-colors"
          >
            <Play className={`w-3.5 h-3.5 text-brand-teal ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scanning SLAs...' : 'Run Deadline Scan'}
          </button>
        </div>
      </div>

      {/* Deadline Scan Result Banner */}
      {scanResult && (
        <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg text-xs text-teal-800 font-medium flex items-center justify-between">
          <span>{scanResult}</span>
          <button onClick={() => setScanResult(null)} className="text-teal-900 font-bold ml-2">✕</button>
        </div>
      )}

      {/* Operational Reconciled Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Applications"
          value={summary?.total_applications || 0}
          subtext="Under active regulatory purview"
          icon={<FileText className="w-5 h-5" />}
        />
        <StatCard
          title="Pending Scrutiny"
          value={summary?.pending_scrutiny || 0}
          subtext="Submitted or under review"
          variant={(summary?.pending_scrutiny || 0) > 0 ? 'amber' : 'default'}
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <StatCard
          title="Deficiency Cure Window"
          value={summary?.deficiency_cure_required || 0}
          subtext="Returned to institution"
          variant="amber"
          icon={<AlertTriangle className="w-5 h-5" />}
        />
        <StatCard
          title="Awaiting EVC"
          value={(summary?.awaiting_evc || 0) + (summary?.evc_scheduled || 0)}
          subtext={`${summary?.awaiting_evc || 0} unscheduled roster items`}
          icon={<Compass className="w-5 h-5" />}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Final Approved"
          value={summary?.approved || 0}
          subtext="Statutory Approval Orders issued"
          variant="teal"
          icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
        />
        <StatCard
          title="Active SLA Escalations"
          value={summary?.active_escalations || 0}
          subtext="Tier-1 / Tier-2 SLA breaches"
          variant={(summary?.active_escalations || 0) > 0 ? 'red' : 'default'}
          icon={<ShieldAlert className="w-5 h-5 text-[#B9474F]" />}
        />
        <StatCard
          title="Overdue Compliance"
          value={summary?.overdue_undertakings || 0}
          subtext="Undertakings past SLA"
          variant={(summary?.overdue_undertakings || 0) > 0 ? 'red' : 'default'}
          icon={<AlertTriangle className="w-5 h-5 text-[#B9474F]" />}
        />
      </div>

      {/* Workload & Bottleneck Analysis Section */}
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-brand-border mb-4">
          <div>
            <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-teal" /> Workload & Regulatory Bottleneck Intelligence
            </h3>
            <p className="text-xs text-brand-muted">
              Live indicators identifying stage accumulation, verification queues, and inspection delays
            </p>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-brand-ink border border-gray-200">
            Database Derived
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-brand-porcelain/60 border border-brand-border">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted">
              Repeated Deficiency Loops
            </span>
            <p className="text-xl font-bold text-brand-ink mt-1">
              {bottlenecks?.repeated_returns_count || 0}
            </p>
            <p className="text-[11px] text-brand-muted mt-0.5">
              Cases returned &gt; 1 time for rectification
            </p>
          </div>

          <div className="p-4 rounded-lg bg-brand-porcelain/60 border border-brand-border">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted">
              Undertaking Verification Backlog
            </span>
            <p className="text-xl font-bold text-[#C5892B] mt-1">
              {bottlenecks?.verification_backlog_undertakings || 0}
            </p>
            <p className="text-[11px] text-brand-muted mt-0.5">
              Compliance proofs awaiting officer review
            </p>
          </div>

          <div className="p-4 rounded-lg bg-brand-porcelain/60 border border-brand-border">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted">
              Document Renewal Queue
            </span>
            <p className="text-xl font-bold text-brand-ink mt-1">
              {bottlenecks?.verification_backlog_documents || 0}
            </p>
            <p className="text-[11px] text-brand-muted mt-0.5">
              Renewed leases/NOCs awaiting sign-off
            </p>
          </div>

          <div className="p-4 rounded-lg bg-brand-porcelain/60 border border-brand-border">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted">
              Average Stage Ageing
            </span>
            <p className="text-xl font-bold text-brand-teal mt-1">
              {bottlenecks?.average_stage_ageing_days || 0} Days
            </p>
            <p className="text-[11px] text-brand-muted mt-0.5">
              Mean pendency across active applications
            </p>
          </div>
        </div>
      </div>

      {/* Priority Action Queue */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">
              Priority Case Action Queue (Explainable Regulatory Intelligence)
            </h3>
            <p className="text-xs text-brand-muted">
              Deterministically ranked by configured weights: stage ageing, deficiency backlog, and imminent SLA breaches
            </p>
          </div>
          <Link
            to="/officer/applications"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Full Docket Registry <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Current Stage</th>
                <th className="px-6 py-3.5">Explainable Priority</th>
                <th className="px-6 py-3.5">Stage Ageing</th>
                <th className="px-6 py-3.5">Recommended Next Action</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(!data?.priority_queue || data.priority_queue.length === 0) ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-brand-muted">
                    No active priority items in queue. All cases are on track.
                  </td>
                </tr>
              ) : (
                data.priority_queue.map((item) => (
                  <tr key={item.application_id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-bold text-brand-ink">
                      {item.application_number}
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-brand-ink">{item.institution_name}</p>
                      <p className="text-[10px] text-brand-muted">{item.region} Region</p>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={item.current_stage} />
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => setSelectedCase(item)}
                        className="text-left group cursor-pointer"
                        title="Click to view explainable factor breakdown"
                      >
                        <PriorityGauge score={item.priority_score} factors={{ tier: item.priority_tier, factors: item.priority_factors }} />
                        <span className="text-[10px] text-brand-teal font-medium group-hover:underline flex items-center gap-1 mt-0.5">
                          <Eye className="w-3 h-3" /> View factors ({item.priority_tier})
                        </span>
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`font-semibold ${item.days_in_stage > 14 ? 'text-[#B9474F]' : item.days_in_stage > 7 ? 'text-[#C5892B]' : 'text-brand-ink'}`}>
                        {item.days_in_stage}d in stage
                      </span>
                    </td>
                    <td className="px-6 py-4 max-w-xs text-brand-muted">
                      <span className="line-clamp-2">{item.recommended_action}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={item.action_link}
                        className="px-3 py-1.5 rounded-lg bg-brand-teal text-white text-xs font-semibold hover:bg-brand-teal-dark shadow-sm inline-flex items-center gap-1"
                      >
                        Action <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Live Operational Activity Stream */}
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-brand-border mb-4">
          <div>
            <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-teal" /> Live Operational Activity Feed
            </h3>
            <p className="text-xs text-brand-muted">
              Chronological log of verified stage transitions, deficiency cures, and verifications
            </p>
          </div>
          <Link
            to="/officer/audit"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Audit Explorer <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="space-y-3">
          {(!data?.recent_activity || data.recent_activity.length === 0) ? (
            <p className="text-xs text-brand-muted text-center py-4">No recent operational activity recorded.</p>
          ) : (
            data.recent_activity.map((act) => (
              <div key={act.id} className="p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-200 text-brand-ink mt-0.5">
                    {act.action}
                  </span>
                  <div>
                    <p className="text-xs font-semibold text-brand-ink">
                      {act.entity_type} #{act.entity_id}
                    </p>
                    <p className="text-[11px] text-brand-muted">
                      {act.details || 'Operational record updated'}
                    </p>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-xs font-medium text-brand-ink">{act.actor_name || 'System Auto'}</p>
                  <p className="text-[10px] text-brand-muted">
                    {new Date(act.created_at).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      dateStyle: 'short',
                      timeStyle: 'short',
                    })}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Priority Factor Explanation Modal */}
      {selectedCase && (
        <Modal
          isOpen={!!selectedCase}
          onClose={() => setSelectedCase(null)}
          title={`Explainable Priority Breakdown — Application ${selectedCase.application_number}`}
          subtitle={`${selectedCase.institution_name} (${selectedCase.region} Region)`}
        >
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border">
              <div>
                <span className="text-[10px] font-bold text-brand-muted uppercase">Computed Urgency Index</span>
                <p className="text-lg font-bold text-brand-ink mt-0.5">
                  {selectedCase.priority_score} / 100 ({selectedCase.priority_tier} Tier)
                </p>
              </div>
              <StatusBadge status={selectedCase.current_stage} />
            </div>

            <div>
              <h4 className="font-bold text-brand-ink uppercase text-[10px] tracking-wider mb-2">
                Itemized Contributing Operational Factors
              </h4>
              <ul className="space-y-1.5">
                {selectedCase.priority_factors.map((f, i) => (
                  <li key={i} className="p-2.5 rounded bg-gray-50 border border-gray-200 font-mono text-[11px] text-brand-ink">
                    • {f}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg">
              <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider">
                Recommended Operational Next Action
              </span>
              <p className="text-xs text-teal-900 font-medium mt-1">
                {selectedCase.recommended_action}
              </p>
            </div>

            <div className="text-[10px] text-brand-muted border-t border-gray-100 pt-3">
              STATUTORY NOTICE: Priority ranking is an operational tool to assist officer triage. It does NOT constitute a statutory decision or adverse regulatory finding.
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
