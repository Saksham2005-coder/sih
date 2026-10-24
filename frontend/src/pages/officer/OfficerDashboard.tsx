import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, AlertTriangle, Compass, CheckCircle2, ShieldAlert,
  BarChart3, RefreshCw, ArrowRight, Play
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { OperationalSummary, Application } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';

export const OfficerDashboard: React.FC = () => {
  const { user, activeRole } = useAuth();
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [priorityApps, setPriorityApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [sumData, appsData] = await Promise.all([
        api.getOperationalSummary(),
        api.getApplications(),
      ]);
      setSummary(sumData);
      setPriorityApps(appsData.slice(0, 5));
    } catch (err) {
      console.error(err);
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

  return (
    <div className="space-y-6">
      {/* Officer Command Banner */}
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              AICTE REGULATORY HEADQUARTERS
            </span>
            <span className="text-xs text-brand-muted">
              Scope: {user?.region ? `${user.region} Region` : 'National Apex'}
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Officer Regulatory Command Centre
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Workspace: <span className="font-semibold text-brand-teal">{activeRole?.replace(/_/g, ' ')}</span> • Live Case Routing & Statutory Oversight
          </p>
        </div>

        <div className="flex items-center gap-2">
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
          subtext="Under active purview"
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
          subtext={`${summary?.awaiting_evc || 0} unscheduled`}
          icon={<Compass className="w-5 h-5" />}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Final Approved"
          value={summary?.approved || 0}
          subtext="Statutory approval granted"
          variant="teal"
          icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
        />
        <StatCard
          title="Active SLA Escalations"
          value={summary?.active_escalations || 0}
          subtext="Tier-1 / Tier-2 breaches"
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

      {/* High Priority Cases Table */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">
              Priority Case Queue (Explainable Regulatory Ranking)
            </h3>
            <p className="text-xs text-brand-muted">
              Ranked dynamically by case ageing, deficiency backlog, and imminent deadlines
            </p>
          </div>
          <Link
            to="/officer/applications"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Full Registry <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Stage</th>
                <th className="px-6 py-3.5">Explainable Priority</th>
                <th className="px-6 py-3.5">Deficiencies</th>
                <th className="px-6 py-3.5">Last Mutation</th>
                <th className="px-6 py-3.5 text-right">Scrutiny Console</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {priorityApps.map((app) => (
                <tr key={app.id} className="hover:bg-gray-50/80 transition-colors">
                  <td className="px-6 py-4 font-bold text-brand-ink">
                    {app.application_number}
                  </td>
                  <td className="px-6 py-4 text-brand-muted font-medium">
                    {app.institution_name} ({app.region})
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={app.current_stage} />
                  </td>
                  <td className="px-6 py-4">
                    <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
                  </td>
                  <td className="px-6 py-4">
                    {app.open_deficiencies_count > 0 ? (
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-[#C5892B] border border-amber-300">
                        {app.open_deficiencies_count} Open
                      </span>
                    ) : (
                      <span className="text-teal-700 text-xs font-medium">Clear</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-brand-muted">
                    {new Date(app.updated_at).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                    })}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/officer/applications/${app.id}`}
                      className="px-3 py-1.5 rounded-lg bg-brand-teal text-white text-xs font-semibold hover:bg-brand-teal-dark shadow-sm inline-flex items-center gap-1"
                    >
                      Scrutiny <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
