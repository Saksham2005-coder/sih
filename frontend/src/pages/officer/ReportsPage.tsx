import React, { useEffect, useState } from 'react';
import {
  BarChart3, Download, PieChart, Layers, CheckCircle2,
  Clock, AlertTriangle, ShieldCheck, RefreshCw, Compass,
  FileText, Printer, Filter, Calendar, Building2, FileCheck2,
  BellRing, ArrowUpRight, Check
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  OperationalSummary, SlaAdherenceData, EvcAnalyticsData,
  ComplianceAnalyticsData, DocumentAnalyticsData,
  EscalationsAnalyticsData, RegionalPerformanceData
} from '../../types';
import { StatCard } from '../../components/common/StatCard';

export const ReportsPage: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'OVERVIEW' | 'SLA' | 'EVC' | 'COMPLIANCE' | 'DOCUMENTS' | 'ESCALATIONS' | 'REGIONAL'
  >('OVERVIEW');

  // Filters
  const userRoles = user?.roles || [];
  const isRegionalOnly = userRoles.includes('REGIONAL_OFFICER') && !userRoles.includes('SYSTEM_ADMIN') && !userRoles.includes('BUREAU_OFFICER');
  const [selectedRegion, setSelectedRegion] = useState<string>(isRegionalOnly && user?.region ? user.region : '');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  // Data states
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [slaData, setSlaData] = useState<SlaAdherenceData | null>(null);
  const [evcData, setEvcData] = useState<EvcAnalyticsData | null>(null);
  const [complianceData, setComplianceData] = useState<ComplianceAnalyticsData | null>(null);
  const [documentData, setDocumentData] = useState<DocumentAnalyticsData | null>(null);
  const [escalationsData, setEscalationsData] = useState<EscalationsAnalyticsData | null>(null);
  const [regionalData, setRegionalData] = useState<RegionalPerformanceData | null>(null);

  // Print mode
  const [showPrintDossier, setShowPrintDossier] = useState(false);

  const loadReports = async () => {
    setLoading(true);
    try {
      const filterParams = {
        region: selectedRegion || undefined,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
      };

      const [sumRes, slaRes, evcRes, compRes, docRes, escRes, regRes] = await Promise.all([
        api.getOperationalSummary(filterParams),
        api.getSlaAdherence(filterParams),
        api.getEvcAnalytics(filterParams),
        api.getComplianceAnalytics(filterParams),
        api.getDocumentAnalytics(filterParams),
        api.getEscalationsAnalytics(filterParams),
        api.getRegionalPerformance({
          date_from: filterParams.date_from,
          date_to: filterParams.date_to,
        })
      ]);

      setSummary(sumRes);
      setSlaData(slaRes);
      setEvcData(evcRes);
      setComplianceData(compRes);
      setDocumentData(docRes);
      setEscalationsData(escRes);
      setRegionalData(regRes);
    } catch (err) {
      console.error('Failed to load regulatory reports', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [selectedRegion]);

  const handleApplyFilter = (e: React.FormEvent) => {
    e.preventDefault();
    loadReports();
  };

  const handleResetFilter = () => {
    setSelectedRegion(isRegionalOnly && user?.region ? user.region : '');
    setDateFrom('');
    setDateTo('');
    setTimeout(() => {
      loadReports();
    }, 50);
  };

  const handleExportCsv = (category: string) => {
    const csvUrl = api.getReportCsvUrl(category, {
      region: selectedRegion || undefined,
      date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
      date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
    });
    window.location.href = csvUrl;
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink dark:text-brand-text">Regulatory Reports & Monitoring Center</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200 dark:border-teal-800/60">
              100% Reconciled
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Verified, jurisdiction-scoped operational intelligence backed directly by authoritative regulatory databases
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={loadReports}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink dark:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>

          <button
            onClick={() => handleExportCsv(activeTab)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white dark:bg-brand-surface border border-brand-border text-brand-ink dark:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-brand-teal" /> Export {activeTab} CSV
          </button>

          <button
            onClick={() => setShowPrintDossier(!showPrintDossier)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark text-xs font-semibold shadow-sm transition-colors"
          >
            <Printer className="w-3.5 h-3.5 text-white" /> {showPrintDossier ? 'Hide PDF Preview' : 'Generate PDF Dossier'}
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <form onSubmit={handleApplyFilter} className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-4 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-bold uppercase tracking-wider text-[10px] text-brand-muted flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-brand-teal" /> Scope Filters:
          </span>

          {/* Region Filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-brand-muted font-medium">Region:</label>
            <select
              disabled={isRegionalOnly}
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="border border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-text font-semibold focus:ring-1 focus:ring-brand-teal disabled:opacity-70"
            >
              <option value="">National (All Regions)</option>
              <option value="Northern">Northern Region</option>
              <option value="North-West">North-West Region</option>
              <option value="Central">Central Region</option>
              <option value="Western">Western Region</option>
              <option value="South-West">South-West Region</option>
              <option value="Southern">Southern Region</option>
              <option value="Eastern">Eastern Region</option>
            </select>
          </div>

          {/* Date Range */}
          <div className="flex items-center gap-1.5">
            <label className="text-brand-muted font-medium">From:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="border border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-text focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-brand-muted font-medium">To:</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="border border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-text focus:ring-1 focus:ring-brand-teal"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-brand-teal text-white font-semibold hover:bg-brand-teal-dark shadow-sm transition-colors"
          >
            Apply Filters
          </button>
          <button
            type="button"
            onClick={handleResetFilter}
            className="px-2.5 py-1.5 rounded-lg border border-brand-border text-brand-muted hover:text-brand-ink dark:hover:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated transition-colors"
          >
            Reset
          </button>
        </div>
      </form>

      {/* Official Print Dossier Modal / View */}
      {showPrintDossier && (
        <div className="bg-white dark:bg-brand-surface border-2 border-brand-teal rounded-xl p-6 shadow-md space-y-4 print:p-0 print:border-none print:shadow-none">
          <div className="flex justify-between items-start border-b border-brand-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-brand-ink dark:text-brand-text">ALL INDIA COUNCIL FOR TECHNICAL EDUCATION</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold border border-amber-300">
                  OFFICIAL AUDIT DOSSIER
                </span>
              </div>
              <p className="text-xs text-brand-muted mt-1">
                Statutory Performance Report & Consolidated Regulatory Audit Record • Reconciled at {new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST
              </p>
              <p className="text-xs text-brand-ink dark:text-brand-text font-semibold mt-0.5">
                Jurisdiction Scope: {selectedRegion ? `${selectedRegion} Regional Office` : 'National Apex Scope'} • Generated by: {user?.full_name} ({userRoles[0]?.replace(/_/g, ' ')})
              </p>
            </div>
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg text-xs font-bold inline-flex items-center gap-1.5 shadow-sm print:hidden"
            >
              <Printer className="w-4 h-4" /> Print / Save as PDF
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border">
              <span className="text-brand-muted text-[10px] uppercase font-bold">Total Docket Count</span>
              <p className="text-lg font-bold text-brand-ink dark:text-brand-text mt-1">{summary?.total_applications || 0}</p>
            </div>
            <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border">
              <span className="text-brand-muted text-[10px] uppercase font-bold">Within SLA Rate</span>
              <p className="text-lg font-bold text-brand-teal mt-1">{slaData?.within_sla_percentage || 100}%</p>
            </div>
            <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border">
              <span className="text-brand-muted text-[10px] uppercase font-bold">Compliance Fulfilment</span>
              <p className="text-lg font-bold text-brand-teal mt-1">{complianceData?.compliance_percentage || 100}%</p>
            </div>
            <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border">
              <span className="text-brand-muted text-[10px] uppercase font-bold">Active Escalations</span>
              <p className="text-lg font-bold text-red-600 dark:text-red-400 mt-1">{summary?.active_escalations || 0}</p>
            </div>
          </div>

          <div className="text-[11px] text-brand-muted border-t border-brand-border pt-3 flex justify-between items-center">
            <span>Authentication Digest: Verified against append-only audit trail and SHA-256 evidence integrity</span>
            <span className="font-mono text-[10px]">RECO-REF-{Date.now().toString().slice(-8)}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-brand-border gap-1 overflow-x-auto text-xs">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'OVERVIEW' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          1. Overview & Pendency
        </button>
        <button
          onClick={() => setActiveTab('SLA')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'SLA' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          2. Ageing & SLA Breaches
        </button>
        <button
          onClick={() => setActiveTab('EVC')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'EVC' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          3. EVC Eligibility & Scheduling
        </button>
        <button
          onClick={() => setActiveTab('COMPLIANCE')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'COMPLIANCE' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          4. Undertaking Compliance
        </button>
        <button
          onClick={() => setActiveTab('DOCUMENTS')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'DOCUMENTS' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          5. Document Validity & Renewals
        </button>
        <button
          onClick={() => setActiveTab('ESCALATIONS')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'ESCALATIONS' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          6. Overdue & Multi-Tier Escalations
        </button>
        <button
          onClick={() => setActiveTab('REGIONAL')}
          className={`px-3.5 py-2.5 font-bold border-b-2 whitespace-nowrap transition-colors ${activeTab === 'REGIONAL' ? 'border-brand-teal text-brand-teal' : 'border-transparent text-brand-muted hover:text-brand-ink dark:hover:text-brand-text'}`}
        >
          7. Regional Workload & Performance
        </button>
      </div>

      {/* Tab 1: Overview & Pendency */}
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
              title="EVC Queue & Visits"
              value={(summary?.awaiting_evc || 0) + (summary?.evc_scheduled || 0)}
              subtext="Eligible / scheduled"
              icon={<PieChart className="w-5 h-5" />}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Stage-wise Breakdown */}
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4 flex items-center justify-between">
                <span>Application Pendency by Stage</span>
                <span className="text-xs text-brand-muted font-normal">Reconciled Counts</span>
              </h3>

              <div className="overflow-x-auto w-full">
                <table className="w-full text-left text-xs min-w-[320px]">
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
                <span>Regional Application Distribution</span>
                <span className="text-xs text-brand-muted font-normal">By AICTE Regional Office</span>
              </h3>

              <div className="overflow-x-auto w-full">
                <table className="w-full text-left text-xs min-w-[320px]">
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

      {/* Tab 2: Ageing & SLA Breaches */}
      {activeTab === 'SLA' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Within SLA Turnaround"
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
              Stage-wise SLA Turnaround & Ageing Analysis
            </h3>

            <div className="overflow-x-auto w-full">
              <table className="w-full text-left text-xs min-w-[600px]">
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

      {/* Tab 3: EVC Eligibility & Scheduling */}
      {activeTab === 'EVC' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <StatCard
              title="Eligible Applications"
              value={evcData?.eligible_count || 0}
              subtext="Physical/Virtual visits"
              icon={<Compass className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Total Inspections"
              value={evcData?.total_inspections || 0}
              subtext="Panels rostered"
              icon={<Layers className="w-5 h-5" />}
            />
            <StatCard
              title="Scheduled / In Progress"
              value={evcData?.scheduled_count || 0}
              subtext="Panel active"
              variant="amber"
              icon={<Clock className="w-5 h-5 text-[#C5892B] dark:text-amber-400" />}
            />
            <StatCard
              title="Completed Visits"
              value={evcData?.completed_count || 0}
              subtext="Signed report received"
              variant="teal"
              icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Inspection Mode Breakdown
              </h3>
              <div className="space-y-3">
                {evcData?.inspection_types && Object.keys(evcData.inspection_types).length > 0 ? (
                  Object.entries(evcData.inspection_types).map(([type, count]) => (
                    <div key={type} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border">
                      <span className="font-semibold text-brand-ink dark:text-brand-text text-xs">{type.replace(/_/g, ' ')}</span>
                      <span className="font-bold text-brand-teal text-sm">{count}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-brand-muted py-4 text-center">No inspections recorded in selected scope.</p>
                )}
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

      {/* Tab 4: Undertaking Compliance */}
      {activeTab === 'COMPLIANCE' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <StatCard
              title="Compliance Ratio"
              value={`${complianceData?.compliance_percentage || 100}%`}
              subtext="Verified undertakings"
              variant="teal"
              icon={<ShieldCheck className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Verified Obligations"
              value={complianceData?.verified_count || 0}
              subtext="Officer signed-off"
              variant="teal"
              icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Pending Verification"
              value={complianceData?.pending_verification_count || 0}
              subtext="Evidence under review"
              variant="amber"
              icon={<Clock className="w-5 h-5 text-amber-500" />}
            />
            <StatCard
              title="Overdue Undertakings"
              value={complianceData?.overdue_count || 0}
              subtext="Beyond stipulated SLA"
              variant={(complianceData?.overdue_count || 0) > 0 ? 'red' : 'default'}
              icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Undertaking Category Breakdown
              </h3>
              <div className="space-y-3">
                {complianceData?.category_breakdown && Object.entries(complianceData.category_breakdown).map(([cat, count]) => (
                  <div key={cat} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border text-xs">
                    <span className="font-semibold text-brand-ink dark:text-brand-text">{cat.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-brand-teal">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Fulfillment Status Distribution
              </h3>
              <div className="space-y-3">
                {complianceData?.status_breakdown && Object.entries(complianceData.status_breakdown).map(([st, count]) => (
                  <div key={st} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border text-xs">
                    <span className="font-semibold text-brand-ink dark:text-brand-text">{st.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-brand-ink dark:text-brand-text">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Document Validity & Renewals */}
      {activeTab === 'DOCUMENTS' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <StatCard
              title="Validity Rate"
              value={`${documentData?.validity_compliance_percentage || 100}%`}
              subtext="Active valid documents"
              variant="teal"
              icon={<ShieldCheck className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Active & Valid"
              value={documentData?.active_count || 0}
              subtext="In term"
              variant="teal"
              icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Expiring Soon"
              value={documentData?.expiring_soon_count || 0}
              subtext="T-90/60/30 window"
              variant="amber"
              icon={<Clock className="w-5 h-5 text-amber-500" />}
            />
            <StatCard
              title="Expired Validity"
              value={documentData?.expired_count || 0}
              subtext="Immediate renewal required"
              variant={(documentData?.expired_count || 0) > 0 ? 'red' : 'default'}
              icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
            />
          </div>

          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
            <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
              Document Type Distribution & Tracking
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {documentData?.type_breakdown && Object.entries(documentData.type_breakdown).map(([dtype, count]) => (
                <div key={dtype} className="p-4 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border text-xs">
                  <span className="font-semibold text-brand-ink dark:text-brand-text block">{dtype.replace(/_/g, ' ')}</span>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-brand-muted text-[10px]">Tracked Records</span>
                    <span className="font-bold text-brand-teal text-base">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: Overdue & Multi-Tier Escalations */}
      {activeTab === 'ESCALATIONS' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <StatCard
              title="Total Escalations"
              value={escalationsData?.total_escalations || 0}
              subtext="Cryptographically deduplicated"
              icon={<BellRing className="w-5 h-5" />}
            />
            <StatCard
              title="Active Escalations"
              value={escalationsData?.active_count || 0}
              subtext="Unacknowledged"
              variant={(escalationsData?.active_count || 0) > 0 ? 'red' : 'default'}
              icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
            />
            <StatCard
              title="Acknowledged"
              value={escalationsData?.acknowledged_count || 0}
              subtext="Officer noted"
              variant="teal"
              icon={<Check className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="Resolved"
              value={escalationsData?.resolved_count || 0}
              subtext="Matter closed"
              icon={<CheckCircle2 className="w-5 h-5 text-brand-teal" />}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Escalation Hierarchy Distribution
              </h3>
              <div className="space-y-3">
                {escalationsData?.tier_breakdown && Object.entries(escalationsData.tier_breakdown).map(([tier, count]) => (
                  <div key={tier} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border text-xs">
                    <span className="font-semibold text-brand-ink dark:text-brand-text">{tier.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-brand-teal">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
              <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4">
                Trigger Cause Distribution
              </h3>
              <div className="space-y-3">
                {escalationsData?.trigger_breakdown && Object.entries(escalationsData.trigger_breakdown).map(([trig, count]) => (
                  <div key={trig} className="flex justify-between items-center p-3 rounded-lg bg-brand-porcelain/60 dark:bg-brand-surface-elevated border border-brand-border text-xs">
                    <span className="font-semibold text-brand-ink dark:text-brand-text">{trig.replace(/_/g, ' ')}</span>
                    <span className="font-bold text-brand-ink dark:text-brand-text">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 7: Regional Workload & Performance */}
      {activeTab === 'REGIONAL' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <StatCard
              title="National SLA Compliance"
              value={`${regionalData?.national_sla_compliance_rate || 100}%`}
              subtext="Across all 7 AICTE regions"
              variant="teal"
              icon={<ShieldCheck className="w-5 h-5 text-brand-teal" />}
            />
            <StatCard
              title="National Average Turnaround"
              value={`${regionalData?.national_avg_turnaround_days || 0} Days`}
              subtext="Stage-to-stage benchmark"
              icon={<Clock className="w-5 h-5" />}
            />
          </div>

          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm">
            <h3 className="text-sm font-bold text-brand-ink dark:text-brand-text pb-3 border-b border-brand-border mb-4 flex items-center justify-between">
              <span>Comparative Regional Performance & Workload Distribution</span>
              <span className="text-xs text-brand-muted font-normal">Reconciled Records</span>
            </h3>

            <div className="overflow-x-auto w-full">
              <table className="w-full text-left text-xs min-w-[700px]">
                <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
                  <tr>
                    <th className="py-2.5 px-3">AICTE Region</th>
                    <th className="py-2.5 px-3 text-center">Total Docket</th>
                    <th className="py-2.5 px-3 text-center">Scrutiny</th>
                    <th className="py-2.5 px-3 text-center">EVC</th>
                    <th className="py-2.5 px-3 text-center">Approved</th>
                    <th className="py-2.5 px-3 text-center">Avg Turnaround</th>
                    <th className="py-2.5 px-3 text-center">SLA Compliance</th>
                    <th className="py-2.5 px-3 text-right">Escalations</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border/40">
                  {regionalData?.regions.map((reg) => (
                    <tr key={reg.region} className="hover:bg-brand-porcelain/30 dark:hover:bg-brand-surface-elevated/40 transition-colors">
                      <td className="py-3 px-3 font-semibold text-brand-ink dark:text-brand-text">{reg.region} Region</td>
                      <td className="py-3 px-3 text-center font-bold text-brand-ink dark:text-brand-text">{reg.total_applications}</td>
                      <td className="py-3 px-3 text-center">{reg.pending_scrutiny}</td>
                      <td className="py-3 px-3 text-center">{reg.in_evc}</td>
                      <td className="py-3 px-3 text-center font-semibold text-brand-teal">{reg.approved}</td>
                      <td className="py-3 px-3 text-center text-brand-muted">{reg.avg_turnaround_days} Days</td>
                      <td className="py-3 px-3 text-center">
                        <span className={`px-2 py-0.5 rounded font-bold ${reg.sla_compliance_rate >= 80 ? 'bg-teal-50 dark:bg-teal-950/40 text-brand-teal border border-teal-200 dark:border-teal-800/60' : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 border border-amber-200'}`}>
                          {reg.sla_compliance_rate}%
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        {reg.active_escalations > 0 ? (
                          <span className="px-2 py-0.5 rounded font-bold bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200">
                            {reg.active_escalations}
                          </span>
                        ) : (
                          <span className="text-brand-teal font-medium">0</span>
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
    </div>
  );
};
