import React, { useEffect, useState } from 'react';
import { CheckSquare, Upload, Filter, FileText, CheckCircle2, Clock } from 'lucide-react';
import { api } from '../../api/client';
import { ComplianceUndertaking } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const CompliancePassport: React.FC = () => {
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedUndertaking, setSelectedUndertaking] = useState<ComplianceUndertaking | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [remarks, setRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadUndertakings = async () => {
    try {
      const data = await api.getUndertakings({ status_filter: statusFilter || undefined });
      setUndertakings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUndertakings();
  }, [statusFilter]);

  const handleOpenUpload = (u: ComplianceUndertaking) => {
    setSelectedUndertaking(u);
    setSelectedFile(null);
    setRemarks('');
    setUploadModalOpen(true);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndertaking) return;
    
    // Create synthetic file if none selected for seamless demo
    let fileToUpload = selectedFile;
    if (!fileToUpload) {
      const blob = new Blob(['%PDF-1.4 Mock Compliance Verification Evidence for AICTE'], { type: 'application/pdf' });
      fileToUpload = new File([blob], `${selectedUndertaking.category}_Proof_Document.pdf`, { type: 'application/pdf' });
    }

    const formData = new FormData();
    formData.append('file', fileToUpload);
    if (remarks) formData.append('remarks', remarks);

    setSubmitting(true);
    try {
      await api.submitComplianceEvidence(selectedUndertaking.id, formData);
      setUploadModalOpen(false);
      loadUndertakings();
    } catch (err: any) {
      alert(err.message || 'Evidence upload failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink">Institutional Compliance Passport</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-brand-teal border border-teal-300">
              Verified Dossier
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Continuous regulatory compliance tracking across time-bound undertakings and statutory evidence
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-brand-muted dark:text-brand-muted" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal"
          >
            <option value="">All Undertaking States</option>
            <option value="OVERDUE">Overdue</option>
            <option value="DUE_SOON">Due Soon</option>
            <option value="PENDING_VERIFICATION">Pending Verification</option>
            <option value="CORRECTION_REQUIRED">Correction Required</option>
            <option value="UNDER_VERIFICATION">Under Verification</option>
            <option value="VERIFIED">Verified</option>
            <option value="DEFICIENT">Deficient</option>
            <option value="NOT_YET_DUE">Not Yet Due</option>
          </select>
        </div>
      </div>

      {/* Undertakings Grid */}
      <div className="grid grid-cols-1 gap-4">
        {undertakings.length === 0 ? (
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-12 text-center text-xs text-brand-muted dark:text-brand-muted transition-colors">
            No compliance undertakings found for selected filter.
          </div>
        ) : (
          undertakings.map((u) => (
            <div
              key={u.id}
              className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-5 shadow-sm hover:border-brand-teal/50 hover:shadow-md transition-all flex flex-col md:flex-row justify-between gap-4"
            >
              <div className="space-y-2 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-brand-muted dark:text-brand-muted">
                    [{u.category}]
                  </span>
                  <StatusBadge status={u.effective_status || u.status} />
                </div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink">{u.title}</h3>
                <p className="text-xs text-brand-muted dark:text-brand-muted">{u.description}</p>
                
                <div className="flex flex-wrap items-center gap-4 text-xs pt-1 text-brand-muted dark:text-brand-muted">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-brand-teal" />
                    Due Date: {new Date(u.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </span>
                  {u.verified_at && (
                    <span className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" />
                      Verified on {new Date(u.verified_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  )}
                </div>

                {/* Evidence history if present */}
                {u.evidences && u.evidences.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-brand-border/60 dark:border-brand-border">
                    <p className="text-[11px] font-semibold text-brand-ink dark:text-brand-ink mb-1">Submitted Evidence History:</p>
                    <div className="space-y-1">
                      {u.evidences.map((ev) => (
                        <div key={ev.id} className="text-[11px] text-brand-muted dark:text-brand-muted flex flex-col gap-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-brand-ink dark:text-brand-ink">v{ev.version}:</span>
                            <span>{ev.file_name}</span>
                            <span className="font-mono text-[9px] text-brand-muted">({ev.checksum_sha256.substring(0, 10)}...)</span>
                            {ev.verification_status && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-brand-porcelain dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink border border-brand-border/60 dark:border-brand-border">
                                {ev.verification_status}
                              </span>
                            )}
                          </div>
                          {ev.verification_notes && (
                            <p className="text-[10px] text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 rounded px-2 py-0.5 border border-amber-200 dark:border-amber-800/40">
                              Remarks: {ev.verification_notes}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex md:flex-col justify-end items-end gap-2 shrink-0">
                <button
                  onClick={() => handleOpenUpload(u)}
                  className="px-3.5 py-1.5 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  {u.evidences?.length > 0 ? 'Submit Revision Evidence' : 'Submit Evidence'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Submit Compliance Evidence"
        subtitle={selectedUndertaking?.title || ''}
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Select Proof Document (PDF, max 15MB)
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2 text-xs"
            />
            <p className="text-[10px] text-brand-muted dark:text-brand-muted mt-1">
              File integrity will be sealed via SHA-256 checksum upon submission.
            </p>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Compliance Notes & Description
            </label>
            <textarea
              rows={3}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Detail installation specs, completion dates, or compliance particulars..."
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setUploadModalOpen(false)}
              className="px-4 py-2 border border-brand-border dark:border-brand-border rounded-lg text-brand-ink dark:text-brand-ink font-semibold hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-hover shadow-sm transition-colors"
            >
              {submitting ? 'Uploading...' : 'Confirm & Submit'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
