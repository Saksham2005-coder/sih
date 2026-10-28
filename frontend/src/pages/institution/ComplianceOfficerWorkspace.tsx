import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileCheck2, AlertTriangle, ShieldCheck, Clock,
  Upload, CheckCircle2, ArrowRight, RefreshCw, FileText
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { ComplianceUndertaking, DocumentRecord } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { StatCard } from '../../components/common/StatCard';
import { Modal } from '../../components/common/Modal';

export const ComplianceOfficerWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Evidence submission state
  const [selectedUndertaking, setSelectedUndertaking] = useState<ComplianceUndertaking | null>(null);
  const [evidenceRemarks, setEvidenceRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Document renewal state
  const [selectedDoc, setSelectedDoc] = useState<DocumentRecord | null>(null);
  const [renewing, setRenewing] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [uList, dList] = await Promise.all([
        api.getUndertakings(),
        api.getDocuments(),
      ]);
      setUndertakings(uList);
      setDocuments(dList);
    } catch (err) {
      console.error('Failed to load compliance data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const overdueCount = undertakings.filter(u => u.status === 'OVERDUE').length;
  const dueSoonCount = undertakings.filter(u => u.status === 'DUE_SOON').length;
  const verifiedCount = undertakings.filter(u => u.status === 'VERIFIED').length;
  const expiringDocsCount = documents.filter(d => d.status === 'EXPIRING_SOON' || d.status === 'EXPIRED').length;

  const handleSubmitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndertaking) return;
    setSubmitting(true);
    try {
      const blob = new Blob(['%PDF-1.4 Institutional Compliance Verification Evidence for AICTE'], { type: 'application/pdf' });
      const file = new File([blob], `${selectedUndertaking.rule_code}_ComplianceProof.pdf`, { type: 'application/pdf' });
      const fd = new FormData();
      fd.append('file', file);
      fd.append('remarks', evidenceRemarks || 'Statutory compliance evidence uploaded by Compliance Officer.');

      await api.submitComplianceEvidence(selectedUndertaking.id, fd);
      setSelectedUndertaking(null);
      setEvidenceRemarks('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Evidence submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRenewDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;
    setRenewing(true);
    try {
      const blob = new Blob(['%PDF-1.4 Renewed Statutory Lease/NOC Document for AICTE'], { type: 'application/pdf' });
      const file = new File([blob], `${selectedDoc.document_type}_Renewal_2026.pdf`, { type: 'application/pdf' });
      const fd = new FormData();
      fd.append('file', file);

      await api.renewDocument(selectedDoc.id, fd);
      setSelectedDoc(null);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Document renewal failed');
    } finally {
      setRenewing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 dark:bg-teal-950/80 text-brand-teal dark:text-teal-300 border border-teal-300 dark:border-teal-700/80">
              INSTITUTION COMPLIANCE WORKSPACE
            </span>
            <span className="text-xs text-brand-muted">
              Scope: {user?.institution_name || 'Apex Institute'} • {user?.region || 'Western'} Region
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Compliance Passport & Statutory Document Office
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Operational Officer: <span className="font-semibold text-brand-ink">{user?.full_name}</span> (COMPLIANCE OFFICER) • Evidence Lifecycle & Validity Management
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors duration-150"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Records
        </button>
      </div>

      {/* Critical Overdue Warning Banner */}
      {overdueCount > 0 && (
        <div className="bg-rose-50 dark:bg-red-950/50 border border-rose-300 dark:border-red-700/80 rounded-xl p-4 shadow-sm flex items-start gap-3">
          <div className="p-2 bg-rose-100 dark:bg-red-900/60 text-[#B42332] dark:text-red-300 rounded-lg shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-brand-ink">
              {overdueCount} Statutory Compliance Obligation(s) Past SLA Due Date
            </h4>
            <p className="text-xs text-brand-muted mt-0.5">
              Overdue undertakings trigger automated multi-tier AICTE escalations (Regional Officer & Bureau). Please upload evidence immediately.
            </p>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total Obligations"
          value={undertakings.length}
          subtext="Statutory compliance covenants"
          icon={<FileCheck2 size={18} />}
        />
        <StatCard
          title="Overdue SLA"
          value={overdueCount}
          subtext="Breached compliance deadlines"
          icon={<AlertTriangle size={18} />}
          variant={overdueCount > 0 ? 'red' : 'default'}
        />
        <StatCard
          title="Due Soon"
          value={dueSoonCount}
          subtext="Approaching deadline (T-15)"
          icon={<Clock size={18} />}
          variant={dueSoonCount > 0 ? 'amber' : 'default'}
        />
        <StatCard
          title="Verified Covenants"
          value={verifiedCount}
          subtext="Signed off by AICTE RO"
          icon={<CheckCircle2 size={18} />}
        />
        <StatCard
          title="Expiring / Expired Docs"
          value={expiringDocsCount}
          subtext="Leases & Municipal NOCs"
          icon={<ShieldCheck size={18} />}
          variant={expiringDocsCount > 0 ? 'amber' : 'default'}
        />
      </div>

      {/* Primary Section: Active Compliance Obligations */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Statutory Compliance Covenants & Evidence Desk</h3>
            <p className="text-xs text-brand-muted">Mandatory undertakings prescribed under AICTE Approval Process Handbook (APH)</p>
          </div>
          <Link
            to="/institution/compliance"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Full Passport <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[700px]">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Obligation Title</th>
                <th className="px-6 py-3.5">Category & Rule</th>
                <th className="px-6 py-3.5">Due Date</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {undertakings.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4">
                    <p className="font-bold text-brand-ink">{u.title}</p>
                    <p className="text-[11px] text-brand-muted mt-0.5 line-clamp-1">{u.description}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-semibold text-brand-ink">{u.category}</span>
                    <span className="block text-[10px] text-brand-teal font-mono mt-0.5">{u.rule_code}</span>
                  </td>
                  <td className="px-6 py-4 font-mono font-medium">
                    {new Date(u.due_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={u.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    {u.status !== 'VERIFIED' ? (
                      <button
                        onClick={() => setSelectedUndertaking(u)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors duration-150"
                      >
                        <Upload className="w-3.5 h-3.5" /> Submit Evidence
                      </button>
                    ) : (
                      <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 flex items-center justify-end gap-1">
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

      {/* Secondary Section: Document Expiry & Renewal Watchlist */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Land Lease Deeds & Municipal Safety NOC Watchlist</h3>
            <p className="text-xs text-brand-muted">Version-controlled regulatory deeds with SHA-256 tamper verification</p>
          </div>
          <Link
            to="/institution/documents"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            All Documents <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[700px]">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Document Title</th>
                <th className="px-6 py-3.5">Issuing Authority</th>
                <th className="px-6 py-3.5">Validity Expiry</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {documents.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4">
                    <p className="font-bold text-brand-ink">{d.title}</p>
                    <p className="text-[11px] text-brand-muted font-mono mt-0.5">{d.document_number} • Ver {d.current_version}</p>
                  </td>
                  <td className="px-6 py-4 text-brand-ink font-medium">
                    {d.issuing_authority}
                  </td>
                  <td className="px-6 py-4 font-mono font-medium">
                    {d.expiry_date ? new Date(d.expiry_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Perpetual'}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={d.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    {d.renewal_required && (d.status === 'EXPIRING_SOON' || d.status === 'EXPIRED') ? (
                      <button
                        onClick={() => setSelectedDoc(d)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#99630D] text-white hover:bg-amber-800 shadow-sm transition-colors duration-150"
                      >
                        <Upload className="w-3.5 h-3.5" /> Renew Deed
                      </button>
                    ) : (
                      <span className="text-[11px] text-brand-muted font-medium">Compliant</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Submit Evidence */}
      {selectedUndertaking && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedUndertaking(null)}
          title={`Upload Compliance Proof: ${selectedUndertaking.title}`}
        >
          <form onSubmit={handleSubmitEvidence} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Rule: {selectedUndertaking.rule_code}</p>
              <p className="text-brand-muted">{selectedUndertaking.description}</p>
              <p className="font-mono text-brand-teal">Prescribed Evidence: {selectedUndertaking.evidence_type}</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Upload Evidence Document (PDF)</label>
              <div className="p-4 border-2 border-dashed border-brand-border rounded-lg text-center hover:border-brand-teal transition-colors">
                <FileText className="w-6 h-6 text-brand-teal mx-auto mb-1" />
                <p className="font-medium text-brand-ink">{selectedUndertaking.rule_code}_ComplianceProof.pdf</p>
                <p className="text-[10px] text-brand-muted mt-0.5">SHA-256 integrity checksum will be generated automatically upon submission.</p>
              </div>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Compliance Remarks & Implementation Notes</label>
              <textarea
                rows={3}
                required
                value={evidenceRemarks}
                onChange={(e) => setEvidenceRemarks(e.target.value)}
                placeholder="Detail the steps taken, procurement numbers, or municipal approvals..."
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white dark:bg-brand-surface-secondary text-brand-ink"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedUndertaking(null)}
                className="px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-100 dark:hover:bg-brand-surface-elevated font-semibold transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm transition-colors duration-150"
              >
                {submitting ? 'Submitting...' : 'Confirm Evidence Submission'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Renew Document */}
      {selectedDoc && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedDoc(null)}
          title={`Submit Document Renewal: ${selectedDoc.title}`}
        >
          <form onSubmit={handleRenewDocument} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Document No: {selectedDoc.document_number}</p>
              <p className="text-brand-muted">Issuing Authority: {selectedDoc.issuing_authority}</p>
              <p className="font-mono text-[#B42332] dark:text-red-400">Current Status: {selectedDoc.status}</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Attach Renewed Statutory Deed (PDF)</label>
              <div className="p-4 border-2 border-dashed border-brand-border rounded-lg text-center hover:border-brand-teal transition-colors">
                <FileText className="w-6 h-6 text-brand-teal mx-auto mb-1" />
                <p className="font-medium text-brand-ink">{selectedDoc.document_type}_Renewal_2026.pdf</p>
                <p className="text-[10px] text-brand-muted mt-0.5">Submitting will increment version to Ver {selectedDoc.current_version + 1} with SHA-256 hash preservation.</p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-100 dark:hover:bg-brand-surface-elevated font-semibold transition-colors duration-150"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={renewing}
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm transition-colors duration-150"
              >
                {renewing ? 'Uploading...' : 'Submit Renewal Version'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
export default ComplianceOfficerWorkspace;
