import React, { useState, useEffect } from 'react';
import {
  FileText, ShieldCheck, Download, ExternalLink, AlertTriangle,
  CheckCircle, Copy, Clock, RefreshCw, XCircle, Plus, Info, Ban
} from 'lucide-react';
import { Modal } from './Modal';
import { ordersApi } from '../../api/client';
import { StatutoryOrderData, User } from '../../types';

interface StatutoryOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: number;
  applicationNumber: string;
  applicationStage: string;
  currentUser?: User | null;
  onOrderChanged?: () => void;
}

export const StatutoryOrderModal: React.FC<StatutoryOrderModalProps> = ({
  isOpen,
  onClose,
  applicationId,
  applicationNumber,
  applicationStage,
  currentUser,
  onOrderChanged,
}) => {
  const [orders, setOrders] = useState<StatutoryOrderData[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<StatutoryOrderData | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  // Form states for generating order
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [customRemarks, setCustomRemarks] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [additionalConditions, setAdditionalConditions] = useState<string[]>([]);
  const [newConditionInput, setNewConditionInput] = useState('');

  // Revocation state
  const [showRevokeForm, setShowRevokeForm] = useState(false);
  const [revocationReason, setRevocationReason] = useState('');

  const isCompetentAuthority =
    currentUser?.roles?.includes('COMPETENT_AUTHORITY') ||
    currentUser?.roles?.includes('SYSTEM_ADMIN');

  const canGenerateOrder =
    isCompetentAuthority &&
    (applicationStage === 'APPROVED' || applicationStage === 'REJECTED');

  const fetchOrders = async () => {
    if (!applicationId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await ordersApi.getOrdersByApplication(applicationId);
      setOrders(data);
      if (data.length > 0) {
        // Select active order or highest version
        const active = data.find(o => o.status === 'ACTIVE') || data[0];
        setSelectedOrder(active);
      } else {
        setSelectedOrder(null);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load statutory orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchOrders();
      setShowGenerateForm(false);
      setShowRevokeForm(false);
    }
  }, [isOpen, applicationId]);

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleAddCondition = () => {
    if (newConditionInput.trim()) {
      setAdditionalConditions([...additionalConditions, newConditionInput.trim()]);
      setNewConditionInput('');
    }
  };

  const handleRemoveCondition = (index: number) => {
    setAdditionalConditions(additionalConditions.filter((_, i) => i !== index));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    setError(null);
    try {
      await ordersApi.generateOrder({
        application_id: applicationId,
        custom_remarks: customRemarks || undefined,
        additional_conditions: additionalConditions.length > 0 ? additionalConditions : undefined,
        override_reason: overrideReason || undefined,
      });
      setShowGenerateForm(false);
      setCustomRemarks('');
      setOverrideReason('');
      setAdditionalConditions([]);
      await fetchOrders();
      if (onOrderChanged) onOrderChanged();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate statutory order');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevoke = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;
    if (revocationReason.trim().length < 10) {
      setError('A substantive administrative justification (min 10 characters) is required to revoke an issued order.');
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await ordersApi.revokeOrder(selectedOrder.id, revocationReason.trim());
      setShowRevokeForm(false);
      setRevocationReason('');
      await fetchOrders();
      if (onOrderChanged) onOrderChanged();
    } catch (err: any) {
      setError(err?.message || 'Failed to revoke order');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownload = (orderId: number) => {
    const token = localStorage.getItem('reguflow_token');
    const url = ordersApi.getOrderDownloadUrl(orderId);
    // Authenticated download via anchor or new window
    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => {
        if (!res.ok) throw new Error('Download failed');
        return res.blob();
      })
      .then(blob => {
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = selectedOrder?.pdf_filename || `statutory_order_${applicationNumber}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(blobUrl);
      })
      .catch(err => {
        setError(err.message || 'Error downloading PDF');
      });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Statutory Decision Order & Integrity Dossier"
      subtitle={`Application: ${applicationNumber} | Civic Precision Official Records`}
      maxWidth="max-w-4xl"
    >
      <div className="space-y-6">
        {error && (
          <div className="p-3 bg-brand-danger/10 border border-brand-danger/30 rounded-lg text-brand-danger text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-xs font-semibold hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3 text-brand-text-muted">
            <RefreshCw className="w-6 h-6 animate-spin text-brand-teal" />
            <p className="text-sm">Retrieving registered statutory order artifacts...</p>
          </div>
        ) : orders.length === 0 && !showGenerateForm ? (
          <div className="py-10 text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-full bg-brand-surface-secondary border border-brand-border flex items-center justify-center text-brand-text-muted">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-brand-text-primary">No Statutory Order Issued</h4>
              <p className="text-sm text-brand-text-muted max-w-md mx-auto mt-1">
                {applicationStage === 'APPROVED' || applicationStage === 'REJECTED'
                  ? 'A statutory decision has been recorded by the Competent Authority. The official signed order artifact has not yet been generated.'
                  : `This application is currently in '${applicationStage}' stage. Statutory orders can only be generated after an official decision of APPROVED or REJECTED.`}
              </p>
            </div>
            {canGenerateOrder && (
              <button
                onClick={() => setShowGenerateForm(true)}
                className="px-4 py-2 bg-brand-teal text-white rounded-lg text-sm font-medium hover:bg-brand-teal/90 shadow-sm transition-colors inline-flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Generate Official Statutory Order
              </button>
            )}
          </div>
        ) : showGenerateForm ? (
          /* Generation Form */
          <form onSubmit={handleGenerate} className="space-y-4 bg-brand-surface p-5 rounded-xl border border-brand-border">
            <div className="flex items-center justify-between border-b border-brand-border pb-3">
              <div>
                <h4 className="text-sm font-semibold text-brand-text-primary">
                  {orders.length > 0 ? `Generate Order Addendum (Version ${orders.length + 1})` : 'Generate Formal Statutory Decision Order'}
                </h4>
                <p className="text-xs text-brand-text-muted">
                  Binds persisted application facts, conditions, undertakings, and SHA-256 hash.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowGenerateForm(false)}
                className="text-xs text-brand-text-muted hover:text-brand-text-primary"
              >
                Cancel
              </button>
            </div>

            {orders.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-brand-text-primary mb-1">
                  Reason for New Version / Superseding <span className="text-brand-danger">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={overrideReason}
                  onChange={e => setOverrideReason(e.target.value)}
                  placeholder="e.g. Supplementary conditions incorporated following EAC review"
                  className="w-full text-xs p-2.5 rounded-lg border border-brand-border bg-brand-surface-elevated text-brand-text-primary focus:outline-none focus:ring-1 focus:ring-brand-teal"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-brand-text-primary mb-1">
                Custom Statutory Remarks / Grounds (Optional)
              </label>
              <textarea
                rows={3}
                value={customRemarks}
                onChange={e => setCustomRemarks(e.target.value)}
                placeholder="Leave blank to use recorded decision remarks from the Competent Authority decision order..."
                className="w-full text-xs p-2.5 rounded-lg border border-brand-border bg-brand-surface-elevated text-brand-text-primary focus:outline-none focus:ring-1 focus:ring-brand-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-brand-text-primary mb-1">
                Additional Order Conditions (Optional)
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={newConditionInput}
                  onChange={e => setNewConditionInput(e.target.value)}
                  placeholder="Add specific time-bound condition..."
                  className="flex-1 text-xs p-2 rounded-lg border border-brand-border bg-brand-surface-elevated text-brand-text-primary focus:outline-none focus:ring-1 focus:ring-brand-teal"
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddCondition();
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddCondition}
                  className="px-3 py-1.5 bg-brand-surface-secondary border border-brand-border text-brand-text-primary rounded-lg text-xs hover:bg-brand-surface transition-colors"
                >
                  Add
                </button>
              </div>

              {additionalConditions.length > 0 && (
                <ul className="space-y-1 mt-2">
                  {additionalConditions.map((cond, idx) => (
                    <li key={idx} className="flex items-center justify-between text-xs bg-brand-surface-secondary p-2 rounded border border-brand-border">
                      <span className="text-brand-text-primary">• {cond}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCondition(idx)}
                        className="text-brand-danger hover:underline text-[11px]"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="p-3 bg-brand-amber/10 border border-brand-amber/30 rounded-lg text-xs text-brand-amber flex items-start gap-2">
              <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Statutory Authority Bound Invariant</p>
                <p className="mt-0.5 text-[11px]">
                  Artifact generation does not mutate the application's statutory status. The generated PDF will be issued as an
                  <span className="font-semibold"> UNSIGNED_PROTOTYPE</span> with verifiable cryptographic SHA-256 integrity and QR validation link.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowGenerateForm(false)}
                className="px-4 py-2 border border-brand-border text-brand-text-muted rounded-lg text-xs hover:text-brand-text-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading}
                className="px-4 py-2 bg-brand-teal text-white rounded-lg text-xs font-medium hover:bg-brand-teal/90 disabled:opacity-50 flex items-center gap-2"
              >
                {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Generate and Record Order
              </button>
            </div>
          </form>
        ) : showRevokeForm ? (
          /* Revocation Form */
          <form onSubmit={handleRevoke} className="space-y-4 bg-brand-danger/5 p-5 rounded-xl border border-brand-danger/30">
            <div className="flex items-center justify-between border-b border-brand-danger/20 pb-3">
              <div className="flex items-center gap-2 text-brand-danger">
                <Ban className="w-5 h-5" />
                <h4 className="text-sm font-semibold">Revoke Statutory Order ({selectedOrder?.order_number})</h4>
              </div>
              <button
                type="button"
                onClick={() => setShowRevokeForm(false)}
                className="text-xs text-brand-text-muted hover:text-brand-text-primary"
              >
                Cancel
              </button>
            </div>

            <p className="text-xs text-brand-text-muted">
              Revoking an order permanently invalidates the public verification token and marks the artifact as REVOKED across the registry.
              A mandatory statutory justification must be logged for the regulatory audit trail.
            </p>

            <div>
              <label className="block text-xs font-medium text-brand-text-primary mb-1">
                Official Revocation Justification <span className="text-brand-danger">*</span>
              </label>
              <textarea
                required
                rows={3}
                value={revocationReason}
                onChange={e => setRevocationReason(e.target.value)}
                placeholder="State the official administrative grounds for order revocation (min 10 characters)..."
                className="w-full text-xs p-2.5 rounded-lg border border-brand-border bg-brand-surface-elevated text-brand-text-primary focus:outline-none focus:ring-1 focus:ring-brand-danger"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowRevokeForm(false)}
                className="px-4 py-2 border border-brand-border text-brand-text-muted rounded-lg text-xs hover:text-brand-text-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={actionLoading || revocationReason.trim().length < 10}
                className="px-4 py-2 bg-brand-danger text-white rounded-lg text-xs font-medium hover:bg-brand-danger/90 disabled:opacity-50 flex items-center gap-2"
              >
                {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Confirm Order Revocation
              </button>
            </div>
          </form>
        ) : selectedOrder ? (
          /* Main Order Display */
          <div className="space-y-6">
            {/* Version Switcher if multiple orders */}
            {orders.length > 1 && (
              <div className="flex items-center gap-2 border-b border-brand-border pb-3 overflow-x-auto">
                <span className="text-xs font-semibold text-brand-text-muted uppercase tracking-wider">Versions:</span>
                {orders.map(ord => (
                  <button
                    key={ord.id}
                    onClick={() => setSelectedOrder(ord)}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                      selectedOrder.id === ord.id
                        ? 'bg-brand-teal text-white shadow-sm'
                        : 'bg-brand-surface-secondary text-brand-text-muted hover:text-brand-text-primary border border-brand-border'
                    }`}
                  >
                    <span>v{ord.version}.0</span>
                    <span className={`text-[10px] px-1 py-0.2 rounded font-mono ${
                      ord.status === 'ACTIVE'
                        ? 'bg-white/20 text-white'
                        : ord.status === 'REVOKED'
                        ? 'bg-brand-danger/20 text-brand-danger'
                        : 'bg-brand-amber/20 text-brand-amber'
                    }`}>
                      {ord.status}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Header Status Card */}
            <div className="bg-brand-surface-secondary p-4 rounded-xl border border-brand-border flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`px-2 py-0.5 text-xs font-bold rounded-md ${
                    selectedOrder.decision === 'APPROVED'
                      ? 'bg-brand-teal/15 text-brand-teal border border-brand-teal/30'
                      : 'bg-brand-danger/15 text-brand-danger border border-brand-danger/30'
                  }`}>
                    {selectedOrder.decision === 'APPROVED' ? 'STATUTORY APPROVAL' : 'STATUTORY REJECTION'}
                  </span>
                  <span className={`px-2 py-0.5 text-xs font-mono font-medium rounded-md ${
                    selectedOrder.status === 'ACTIVE'
                      ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                      : selectedOrder.status === 'REVOKED'
                      ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                      : 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                  }`}>
                    STATUS: {selectedOrder.status}
                  </span>
                  <span className="text-xs text-brand-text-muted">
                    Version {selectedOrder.version}.0
                  </span>
                </div>
                <h3 className="text-base font-mono font-bold text-brand-text-primary tracking-tight">
                  {selectedOrder.order_number}
                </h3>
                <p className="text-xs text-brand-text-muted flex items-center gap-3">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    Issued: {new Date(selectedOrder.order_date).toLocaleDateString()}
                  </span>
                  <span>•</span>
                  <span>Signatory: {selectedOrder.issued_by_name}</span>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => handleDownload(selectedOrder.id)}
                  className="px-3 py-1.5 bg-brand-teal text-white rounded-lg text-xs font-medium hover:bg-brand-teal/90 shadow-sm transition-colors inline-flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download PDF Order
                </button>
                <a
                  href={`/verify-order?token=${selectedOrder.verification_token}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 bg-brand-surface border border-brand-border text-brand-text-primary rounded-lg text-xs font-medium hover:bg-brand-surface-elevated transition-colors inline-flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5 text-brand-teal" />
                  Public Verification
                </a>
              </div>
            </div>

            {/* Prototype Signature State & Regulatory Disclosure */}
            <div className="p-3.5 bg-brand-amber/10 border border-brand-amber/30 rounded-xl space-y-1.5">
              <div className="flex items-center gap-2 text-brand-amber font-semibold text-xs">
                <ShieldCheck className="w-4 h-4 text-brand-amber" />
                <span>SIGNATURE INTEGRITY STATE: {selectedOrder.signature_status}</span>
              </div>
              <p className="text-xs text-brand-text-muted leading-relaxed">
                {selectedOrder.signature_disclaimer}
              </p>
            </div>

            {/* Cryptographic Verification & Provenance Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 bg-brand-surface rounded-xl border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-brand-text-muted uppercase">SHA-256 Artifact Digest</span>
                  <button
                    onClick={() => handleCopyHash(selectedOrder.checksum_sha256)}
                    className="text-[11px] text-brand-teal hover:underline flex items-center gap-1"
                  >
                    {copiedHash ? <CheckCircle className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    {copiedHash ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="p-2 bg-brand-surface-secondary rounded font-mono text-[11px] text-brand-text-primary break-all border border-brand-border/60">
                  {selectedOrder.checksum_sha256}
                </div>
                <p className="text-[11px] text-brand-text-muted">
                  Exact immutable checksum of the generated physical PDF. Any post-issuance file alteration fails integrity verification.
                </p>
              </div>

              <div className="p-3.5 bg-brand-surface rounded-xl border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-brand-text-muted uppercase">Verification Token</span>
                  <span className="text-[11px] font-mono text-brand-teal">64-char Non-Guessable</span>
                </div>
                <div className="p-2 bg-brand-surface-secondary rounded font-mono text-[11px] text-brand-text-primary break-all border border-brand-border/60">
                  {selectedOrder.verification_token}
                </div>
                <p className="text-[11px] text-brand-text-muted">
                  Embedded in the document QR code. Discloses minimal provenance metadata without exposing confidential applicant dossiers.
                </p>
              </div>
            </div>

            {/* Operative Decision Grounds & Conditions */}
            <div className="space-y-3">
              <div className="p-3.5 bg-brand-surface rounded-xl border border-brand-border space-y-1">
                <h4 className="text-xs font-semibold text-brand-text-muted uppercase">Competent Authority Grounds & Remarks</h4>
                <p className="text-xs text-brand-text-primary leading-relaxed whitespace-pre-wrap">
                  {selectedOrder.decision_remarks}
                </p>
              </div>

              {selectedOrder.conditions && selectedOrder.conditions.length > 0 && (
                <div className="p-3.5 bg-brand-surface rounded-xl border border-brand-border space-y-2">
                  <h4 className="text-xs font-semibold text-brand-text-muted uppercase">Applicable Conditions & Time-Bound Undertakings</h4>
                  <ul className="space-y-1.5">
                    {selectedOrder.conditions.map((c, i) => (
                      <li key={i} className="text-xs flex items-start gap-2 text-brand-text-primary">
                        <span className="text-brand-teal font-mono text-[11px] flex-shrink-0 mt-0.5">[{c.rule_code || `C-${i+1}`}]</span>
                        <div className="flex-1">
                          <span>{c.title}</span>
                          {c.due_date && (
                            <span className="ml-2 text-[11px] text-brand-text-muted font-mono">
                              (Due: {c.due_date})
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Superseding / Revocation Notices if applicable */}
              {selectedOrder.is_revoked && (
                <div className="p-3 bg-brand-danger/10 border border-brand-danger/30 rounded-xl text-xs space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-brand-danger">
                    <XCircle className="w-4 h-4" />
                    <span>ORDER FORMALLY REVOKED</span>
                  </div>
                  <p className="text-brand-text-primary">
                    <span className="font-semibold">Reason:</span> {selectedOrder.revocation_reason}
                  </p>
                  {selectedOrder.revoked_at && (
                    <p className="text-[11px] text-brand-text-muted">
                      Revocation recorded on {new Date(selectedOrder.revoked_at).toLocaleString()}
                    </p>
                  )}
                </div>
              )}

              {selectedOrder.status === 'SUPERSEDED' && (
                <div className="p-3 bg-brand-amber/10 border border-brand-amber/30 rounded-xl text-xs space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-brand-amber">
                    <AlertTriangle className="w-4 h-4" />
                    <span>SUPERSEDED ARTIFACT VERSION</span>
                  </div>
                  <p className="text-brand-text-primary">
                    This order version has been superseded by a newer version. It is maintained in the audit record for complete provenance traceability.
                  </p>
                  {selectedOrder.superseding_reason && (
                    <p className="text-[11px] text-brand-text-muted">
                      Reason: {selectedOrder.superseding_reason}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Officer Action Bar (Generate Addendum / Revoke) */}
            {canGenerateOrder && (
              <div className="flex items-center justify-between pt-2 border-t border-brand-border">
                <div className="text-xs text-brand-text-muted">
                  Competent Authority Action Console
                </div>
                <div className="flex items-center gap-3">
                  {selectedOrder.status === 'ACTIVE' && (
                    <button
                      onClick={() => setShowRevokeForm(true)}
                      className="px-3 py-1.5 border border-brand-danger/30 text-brand-danger rounded-lg text-xs hover:bg-brand-danger/10 transition-colors inline-flex items-center gap-1"
                    >
                      <Ban className="w-3.5 h-3.5" />
                      Revoke Order
                    </button>
                  )}
                  <button
                    onClick={() => setShowGenerateForm(true)}
                    className="px-3 py-1.5 bg-brand-teal text-white rounded-lg text-xs font-medium hover:bg-brand-teal/90 transition-colors inline-flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Issue New Version / Addendum
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </Modal>
  );
};

export default StatutoryOrderModal;
