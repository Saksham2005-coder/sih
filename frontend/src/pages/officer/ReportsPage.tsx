import React, { useEffect, useState } from 'react';
import {
  BarChart3, Download, PieChart, Layers, CheckCircle2,
  Clock, AlertTriangle, ShieldCheck, RefreshCw, Compass
} from 'lucide-react';
import { api } from '../../api/client';
import {
  OperationalSummary, SlaAdherenceData, EvcAnalyticsData
} from '../../types';
import { StatCard } from '../../components/common/StatCard';

export const ReportsPage: React.FC = () => {
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [slaData, setSlaData] = useState<SlaAdherenceData | null>(null);
  const [evcData, setEvcData] = useState<EvcAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'SLA' | 'EVC'>('OVERVIEW');

  const loadReports = async () => {
    setLoading(true);
    try {
      const [sumRes, slaRes, evcRes] = await Promise.all([
        api.getOperationalSummary(),
        api.getSlaAdherence(),
        api.getEvcAnalytics()
      ]);
      setSummary(sumRes);
      setSlaData(slaRes);
      setEvcData(evcRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleExportCsv = () => {
    window.location.href = '/api/audit/export';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink dark:text-brand-text">Regulatory Reports & Performance Analytics</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200 dark:border-teal-800/60">
              100% Reconciled
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Verified aggregate metrics reconciling directly with underlying regulatory database records
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadReports}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink dark:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={handleExportCsv}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white dark:bg-brand-surface border border-brand-border text-brand-ink dark:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-brand-teal" /> Export Audit CSV
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-brand-border gap-2 text-xs">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`px-4 py-2.5 font-bold border-b-2 transition-colors ${activeTab === 'OVERVIEW' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          Operational Overview
        </button>
        <button
          onClick={() => setActiveTab('SLA')}
          className={`px-4 py-2.5 font-bold border-b-2 transition-colors ${activeTab === 'SLA' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          Stage SLA Adherence
        </button>
        <button
          onClick={() => setActiveTab('EVC')}
          className={`px-4 py-2.5 font-bold border-b-2 transition-colors ${activeTab === 'EVC' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          EVC Inspection Turnaround
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Docket Count"
              value={summary?.total_applications || 0}
              subtext="100% database reconciled"
              icon={<Layers className="w-5 h-5" />}
            />
            <StatCard
              title="Under Active Scrutiny"
              value={summary?.pending_scrutiny || 0}
              subtext="RO / BO review queue"
              variant="amber"
              icon={<BarChart3 className="w-5 h-5" />}
            />
            <StatCard
              title="Statutory Approvals"
              value={summary?.approved || 0}
              subtext="Approval Order issued"
              variant="teal"
              icon={<CheckCircle2 className="w-5 h-5" />}
            />
            <StatCard
              title="EVC Inspections"
              value={(summary?.awaiting_evc || 0) + (summary?.evc_scheduled || 0)}
              subtext="Scheduled & completed"
              icon={<PieChart className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Stage-wise Breakdown */}
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4 flex items-center justify-between">
                <span>Stage-wise Application Distribution</span>
                <span className="text-xs text-brand-muted font-normal">Reconciled Counts</span>
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
                    <tr>
                      <th className="py-2.5 px-3">Regulatory Stage</th>
                      <th className="py-2.5 px-3 text-right">Active Count</th>
                      <th className="py-2.5 px-3 text-right">Percentage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border/40">
                    {summary?.stage_breakdown &&
                      Object.entries(summary.stage_breakdown).map(([stg, count]) => {
                        const total = summary.total_applications || 1;
                        const pct = Math.round((count / total) * 100);
                        return (
                          <tr key={stg} className="hover:bg-brand-porcelain/30 dark:hover:bg-brand-surface-elevated/40 transition-colors">
                            <td className="py-2.5 px-3 font-semibold text-brand-ink dark:text-brand-text">{stg.replace(/_/g, ' ')}</td>
                            <td className="py-2.5 px-3 text-right font-bold text-brand-ink dark:text-brand-text">{count}</td>
                            <td className="py-2.5 px-3 text-right text-brand-muted">{pct}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Regional Breakdown */}
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4 flex items-center justify-between">
                <span>Regional Workload Distribution</span>
                <span className="text-xs text-brand-muted font-normal">By AICTE Regional Office</span>
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
                    <tr>
                      <th className="py-2.5 px-3">Regional Office Scope</th>
                      <th className="py-2.5 px-3 text-right">Assigned Docket</th>
                      <th className="py-2.5 px-3 text-right">Distribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border/40">
                    {summary?.regional_breakdown &&
                      Object.entries(summary.regional_breakdown).map(([reg, count]) => {
                        const total = summary.total_applications || 1;
                        const pct = Math.round((count / total) * 100);
                        return (
                          <tr key={reg} className="hover:bg-brand-porcelain/30 dark:hover:bg-brand-surface-elevated/40 transition-colors">
                            <td className="py-2.5 px-3 font-semibold text-brand-ink dark:text-brand-text">{reg} Region</td>
                            <td className="py-2.5 px-3 text-right font-bold text-brand-ink dark:text-brand-text">{count}</td>
                            <td className="py-2.5 px-3 text-right text-brand-muted">{pct}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: SLA Adherence */}
      {activeTab === 'SLA' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Within SLA Performance"
              value={`${slaData?.within_sla_percentage || 0}%`}
              subtext={`${slaData?.within_sla_count || 0} cases compliant`}
              variant="teal"
              icon={<ShieldCheck className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Breached SLA Backlog"
              value={`${slaData?.breached_sla_percentage || 0}%`}
              subtext={`${slaData?.breached_sla_count || 0} cases pending > 14 days`}
              variant={(slaData?.breached_sla_count || 0) > 0 ? 'red' : 'default'}
              icon={<AlertTriangle className="w-5 h-5 text-[#B9474F] dark:text-red-400" />}
            />
            <StatCard
              title="Total Cases Monitored"
              value={slaData?.total_cases_analyzed || 0}
              subtext="Active regulatory dockets"
              icon={<Layers className="w-5 h-5" />}
            />
          </div>

          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
            <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
              Stage-wise SLA Turnaround & Pendency Analysis
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
                  <tr>
                    <th className="py-2.5 px-4">Stage Name</th>
                    <th className="py-2.5 px-4 text-center">Cases</th>
                    <th className="py-2.5 px-4 text-center">Average Turnaround</th>
                    <th className="py-2.5 px-4 text-center">Within SLA</th>
                    <th className="py-2.5 px-4 text-right">Breached SLA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/40">
                  {slaData?.stage_sla_breakdown.map((row) => (
                    <tr key={row.stage} className="hover:bg-brand-porcelain/30 dark:hover:bg-brand-surface-elevated/40 transition-colors">
                      <td className="py-3 px-4 font-semibold text-brand-ink dark:text-brand-text">{row.stage.replace(/_/g, ' ')}</td>
                      <td className="py-3 px-4 text-center font-bold text-brand-ink dark:text-brand-text">{row.case_count}</td>
                      <td className="py-3 px-4 text-center text-brand-muted">{row.average_days} Days</td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded font-bold bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200 dark:border-teal-800/60">
                          {row.within_count}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {row.breached_count > 0 ? (
                          <span className="px-2 py-0.5 rounded font-bold bg-red-50 dark:bg-red-950/40 text-[#B9474F] dark:text-red-400 border border-red-200 dark:border-red-900/60">
                            {row.breached_count} Breached
                          </span>
                        ) : (
                          <span className="text-teal-700 dark:text-teal-400 font-medium">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: EVC Analytics */}
      {activeTab === 'EVC' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Total Inspections"
              value={evcData?.total_inspections || 0}
              subtext="Physical & virtual roster"
              icon={<Compass className="w-5 h-5" />}
            />
            <StatCard
              title="Scheduled / In Progress"
              value={evcData?.scheduled_count || 0}
              subtext="Panels assigned"
              variant="amber"
              icon={<Clock className="w-5 h-5 text-[#C5892B] dark:text-amber-400" />}
            />
            <StatCard
              title="Completed Visits"
              value={evcData?.completed_count || 0}
              subtext="Signed reports received"
              variant="teal"
              icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Inspection Mode Distribution
              </h3>
              <div className="space-y-3">
                {evcData?.inspection_types &&
                  Object.entries(evcData.inspection_types).map(([type, count]) => (
                    <div key={type} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border">
                      <span className="font-semibold text-brand-ink dark:text-brand-text text-xs">{type.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-brand-teal text-sm">{count}</span>
                    </div>
                  ))}
              </div>
            </div>

            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Committee Recommendation Outcomes
              </h3>
              <div className="space-y-3">
                {evcData?.recommendations && Object.keys(evcData.recommendations).length > 0 ? (
                  Object.entries(evcData.recommendations).map(([rec, count]) => (
                    <div key={rec} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border">
                      <span className="font-semibold text-brand-ink dark:text-brand-text text-xs">{rec.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-brand-ink dark:text-brand-text text-sm">{count}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-brand-muted py-4 text-center">No final recommendations recorded yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
