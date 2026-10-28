import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, AlertTriangle, Compass, CheckCircle2, ShieldAlert,
  BarChart3, RefreshCw, ArrowRight, Eye, CheckSquare, Layers, Clock, Cpu, FileSearch
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { CommandCentreData, PriorityActionItem, ComplianceUndertaking, DocumentRecord, Application } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';
import { Modal } from '../../components/common/Modal';
import { DocumentIntelligenceModal } from '../../components/common/DocumentIntelligenceModal';

export const RegionalOfficerWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<CommandCentreData | null>(null);
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [intelModalOpen, setIntelModalOpen] = useState(false);
  const [selectedDocForIntel, setSelectedDocForIntel] = useState<DocumentRecord | null>(null);

  // Deficiency creation state
  const [deficiencyModalApp, setDeficiencyModalApp] = useState<Application | null>(null);
  const [defCategory, setDefCategory] = useState('INFRASTRUCTURE');
  const [defDescription, setDefDescription] = useState('');
  const [defDoc, setDefDoc] = useState('');
  const [submittingDef, setSubmittingDef] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ccRes, uList, dList] = await Promise.all([
        api.getCommandCentre(),
        api.getUndertakings(),
        api.getDocuments(),
      ]);
      setData(ccRes);
      setUndertakings(uList);
      setDocuments(dList);
    } catch (err) {
      console.error('Failed to load regional data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleIssueDeficiency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deficiencyModalApp) return;
    setSubmittingDef(true);
    try {
      await api.issueDeficiency(deficiencyModalApp.id, {
        category: defCategory,
        description: defDescription,
        required_document: defDoc || undefined,
      });
      // Transition application to DEFICIENCY_COMMUNICATED
      await api.transitionApplication(deficiencyModalApp.id, {
        to_stage: 'DEFICIENCY_COMMUNICATED',
        remarks: `Deficiency memo issued under category ${defCategory}: ${defDescription}`,
      });
      setDeficiencyModalApp(null);
      setDefDescription('');
      setDefDoc('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to issue deficiency');
    } finally {
      setSubmittingDef(false);
    }
  };

  const handleVerifyUndertaking = async (uId: number, statusVal: string) => {
    try {
      await api.verifyCompliance(uId, {
        status: statusVal,
        notes: `Verified by Regional Officer ${user?.full_name} for ${user?.region} Region.`,
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    }
  };

  const handleOpenDocIntelligence = (doc: DocumentRecord) => {
    setSelectedDocForIntel(doc);
    setIntelModalOpen(true);
  };

  const summary = data?.summary;
  const bottlenecks = data?.bottlenecks;
  const priorityItems = data?.priority_queue || [];

  return (
    <div className="space-y-6">
      {/* Regional Command Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              AICTE REGIONAL COMMAND CENTRE
            </span>
            <span className="text-xs text-brand-muted">
              Scope: <strong className="text-brand-ink">{user?.region || 'Western'} Region</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Regional Operational Regulatory Command
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Officer: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (REGIONAL OFFICER) • Scrutiny, Cure Audits & Verification
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Scope
        </button>
      </div>

      {/* Regional Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Regional Applications"
          value={summary?.total_applications ?? 0}
          subtext={`Under ${user?.region || 'Western'} jurisdiction`}
          icon={<FileText size={18} />}
        />
        <StatCard
          title="Pending Scrutiny"
          value={summary?.pending_scrutiny ?? 0}
          subtext="Submitted or resubmitted"
          icon={<AlertTriangle size={18} />}
          variant={(summary?.pending_scrutiny ?? 0) > 0 ? 'amber' : 'default'}
        />
        <StatCard
          title="Deficiency Cure Window"
          value={summary?.deficiency_cure_required ?? 0}
          subtext="Institutions rectifying memos"
          icon={<Clock size={18} />}
        />
        <StatCard
          title="Regional Escalations"
          value={summary?.active_escalations ?? 0}
          subtext="SLA breaches requiring RO action"
          icon={<ShieldAlert size={18} />}
          variant={(summary?.active_escalations ?? 0) > 0 ? 'red' : 'default'}
        />
      </div>

      {/* Workload & Bottleneck Metrics */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-brand-border">
          <span className="text-xs font-bold text-brand-ink uppercase tracking-wider flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-teal" />
            Regional Operational Bottleneck Indicators
          </span>
          <span className="text-[10px] text-brand-muted font-medium bg-gray-100 dark:bg-brand-surface-secondary px-2 py-0.5 rounded border border-brand-border">
            Live Database Derived
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 text-xs">
          <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Repeated Deficiencies:</span>
            <p className="text-base font-bold text-brand-ink mt-0.5">{bottlenecks?.repeated_returns_count ?? 0}</p>
            <span className="text-[10px] text-brand-muted">Cases returned &gt; 1 time</span>
          </div>
          <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Undertaking Backlog:</span>
            <p className="text-base font-bold text-brand-ink mt-0.5">{bottlenecks?.verification_backlog_undertakings ?? 0}</p>
            <span className="text-[10px] text-brand-muted">Awaiting official RO verification</span>
          </div>
          <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Document Renewal Queue:</span>
            <p className="text-base font-bold text-brand-ink mt-0.5">{bottlenecks?.verification_backlog_documents ?? 0}</p>
            <span className="text-[10px] text-brand-muted">Renewed deeds pending sign-off</span>
          </div>
          <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Average Stage Ageing:</span>
            <p className="text-base font-bold text-brand-ink mt-0.5">{bottlenecks?.average_stage_ageing_days ?? 0} Days</p>
            <span className="text-[10px] text-brand-muted">Mean pendency in stage</span>
          </div>
        </div>
      </div>

      {/* Priority Scrutiny Queue Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-brand-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Regional Priority Scrutiny & Action Queue</h3>
            <p className="text-xs text-brand-muted">Ranked by explainable urgency score (SLA pendency, past deficiencies, regulatory weights)</p>
          </div>
          <Link
            to="/officer/applications"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1 self-start sm:self-auto"
          >
            All Regional Cases <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[700px]">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Current Stage</th>
                <th className="px-6 py-3.5">Priority Urgency</th>
                <th className="px-6 py-3.5">Stage Pendency</th>
                <th className="px-6 py-3.5 text-right">Scrutiny Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {priorityItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-brand-muted">
                    No active applications requiring priority regional action.
                  </td>
                </tr>
              ) : (
                priorityItems.map((item) => (
                  <tr key={item.application_id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                    <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                      <Link to={`/officer/applications/${item.application_id}`} className="hover:text-brand-teal transition-colors">
                        {item.application_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{item.institution_name}</p>
                      <span className="text-[10px] text-brand-muted">{item.region} Region</span>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={item.current_stage} />
                    </td>
                    <td className="px-6 py-4">
                      <PriorityGauge score={item.priority_score} factors={{ tier: item.priority_tier, factors: item.priority_factors }} />
                    </td>
                    <td className="px-6 py-4 font-mono font-medium text-brand-ink">
                      {item.days_in_stage} days
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/officer/applications/${item.application_id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                      >
                        <Eye className="w-3.5 h-3.5" /> Scrutinize Case
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Regional Compliance Evidence Verification Desk */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-brand-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Compliance Undertaking Verification Desk</h3>
            <p className="text-xs text-brand-muted">Review submitted institutional proofs and issue statutory verification or deficiency orders</p>
          </div>
          <Link
            to="/officer/compliance"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1 self-start sm:self-auto"
          >
            Compliance Module <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[650px]">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Obligation & Rule</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Due Date</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Regional Sign-Off</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {undertakings.slice(0, 5).map((u) => (
                <tr key={u.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4">
                    <p className="font-bold text-brand-ink">{u.title}</p>
                    <span className="text-[10px] text-brand-teal font-mono">{u.rule_code}</span>
                  </td>
                  <td className="px-6 py-4 font-semibold text-brand-ink">
                    {u.institution_name || 'Apex Institute'}
                  </td>
                  <td className="px-6 py-4 font-mono font-medium text-brand-ink">
                    {new Date(u.due_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={u.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    {u.status !== 'VERIFIED' ? (
                      <div className="inline-flex gap-1.5 justify-end">
                        <button
                          onClick={() => handleVerifyUndertaking(u.id, 'VERIFIED')}
                          className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm transition-colors duration-150"
                        >
                          Verify Proof
                        </button>
                        <button
                          onClick={() => handleVerifyUndertaking(u.id, 'CORRECTION_REQUIRED')}
                          className="px-2.5 py-1 rounded text-xs font-semibold bg-[#99630D] text-white hover:bg-amber-800 shadow-sm transition-colors duration-150"
                        >
                          Require Cure
                        </button>
                      </div>
                    ) : (
                      <span className="text-emerald-700 dark:text-emerald-400 font-semibold text-xs flex items-center justify-end gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Regional Document Intelligence & Cross-Check Verification Desk */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-brand-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-brand-teal" />
              <h3 className="text-sm font-bold text-brand-ink">Document Intelligence & Regulatory Cross-Check Desk</h3>
            </div>
            <p className="text-xs text-brand-muted">
              Inspect candidate extraction findings, cross-check against recorded dates, and commit statutory review orders
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-brand-teal/10 text-brand-teal border border-brand-teal/20 self-start sm:self-auto">
            {documents.length} Tracked Documents
          </span>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[650px]">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Document Title & Type</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Version & Doc Number</th>
                <th className="px-6 py-3.5">Authoritative Expiry</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Intelligence Scrutiny</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4">
                    <p className="font-bold text-brand-ink">{doc.title}</p>
                    <span className="text-[10px] text-brand-teal font-mono">{doc.document_type.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="px-6 py-4 font-semibold text-brand-ink">
                    {doc.institution_name || 'Apex Institute of Technology'}
                  </td>
                  <td className="px-6 py-4 font-mono text-brand-ink">
                    v{doc.current_version} • <span className="text-brand-muted">{doc.document_number || 'N/A'}</span>
                  </td>
                  <td className="px-6 py-4 font-mono font-medium text-brand-ink">
                    {doc.expiry_date
                      ? new Date(doc.expiry_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                      : 'Continuous'}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleOpenDocIntelligence(doc)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                    >
                      <Cpu className="w-3.5 h-3.5" /> Intelligence Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Intelligence Modal */}
      <DocumentIntelligenceModal
        isOpen={intelModalOpen}
        onClose={() => setIntelModalOpen(false)}
        documentRecord={selectedDocForIntel}
        onRecordUpdated={loadData}
      />
    </div>
  );
};
export default RegionalOfficerWorkspace;
