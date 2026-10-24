import React, { useEffect, useState } from 'react';
import { Files, Upload, AlertTriangle, CheckCircle, Clock, History } from 'lucide-react';
import { api } from '../../api/client';
import { DocumentRecord } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const DocumentsRenewals: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<DocumentRecord | null>(null);
  const [renewModalOpen, setRenewModalOpen] = useState(false);
  const [newExpiry, setNewExpiry] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadDocs = async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleOpenRenew = (doc: DocumentRecord) => {
    setSelectedDoc(doc);
    setNewExpiry('2028-12-31');
    setNotes('');
    setSelectedFile(null);
    setRenewModalOpen(true);
  };

  const handleRenewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;

    let fileToUpload = selectedFile;
    if (!fileToUpload) {
      const blob = new Blob(['%PDF-1.4 Mock Renewed Statutory Document for AICTE'], { type: 'application/pdf' });
      fileToUpload = new File([blob], `${selectedDoc.document_type}_Renewed_Signed.pdf`, { type: 'application/pdf' });
    }

    const formData = new FormData();
    formData.append('file', fileToUpload);
    formData.append('new_expiry_date', newExpiry);
    if (notes) formData.append('notes', notes);

    setSubmitting(true);
    try {
      await api.renewDocument(selectedDoc.id, formData);
      setRenewModalOpen(false);
      loadDocs();
    } catch (err: any) {
      alert(err.message || 'Renewal submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-brand-ink">Prescribed Documents & Validity Tracking</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Multi-year validity tracking for 33-year land leases, fire NOCs, and building certificates
        </p>
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 gap-6">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="bg-white rounded-xl border border-brand-border p-6 shadow-sm hover:border-brand-teal/50 transition-all"
          >
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-brand-border">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">
                    {doc.document_type.replace(/_/g, ' ')}
                  </span>
                  <StatusBadge status={doc.status} />
                </div>
                <h3 className="text-base font-bold text-brand-ink mt-1">{doc.title}</h3>
                <p className="text-xs text-brand-muted mt-0.5">
                  Doc Number: <span className="font-semibold text-brand-ink">{doc.document_number || 'N/A'}</span> • Current Version: v{doc.current_version}
                </p>
              </div>

              <button
                onClick={() => handleOpenRenew(doc)}
                className="px-3.5 py-1.5 rounded-lg bg-brand-teal hover:bg-brand-teal-dark text-white text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
              >
                <Upload className="w-3.5 h-3.5" /> Submit Document Renewal
              </button>
            </div>

            {/* Expiry Details */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-xs">
              <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
                <span className="text-brand-muted text-[10px] uppercase font-semibold">Issue Date:</span>
                <p className="font-bold text-brand-ink mt-0.5">
                  {doc.issue_date ? new Date(doc.issue_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}
                </p>
              </div>

              <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
                <span className="text-brand-muted text-[10px] uppercase font-semibold">Expiry Date:</span>
                <p className="font-bold text-brand-ink mt-0.5">
                  {doc.expiry_date ? new Date(doc.expiry_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Continuous'}
                </p>
              </div>

              <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
                <span className="text-brand-muted text-[10px] uppercase font-semibold">Total Versions Archived:</span>
                <p className="font-bold text-brand-teal mt-0.5">{doc.versions?.length || 1} Audited Versions</p>
              </div>
            </div>

            {/* Version History */}
            {doc.versions && doc.versions.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <h4 className="text-xs font-bold text-brand-ink flex items-center gap-1.5 mb-2">
                  <History className="w-3.5 h-3.5 text-brand-teal" /> Immutable Document Version History
                </h4>
                <div className="space-y-2">
                  {doc.versions.map((ver) => (
                    <div
                      key={ver.id}
                      className="p-3 rounded-lg border border-brand-border bg-gray-50/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-brand-ink">Version {ver.version}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-200 text-gray-700">
                            {ver.verification_status}
                          </span>
                        </div>
                        <p className="text-[11px] text-brand-muted mt-0.5">
                          File: <span className="text-brand-ink font-medium">{ver.file_name}</span> • SHA-256:{' '}
                          <span className="font-mono text-[9px]">{ver.checksum_sha256.substring(0, 16)}...</span>
                        </p>
                        {ver.verification_notes && (
                          <p className="text-[11px] text-teal-800 mt-1">Note: {ver.verification_notes}</p>
                        )}
                      </div>

                      <span className="text-[11px] text-brand-muted shrink-0">
                        {new Date(ver.uploaded_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Renewal Modal */}
      <Modal
        isOpen={renewModalOpen}
        onClose={() => setRenewModalOpen(false)}
        title="Submit Document Renewal"
        subtitle={selectedDoc?.title || ''}
      >
        <form onSubmit={handleRenewSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              New Validity Expiry Date
            </label>
            <input
              type="date"
              required
              value={newExpiry}
              onChange={(e) => setNewExpiry(e.target.value)}
              className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Select Signed Renewal Deed / Certificate (PDF, max 15MB)
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full border border-brand-border rounded-lg p-2 text-xs"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Renewal Remarks & Issuing Authority Details
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Sub-Registrar registration details, 5-year lease extension agreement..."
              className="w-full border border-brand-border rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setRenewModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-dark shadow-sm"
            >
              {submitting ? 'Submitting...' : 'Upload & Archive New Version'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
