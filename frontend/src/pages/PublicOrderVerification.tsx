import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  ShieldCheck, AlertTriangle, CheckCircle, XCircle, Search,
  Upload, FileText, ArrowLeft, RefreshCw, Hash, Lock, HelpCircle
} from 'lucide-react';
import { ordersApi } from '../api/client';
import { StatutoryOrderPublicVerificationData, OrderArtifactVerifyUploadData } from '../types';
import ThemeToggle from '../components/common/ThemeToggle';

export const PublicOrderVerification: React.FC = () => {
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const [inputToken, setInputToken] = useState(tokenFromUrl);
  const [tokenResult, setTokenResult] = useState<StatutoryOrderPublicVerificationData | null>(null);
  const [tokenLoading, setTokenLoading] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);

  // File Upload verification states
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<OrderArtifactVerifyUploadData | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'token' | 'file'>('token');

  const verifyToken = async (tok: string) => {
    if (!tok.trim()) return;
    setTokenLoading(true);
    setTokenError(null);
    setTokenResult(null);
    try {
      const data = await ordersApi.verifyOrderByToken(tok.trim());
      setTokenResult(data);
    } catch (err: any) {
      setTokenError(err?.message || 'Verification failed. The token could not be verified against the official AICTE registry.');
    } finally {
      setTokenLoading(false);
    }
  };

  useEffect(() => {
    if (tokenFromUrl) {
      setInputToken(tokenFromUrl);
      verifyToken(tokenFromUrl);
    }
  }, [tokenFromUrl]);

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    verifyToken(inputToken);
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF documents can be verified against the AICTE statutory order registry.');
      return;
    }
    setUploadFile(file);
    setUploadLoading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const res = await ordersApi.verifyOrderUpload(file);
      setUploadResult(res);
    } catch (err: any) {
      setUploadError(err?.message || 'Failed to verify file integrity.');
    } finally {
      setUploadLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-surface-canvas text-brand-text-primary flex flex-col">
      {/* Header */}
      <header className="border-b border-brand-border bg-brand-surface-secondary/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-teal/15 border border-brand-teal/30 flex items-center justify-center text-brand-teal">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-tight text-brand-text-primary">ReguFlow 360</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold bg-brand-teal/15 text-brand-teal border border-brand-teal/30">
                  PUBLIC VERIFICATION
                </span>
              </div>
              <p className="text-[11px] text-brand-text-muted">
                AICTE Statutory Decision Order Provenance & Integrity Portal
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link
              to="/login"
              className="px-3 py-1.5 bg-brand-surface border border-brand-border text-brand-text-primary rounded-lg text-xs font-medium hover:bg-brand-surface-elevated transition-colors inline-flex items-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Portal</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-8 space-y-6">
        {/* Banner */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-brand-text-primary">
            Official Order Authenticity & Cryptographic Verification
          </h1>
          <p className="text-xs text-brand-text-muted max-w-2xl mx-auto leading-relaxed">
            Verify the genuine issuance, persisted approval decision, artifact version, and cryptographic SHA-256
            integrity of an official AICTE statutory decision order issued under the Approval Process Handbook (APH).
          </p>
        </div>

        {/* Verification Method Tabs */}
        <div className="flex border-b border-brand-border max-w-md mx-auto">
          <button
            onClick={() => setActiveTab('token')}
            className={`flex-1 py-2.5 text-xs font-semibold text-center border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
              activeTab === 'token'
                ? 'border-brand-teal text-brand-teal'
                : 'border-transparent text-brand-text-muted hover:text-brand-text-primary'
            }`}
          >
            <Search className="w-4 h-4" />
            Verification Token / QR Code
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`flex-1 py-2.5 text-xs font-semibold text-center border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
              activeTab === 'file'
                ? 'border-brand-teal text-brand-teal'
                : 'border-transparent text-brand-text-muted hover:text-brand-text-primary'
            }`}
          >
            <Upload className="w-4 h-4" />
            Verify PDF File Checksum
          </button>
        </div>

        {/* Tab 1: Token Lookup */}
        {activeTab === 'token' && (
          <div className="space-y-6">
            <form onSubmit={handleTokenSubmit} className="max-w-2xl mx-auto flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-brand-text-muted absolute left-3 top-3" />
                <input
                  type="text"
                  value={inputToken}
                  onChange={e => setInputToken(e.target.value)}
                  placeholder="Enter 64-character verification token from document QR code..."
                  className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl border border-brand-border bg-brand-surface-elevated text-brand-text-primary focus:outline-none focus:ring-1 focus:ring-brand-teal font-mono shadow-sm"
                />
              </div>
              <button
                type="submit"
                disabled={tokenLoading || !inputToken.trim()}
                className="px-5 py-2.5 bg-brand-teal text-white rounded-xl text-xs font-semibold hover:bg-brand-teal/90 disabled:opacity-50 transition-colors shadow-sm inline-flex items-center gap-1.5 flex-shrink-0"
              >
                {tokenLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Verify Token
              </button>
            </form>

            {tokenError && (
              <div className="max-w-2xl mx-auto p-4 bg-brand-danger/10 border border-brand-danger/30 rounded-xl text-brand-danger text-xs flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-semibold">Verification Record Not Found</p>
                  <p>{tokenError}</p>
                </div>
              </div>
            )}

            {tokenResult && (
              <div className="bg-brand-surface-elevated rounded-2xl border border-brand-border shadow-lg overflow-hidden transition-colors">
                {/* Status Hero Banner */}
                <div className={`p-5 border-b ${
                  tokenResult.verification_status === 'VERIFIED_AUTHENTIC'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                    : tokenResult.verification_status === 'TAMPERED_HASH_MISMATCH'
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400'
                    : tokenResult.verification_status === 'REVOKED'
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400'
                    : 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400'
                }`}>
                  <div className="flex items-center gap-3">
                    {tokenResult.verification_status === 'VERIFIED_AUTHENTIC' ? (
                      <CheckCircle className="w-8 h-8 flex-shrink-0" />
                    ) : tokenResult.verification_status === 'REVOKED' ? (
                      <XCircle className="w-8 h-8 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-8 h-8 flex-shrink-0" />
                    )}
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm tracking-wide">
                          {tokenResult.verification_status === 'VERIFIED_AUTHENTIC'
                            ? 'GENUINE AICTE STATUTORY ORDER — CHECKSUM VERIFIED'
                            : tokenResult.verification_status === 'TAMPERED_HASH_MISMATCH'
                            ? 'INTEGRITY ALERT — CHECKSUM MISMATCH (FILE ALTERED)'
                            : tokenResult.verification_status === 'REVOKED'
                            ? 'STATUTORY ORDER REVOKED BY AICTE'
                            : 'SUPERSEDED ARTIFACT VERSION'}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase bg-black/10 dark:bg-white/10">
                          {tokenResult.decision}
                        </span>
                      </div>
                      <p className="text-xs mt-0.5 opacity-90">
                        {tokenResult.status_details}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Minimal Public Verification Metadata */}
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Order Reference Number</span>
                      <p className="text-sm font-mono font-bold text-brand-text-primary mt-0.5">
                        {tokenResult.order_number}
                      </p>
                    </div>

                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Application Number</span>
                      <p className="text-sm font-mono font-bold text-brand-text-primary mt-0.5">
                        {tokenResult.application_number}
                      </p>
                    </div>

                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Technical Institution Name</span>
                      <p className="text-xs font-semibold text-brand-text-primary mt-0.5">
                        {tokenResult.institution_name}
                      </p>
                    </div>

                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Regional Jurisdiction</span>
                      <p className="text-xs font-medium text-brand-text-primary mt-0.5">
                        {tokenResult.regional_office}
                      </p>
                    </div>

                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Date of Statutory Issuance</span>
                      <p className="text-xs font-medium text-brand-text-primary mt-0.5">
                        {new Date(tokenResult.order_date).toLocaleDateString()} (Version v{tokenResult.version}.0)
                      </p>
                    </div>

                    <div className="p-3 bg-brand-surface-secondary rounded-xl border border-brand-border">
                      <span className="text-[11px] font-semibold text-brand-text-muted uppercase">Order Registry Status</span>
                      <p className="text-xs font-mono font-bold text-brand-text-primary mt-0.5">
                        {tokenResult.status}
                      </p>
                    </div>
                  </div>

                  {/* SHA-256 Checksum Card */}
                  <div className="p-4 bg-brand-surface rounded-xl border border-brand-border space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-brand-text-muted uppercase">
                        <Hash className="w-3.5 h-3.5 text-brand-teal" />
                        <span>Registered SHA-256 Document Checksum</span>
                      </div>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                        tokenResult.artifact_hash_match
                          ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                          : 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                      }`}>
                        {tokenResult.artifact_hash_match ? 'HASH MATCH: VERIFIED' : 'HASH MISMATCH: TAMPERED'}
                      </span>
                    </div>
                    <p className="font-mono text-xs text-brand-text-primary break-all bg-brand-surface-secondary p-2.5 rounded-lg border border-brand-border/60">
                      {tokenResult.checksum_sha256}
                    </p>
                    <p className="text-[11px] text-brand-text-muted">
                      This cryptographic fingerprint uniquely anchors the physical PDF artifact. Any alteration of text, stamps, signatures, or pagination immediately modifies the computed digest and fails this verification test.
                    </p>
                  </div>

                  {/* Prototype Signature State & Explicit Boundary */}
                  <div className="p-4 bg-brand-amber/10 border border-brand-amber/30 rounded-xl space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-brand-amber">
                      <Lock className="w-4 h-4" />
                      <span>SIGNATURE STATUS: {tokenResult.signature_status || 'UNSIGNED_PROTOTYPE'}</span>
                    </div>
                    <p className="text-xs text-brand-text-muted leading-relaxed">
                      {tokenResult.signature_disclaimer ||
                        'This document is an UNSIGNED_PROTOTYPE generated for regulatory workflow evaluation under AICTE SIH 2026 PS 26262. It does not carry a legally binding digital signature under the Information Technology Act, 2000. Official statutory issuance requires integration with a licensed Certifying Authority (CCA) Digital Signature Certificate (DSC) or Aadhaar e-Sign gateway.'}
                    </p>
                    <div className="flex items-center gap-1 text-[11px] text-brand-amber/90 font-medium pt-1">
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>QR code establishes document reference provenance; it does not constitute a cryptographic digital signature certificate.</span>
                    </div>
                  </div>

                  {/* Revocation Warning if revoked */}
                  {tokenResult.is_revoked && (
                    <div className="p-4 bg-brand-danger/10 border border-brand-danger/30 rounded-xl space-y-1 text-xs text-brand-danger">
                      <p className="font-bold">Revocation Notice:</p>
                      <p>{tokenResult.revocation_reason}</p>
                    </div>
                  )}

                  {/* Footer provenance stamp */}
                  <div className="pt-2 border-t border-brand-border flex items-center justify-between text-[11px] text-brand-text-muted">
                    <span>Verified via AICTE ReguFlow 360 National Regulatory Registry</span>
                    <span>Query Time: {new Date(tokenResult.verified_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: File Checksum Verification */}
        {activeTab === 'file' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div
              onDragOver={e => e.preventDefault()}
              onDrop={e => {
                e.preventDefault();
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                  handleFileUpload(e.dataTransfer.files[0]);
                }
              }}
              className="border-2 border-dashed border-brand-border rounded-2xl p-8 text-center space-y-3 bg-brand-surface-secondary/50 hover:bg-brand-surface-secondary transition-colors"
            >
              <div className="w-12 h-12 mx-auto rounded-full bg-brand-teal/15 text-brand-teal flex items-center justify-center">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-brand-text-primary">
                  Upload an AICTE Statutory Decision Order PDF
                </h3>
                <p className="text-xs text-brand-text-muted mt-1">
                  Drag and drop the document here, or click below to select from your device.
                </p>
              </div>

              <input
                type="file"
                id="file-upload"
                accept=".pdf"
                className="hidden"
                onChange={e => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
              <label
                htmlFor="file-upload"
                className="inline-block px-4 py-2 bg-brand-teal text-white rounded-lg text-xs font-semibold hover:bg-brand-teal/90 transition-colors cursor-pointer shadow-sm"
              >
                Select PDF File
              </label>

              {uploadFile && (
                <p className="text-xs text-brand-text-muted font-mono pt-2">
                  Selected: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            {uploadLoading && (
              <div className="py-6 flex items-center justify-center gap-2 text-xs text-brand-text-muted">
                <RefreshCw className="w-4 h-4 animate-spin text-brand-teal" />
                <span>Computing SHA-256 cryptographic digest and verifying registry record...</span>
              </div>
            )}

            {uploadError && (
              <div className="p-4 bg-brand-danger/10 border border-brand-danger/30 rounded-xl text-brand-danger text-xs flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <p>{uploadError}</p>
              </div>
            )}

            {uploadResult && (
              <div className={`p-5 rounded-xl border space-y-3 ${
                uploadResult.is_match
                  ? 'bg-emerald-500/10 border-emerald-500/30'
                  : 'bg-rose-500/10 border-rose-500/30'
              }`}>
                <div className="flex items-center gap-3">
                  {uploadResult.is_match ? (
                    <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-6 h-6 text-rose-600 dark:text-rose-400 flex-shrink-0" />
                  )}
                  <div>
                    <h4 className="text-sm font-bold text-brand-text-primary">
                      {uploadResult.is_match
                        ? 'AUTHENTIC UNALTERED ARTIFACT VERIFIED'
                        : 'CHECKSUM MISMATCH / UNREGISTERED DOCUMENT'}
                    </h4>
                    <p className="text-xs text-brand-text-muted mt-0.5">
                      {uploadResult.message}
                    </p>
                  </div>
                </div>

                <div className="p-3 bg-brand-surface-secondary rounded-lg border border-brand-border space-y-1 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-brand-text-muted">Computed File SHA-256:</span>
                    <span className="font-bold text-brand-text-primary break-all ml-2">{uploadResult.computed_checksum_sha256}</span>
                  </div>
                  {uploadResult.stored_checksum_sha256 && (
                    <div className="flex justify-between">
                      <span className="text-brand-text-muted">Registry Registered SHA-256:</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400 break-all ml-2">{uploadResult.stored_checksum_sha256}</span>
                    </div>
                  )}
                  {uploadResult.order_number && (
                    <div className="flex justify-between pt-1 border-t border-brand-border/60">
                      <span className="text-brand-text-muted">Matched Order:</span>
                      <span className="font-bold text-brand-teal">{uploadResult.order_number}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-brand-border py-4 bg-brand-surface-secondary text-center text-xs text-brand-text-muted">
        AICTE ReguFlow 360 Verification Registry • Prototype for SIH 2026 AICTE Problem Statement 26262
      </footer>
    </div>
  );
};

export default PublicOrderVerification;
