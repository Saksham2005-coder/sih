import React, { useEffect, useState } from 'react';
import { CheckSquare, Check, X, FileText, Clock } from 'lucide-react';
import { api } from '../../api/client';
import { ComplianceUndertaking } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const ComplianceMonitoring: React.FC = () => {
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [selectedU, setSelectedU] = useState<ComplianceUndertaking | null>(null);
  const [outcome, setOutcome] = useState('VERIFIED');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadUndertakings = async () => {
    try {
      const data = await api.getUndertakings();
      setUndertakings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUndertakings();
  }, []);

  const handleOpenVerify = (u: ComplianceUndertaking) => {
    setSelectedU(u);
    setOutcome('VERIFIED');
    setNotes('Verified compliance evidence documents adhere to prescribed norms.');
    setVerifyModalOpen(true);
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedU) return;
    setSubmitting(true);
    try {
      await api.verifyCompliance(selectedU.id, {
        status: outcome,
        notes: notes,
      });
      setVerifyModalOpen(false);
      loadUndertakings();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-brand-ink">Institutional Compliance Verification Queue</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Review time-bound undertakings and verify cryptographic evidence submissions
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {undertakings.map((u) => (
          <div
            key={u.id}
            className="bg-white rounded-xl border border-brand-border p-6 shadow-sm hover:border-brand-teal/50 transition-all flex flex-col md:flex-row justify-between gap-6"
          >
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-brand-teal">{u.institution_name}</span>
                <span className="text-[10px] text-brand-muted uppercase">[{u.category}]</span>
                <StatusBadge status={u.status} />
              </div>

              <h3 className="text-sm font-bold text-brand-ink">{u.title}</h3>
              <p className="text-xs text-brand-muted">{u.description}</p>
              <p className="text-xs text-brand-muted flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-brand-teal" />
                Due Date: {new Date(u.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
              </p>

              {/* Submitted evidence list */}
              {u.evidences && u.evidences.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100 space-y-1">
                  <p className="text-[11px] font-semibold text-brand-ink">Attached Compliance Proof:</p>
                  {u.evidences.map((ev) => (
                    <div key={ev.id} className="text-xs text-brand-muted flex items-center gap-2">
                      <span className="font-bold text-brand-ink">v{ev.version}:</span>
                      <a href={ev.file_url} target="_blank" rel="noreferrer" className="text-brand-teal hover:underline flex items-center gap-1 font-medium">
                        <FileText className="w-3.5 h-3.5" /> {ev.file_name}
                      </a>
                      <span className="font-mono text-[9px] text-gray-400">({ev.checksum_sha256.substring(0, 14)}...)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex md:flex-col justify-end items-end gap-2 shrink-0">
              <button
                onClick={() => handleOpenVerify(u)}
                className="px-4 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-dark text-white text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
              >
                <Check className="w-3.5 h-3.5" /> Sign-off Verification
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Verification Modal */}
      <Modal
        isOpen={verifyModalOpen}
        onClose={() => setVerifyModalOpen(false)}
        title="Verify Compliance Evidence"
        subtitle={selectedU?.title || ''}
      >
        <form onSubmit={handleVerifySubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Verification Outcome
            </label>
            <select
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full border border-brand-border rounded-lg px-3 py-2 text-xs font-semibold focus:ring-1 focus:ring-brand-teal"
            >
              <option value="VERIFIED">VERIFIED — Evidence Conforms to Statutory Norms</option>
              <option value="CORRECTION_REQUIRED">CORRECTION_REQUIRED — Request Specific Cures / Correction</option>
              <option value="DEFICIENT">DEFICIENT — Evidence Incomplete or Inadequate</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Verification Notes & Scrutiny Observations
            </label>
            <textarea
              rows={3}
              required
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border border-brand-border rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setVerifyModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-dark shadow-sm"
            >
              {submitting ? 'Recording...' : 'Confirm Decision'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
