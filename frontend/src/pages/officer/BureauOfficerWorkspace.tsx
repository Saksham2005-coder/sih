import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Layers, AlertTriangle, ShieldAlert, BarChart3,
  RefreshCw, Play, ArrowRight, Eye, CheckCircle2,
  TrendingUp, Download, Globe
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { CommandCentreData, AlertEscalationItem, SlaAdherenceData } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';

export const BureauOfficerWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<CommandCentreData | null>(null);
  const [escalations, setEscalations] = useState<AlertEscalationItem[]>([]);
  const [slaData, setSlaData] = useState<SlaAdherenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ccRes, escList, slaRes] = await Promise.all([
        api.getCommandCentre(),
        api.getEscalations({ status_filter: 'ACTIVE' }),
        api.getSlaAdherence(),
      ]);
      setData(ccRes);
      setEscalations(escList);
      setSlaData(slaRes);
    } catch (err) {
      console.error('Failed to load bureau data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunDeadlineScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.runDeadlineScan();
      setScanResult(
        `National SLA Scan Finished: ${res.scanned_entities} cases evaluated, ${res.reminders_created} reminders generated, ${res.escalations_created} escalations triggered, ${res.duplicates_prevented} duplicate events prevented in ${res.execution_time_ms}ms.`
      );
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleAcknowledgeEscalation = async (escId: number) => {
    try {
      await api.acknowledgeEscalation(escId, 'Acknowledged at AICTE Apex Bureau level.');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Acknowledgment failed');
    }
  };

  const summary = data?.summary;
  const regionalBreakdown = summary?.regional_breakdown || {};
  const stageBreakdown = summary?.stage_breakdown || {};

  return (
    <div className="space-y-6">
      {/* Bureau Oversight Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-ink text-white">
              AICTE APEX BUREAU OVERSIGHT
            </span>
            <span className="text-xs text-brand-muted">
              Scope: <strong>National Regulatory Directorate</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            National Approval Operations & SLA Oversight
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Bureau Officer: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (BUREAU OFFICER) • Cross-Regional Workload & Tier-2 Escalations
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors duration-150"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={handleRunDeadlineScan}
            disabled={scanning}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-teal text-white text-xs font-semibold hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
          >
            <Play className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Running National Scan...' : 'Trigger National SLA Scan'}
          </button>
        </div>
      </div>

      {/* Scan Result Notice */}
      {scanResult && (
        <div className="p-4 bg-teal-50 dark:bg-teal-950/80 border border-teal-200 dark:border-teal-700/80 rounded-xl text-xs text-teal-800 dark:text-teal-200 font-medium flex items-center justify-between">
          <span>{scanResult}</span>
          <button onClick={() => setScanResult(null)} className="text-teal-900 dark:text-teal-100 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* National Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total National Filings"
          value={summary?.total_applications ?? 0}
          subtext="All regions across India"
          icon={<Globe size={18} />}
        />
        <StatCard
          title="Active SLA Escalations"
          value={escalations.length}
          subtext="L2 Bureau & L3 Council alerts"
          icon={<ShieldAlert size={18} />}
          variant={escalations.length > 0 ? 'red' : 'default'}
        />
        <StatCard
          title="SLA Compliance Rate"
          value={`${slaData?.within_sla_percentage ?? 100}%`}
          subtext={`${slaData?.within_sla_count ?? 0} of ${slaData?.total_cases_analyzed ?? 0} cases within SLA`}
          icon={<TrendingUp size={18} />}
          variant={(slaData?.within_sla_percentage ?? 100) < 80 ? 'amber' : 'default'}
        />
        <StatCard
          title="Total Approved"
          value={summary?.approved ?? 0}
          subtext="Statutory approval orders issued"
          icon={<CheckCircle2 size={18} />}
        />
      </div>

      {/* Cross-Regional Workload & Comparison Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Cross-Regional Workload & Pendency Breakdown</h3>
            <p className="text-xs text-brand-muted">Comparative regional performance, application volume, and stage distribution</p>
          </div>
          <Link
            to="/officer/reports"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Analytics Hub <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(regionalBreakdown).map(([region, count]) => (
            <div key={region} className="p-4 rounded-xl border border-brand-border bg-brand-porcelain/40 dark:bg-brand-surface-secondary/60 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-brand-ink">{region} Region</p>
                <p className="text-[11px] text-brand-muted mt-0.5">Active Jurisdiction</p>
              </div>
              <div className="text-right">
                <span className="text-lg font-bold text-brand-teal">{count}</span>
                <span className="block text-[10px] text-brand-muted">Applications</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Bureau-Level Escalations Queue */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Active Bureau & Multi-Tier Escalations</h3>
            <p className="text-xs text-brand-muted">Breached regulatory SLAs automatically escalated from Regional Offices</p>
          </div>
          <Link
            to="/officer/escalations"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            All Escalations <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Escalation Tier</th>
                <th className="px-6 py-3.5">Entity & Trigger</th>
                <th className="px-6 py-3.5">Institution / Region</th>
                <th className="px-6 py-3.5">Overdue Days</th>
                <th className="px-6 py-3.5 text-right">Bureau Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {escalations.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-brand-muted">
                    Zero active escalations. All regional operations currently running within SLA.
                  </td>
                </tr>
              ) : (
                escalations.map((esc) => (
                  <tr key={esc.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 dark:bg-red-950/80 text-[#B42332] dark:text-red-200 border border-rose-300 dark:border-red-700/80">
                        {esc.escalation_level.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-bold text-brand-ink">{esc.entity_type} #{esc.entity_id}</p>
                      <span className="text-[10px] text-brand-muted">{esc.trigger_type}</span>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{esc.region || `Institution #${esc.institution_id}` || 'Regional Institutional Unit'}</p>
                      <span className="text-[10px] text-brand-muted">Entity #{esc.entity_id}</span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-[#B42332] dark:text-red-400">
                      +{esc.threshold_days} days
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleAcknowledgeEscalation(esc.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                      >
                        Acknowledge & Intervene
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default BureauOfficerWorkspace;
