import React, { useEffect, useState } from 'react';
import {
  FileText, ShieldCheck, AlertTriangle, CheckCircle2, Clock,
  RefreshCw, Cpu, Check, AlertOctagon, Info, ChevronRight, FileSearch
} from 'lucide-react';
import { Modal } from './Modal';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { DocumentRecord, DocumentVersion, DocumentAnalysisData, CrossCheckFinding } from '../../types';

interface DocumentIntelligenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentRecord?: DocumentRecord | null;
  documentVersionId?: number | null;
  complianceEvidenceId?: number | null;
  onRecordUpdated?: () => void;
}

export const DocumentIntelligenceModal: React.FC<DocumentIntelligenceModalProps> = ({
  isOpen,
  onClose,
  documentRecord,
  documentVersionId,
  complianceEvidenceId,
  onRecordUpdated,
}) => {
  const { user, activeRole } = useAuth();
  const [analysis, setAnalysis] = useState<DocumentAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Officer review form state
  const [decision, setDecision] = useState<'CONFIRMED' | 'CORRECTED' | 'REJECTED'>('CONFIRMED');
  const [remarks, setRemarks] = useState('');
  const [applyToRecord, setApplyToRecord] = useState(false);
  const [correctExpiry, setCorrectExpiry] = useState('');
  const [correctDocNum, setCorrectDocNum] = useState('');
  const [correctAuthority, setCorrectAuthority] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState(false);

  const isOfficer = ['REGIONAL_OFFICER', 'BUREAU_OFFICER', 'SYSTEM_ADMIN'].includes(
    activeRole || user?.roles?.[0] || ''
  );

  const activeVersionId =
    documentVersionId ||
    (documentRecord?.versions && documentRecord.versions.length > 0
      ? documentRecord.versions[documentRecord.versions.length - 1].id
      : null);

  const activeVersion: DocumentVersion | undefined = documentRecord?.versions?.find(
    (v) => v.id === activeVersionId
  );

  const loadAnalysis = async () => {
    if (!isOpen) return;
    setError(null);
    setLoading(true);
    try {
      if (activeVersionId) {
        const data = await api.getDocumentAnalysisByVersion(activeVersionId);
        setAnalysis(data);
        if (data.reviewer_decision) {
          setDecision(data.reviewer_decision as any);
        }
      } else if (documentRecord?.id) {
        const list = await api.getDocumentAnalyses({ document_record_id: documentRecord.id });
        if (list.length > 0) {
          setAnalysis(list[0]);
        } else {
          // Trigger initial analysis
          const trig = await api.triggerDocumentAnalysis({ document_record_id: documentRecord.id });
          setAnalysis(trig);
        }
      }
    } catch (err: any) {
      console.error('Failed to load document analysis', err);
      setError(err.message || 'Failed to retrieve document analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadAnalysis();
      setRemarks('');
      setReviewSuccess(false);
    }
  }, [isOpen, activeVersionId, documentRecord?.id]);

  const handleRetrigger = async () => {
    setTriggering(true);
    setError(null);
    try {
      const updated = await api.triggerDocumentAnalysis({
        document_version_id: activeVersionId || undefined,
        document_record_id: documentRecord?.id || undefined,
        force_retry: true,
      });
      setAnalysis(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to re-analyze document');
    } finally {
      setTriggering(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!analysis) return;
    if (remarks.trim().length < 5) {
      alert('Review remarks are mandatory (minimum 5 characters).');
      return;
    }

    const correctedPayload: Record<string, any> = {};
    if (decision === 'CORRECTED') {
      if (correctExpiry) correctedPayload['expiry_date'] = correctExpiry;
      if (correctDocNum) correctedPayload['document_number'] = correctDocNum;
      if (correctAuthority) correctedPayload['issuing_authority'] = correctAuthority;
    }

    setSubmittingReview(true);
    try {
      const res = await api.reviewDocumentAnalysis(analysis.id, {
        decision,
        reviewer_remarks: remarks.trim(),
        apply_to_record: applyToRecord,
        corrected_fields: Object.keys(correctedPayload).length > 0 ? correctedPayload : undefined,
      });
      setAnalysis(res);
      setReviewSuccess(true);
      if (onRecordUpdated) onRecordUpdated();
    } catch (err: any) {
      alert(err.message || 'Review submission failed');
    } finally {
      setSubmittingReview(false);
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'CONFIRMED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center gap-1">
            <Check className="w-3 h-3" /> CONFIRMED
          </span>
        );
      case 'REVIEW_REQUIRED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> REVIEW REQUIRED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-300 dark:border-sky-800 flex items-center gap-1 animate-pulse">
            <RefreshCw className="w-3 h-3 animate-spin" /> PROCESSING
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-300 dark:border-rose-800 flex items-center gap-1">
            <AlertOctagon className="w-3 h-3" /> FAILED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border border-gray-300 dark:border-gray-700">
            {st}
          </span>
        );
    }
  };

  const getFindingStatusBadge = (fStatus: string) => {
    switch (fStatus) {
      case 'MATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
            <Check className="w-3 h-3" /> MATCH
          </span>
        );
      case 'POSSIBLE_MISMATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200 dark:border-rose-800 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> POSSIBLE MISMATCH
          </span>
        );
      case 'MISSING_EVIDENCE':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200 dark:border-amber-800 flex items-center gap-1">
            <Info className="w-3 h-3" /> MISSING EVIDENCE
          </span>
        );
      case 'EXTRACTION_UNAVAILABLE':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-300 dark:border-slate-700 flex items-center gap-1">
            <Cpu className="w-3 h-3" /> OCR UNAVAILABLE
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
            {fStatus}
          </span>
        );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Document Intelligence & Compliance Cross-Check"
      subtitle={documentRecord?.title || activeVersion?.file_name || 'Regulatory Evidence Extraction'}
      maxWidth="max-w-4xl"
    >
      <div className="space-y-6 text-xs text-brand-text-primary">
        {/* Header Telemetry Strip */}
        <div className="p-4 rounded-xl border border-brand-border bg-brand-surface-secondary flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-brand-ink">
                {documentRecord?.title || 'Document Record'}
              </span>
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-brand-surface border border-brand-border text-brand-teal">
                v{activeVersion?.version || analysis?.document_version_id || 1}
              </span>
              {analysis && getStatusBadge(analysis.status)}
            </div>
            <p className="text-[11px] text-brand-muted">
              File: <strong className="text-brand-ink">{analysis?.file_name || activeVersion?.file_name || 'N/A'}</strong>{' '}
              • SHA-256: <span className="font-mono text-[10px]">{analysis?.checksum_sha256?.substring(0, 16)}...</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded text-[10px] font-mono font-semibold bg-brand-surface border border-brand-border text-brand-muted">
              Engine: {analysis?.extraction_engine || 'pypdf-text-v1'}
            </span>
            <span
              className={`px-2 py-1 rounded text-[10px] font-mono font-semibold border ${
                analysis?.ocr_provider === 'TESSERACT_LOCAL'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/50 dark:border-emerald-800'
                  : 'bg-slate-50 text-slate-600 border-slate-300 dark:bg-slate-900/50 dark:border-slate-700'
              }`}
            >
              OCR: {analysis?.ocr_provider || 'UNAVAILABLE'}
            </span>
            <button
              onClick={handleRetrigger}
              disabled={triggering}
              className="p-1.5 rounded-lg border border-brand-border bg-brand-surface hover:bg-brand-surface-elevated text-brand-ink transition-colors flex items-center gap-1 font-semibold text-[11px]"
              title="Re-run extraction scan"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${triggering ? 'animate-spin text-brand-teal' : ''}`} />
              Re-Scan
            </button>
          </div>
        </div>

        {loading && (
          <div className="p-8 text-center text-brand-muted flex flex-col items-center justify-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-brand-teal" />
            <p className="text-xs">Extracting embedded text layer and evaluating regulatory cross-checks...</p>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg border border-rose-300 bg-rose-50 dark:bg-rose-950/50 text-rose-800 dark:text-rose-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {analysis && !loading && (
          <>
            {/* Reliability & Overview Gauge Card */}
            <div className="p-4 rounded-xl border border-brand-border bg-brand-surface grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">
                  Extraction Reliability
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-brand-teal font-mono">
                    {Math.round((analysis.overall_confidence || 0) * 100)}%
                  </span>
                  <span className="text-[11px] text-brand-muted">
                    {analysis.has_text_layer ? 'Text Layer Validated' : 'Scanned / Non-Text Layer'}
                  </span>
                </div>
                <div className="w-full bg-brand-surface-secondary rounded-full h-1.5 overflow-hidden border border-brand-border/40">
                  <div
                    className="bg-brand-teal h-full transition-all duration-500"
                    style={{ width: `${Math.min(100, Math.round((analysis.overall_confidence || 0) * 100))}%` }}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">
                  Pages & Layout
                </span>
                <p className="text-sm font-semibold text-brand-ink">
                  {analysis.page_count} Page(s) Scanned
                </p>
                <p className="text-[11px] text-brand-muted">
                  {analysis.is_scanned
                    ? 'Raster image container detected'
                    : 'Digital vector PDF with native text font metrics'}
                </p>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] uppercase font-bold text-brand-muted tracking-wider">
                  Cross-Check Findings
                </span>
                <p className="text-sm font-semibold text-brand-ink">
                  {analysis.cross_check_findings?.length || 0} Rule Finding(s)
                </p>
                <p className="text-[11px] text-brand-muted">
                  {analysis.summary_findings || 'Evaluation completed without unhandled exceptions.'}
                </p>
              </div>
            </div>

            {/* Cross-Check Findings Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-teal" />
                  Regulatory Cross-Check Findings
                </h4>
                <span className="text-[11px] text-brand-muted">
                  Conservative fact cross-checking against database records
                </span>
              </div>

              <div className="space-y-2">
                {analysis.cross_check_findings && analysis.cross_check_findings.length > 0 ? (
                  analysis.cross_check_findings.map((f: CrossCheckFinding, idx: number) => (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-lg border text-xs transition-colors ${
                        f.status === 'POSSIBLE_MISMATCH'
                          ? 'border-rose-300 bg-rose-50/50 dark:bg-rose-950/20 dark:border-rose-900'
                          : f.status === 'MATCH'
                          ? 'border-emerald-300 bg-emerald-50/50 dark:bg-emerald-950/20 dark:border-emerald-900'
                          : f.status === 'MISSING_EVIDENCE'
                          ? 'border-amber-300 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-900'
                          : 'border-brand-border bg-brand-surface-secondary'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          {getFindingStatusBadge(f.status)}
                          <span className="font-mono text-[10px] text-brand-muted font-bold">
                            {f.rule_code}
                          </span>
                        </div>
                        {f.source_page && (
                          <span className="text-[10px] font-semibold text-brand-muted px-2 py-0.5 rounded bg-brand-surface border border-brand-border">
                            Page {f.source_page}
                          </span>
                        )}
                      </div>

                      <p className="font-semibold text-brand-ink">{f.description}</p>

                      {(f.entered_value || f.extracted_value) && (
                        <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-2 border-t border-brand-border/40">
                          <div>
                            <span className="text-brand-muted uppercase text-[9px] font-bold">Authoritative Record Value:</span>
                            <p className="font-medium text-brand-ink font-mono">{f.entered_value || 'None'}</p>
                          </div>
                          <div>
                            <span className="text-brand-muted uppercase text-[9px] font-bold">Extracted Document Candidate:</span>
                            <p className="font-medium text-brand-ink font-mono">{f.extracted_value || 'None'}</p>
                          </div>
                        </div>
                      )}

                      {f.source_excerpt && (
                        <div className="mt-2 p-2 rounded bg-brand-surface border border-brand-border/60 text-[11px] font-mono text-brand-muted italic">
                          "{f.source_excerpt}"
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-4 rounded-lg border border-dashed border-brand-border text-center text-brand-muted">
                    No conflicting findings detected. All extracted facts match authoritative records.
                  </div>
                )}
              </div>
            </div>

            {/* Extracted Fields Table */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
                <FileSearch className="w-4 h-4 text-brand-teal" />
                Candidate Fields & Supporting Source Evidence
              </h4>

              <div className="border border-brand-border rounded-xl overflow-hidden bg-brand-surface">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-brand-surface-secondary text-[10px] uppercase font-bold text-brand-muted border-b border-brand-border">
                    <tr>
                      <th className="px-4 py-2.5">Field Candidate</th>
                      <th className="px-4 py-2.5">Extracted Value</th>
                      <th className="px-4 py-2.5">Record Value</th>
                      <th className="px-4 py-2.5">Reliability</th>
                      <th className="px-4 py-2.5">Source Evidence Excerpt</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {/* Expiry Date */}
                    <tr className="hover:bg-brand-surface-secondary/50">
                      <td className="px-4 py-2.5 font-bold text-brand-ink">Expiry / Validity Date</td>
                      <td className="px-4 py-2.5 font-mono text-brand-teal font-semibold">
                        {analysis.extracted_fields?.expiry_date?.value || 'Not extracted'}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-brand-muted">
                        {documentRecord?.expiry_date || 'N/A'}
                      </td>
                      <td className="px-4 py-2.5 font-mono">
                        {analysis.extracted_fields?.expiry_date?.confidence
                          ? `${Math.round(analysis.extracted_fields.expiry_date.confidence * 100)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                        {analysis.extracted_fields?.expiry_date?.source_excerpt || '-'}
                      </td>
                    </tr>

                    {/* Document Number */}
                    <tr className="hover:bg-brand-surface-secondary/50">
                      <td className="px-4 py-2.5 font-bold text-brand-ink">Document / Reference Number</td>
                      <td className="px-4 py-2.5 font-mono text-brand-teal font-semibold">
                        {analysis.extracted_fields?.document_number?.value || 'Not extracted'}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-brand-muted">
                        {documentRecord?.document_number || 'N/A'}
                      </td>
                      <td className="px-4 py-2.5 font-mono">
                        {analysis.extracted_fields?.document_number?.confidence
                          ? `${Math.round(analysis.extracted_fields.document_number.confidence * 100)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                        {analysis.extracted_fields?.document_number?.source_excerpt || '-'}
                      </td>
                    </tr>

                    {/* Issuing Authority */}
                    <tr className="hover:bg-brand-surface-secondary/50">
                      <td className="px-4 py-2.5 font-bold text-brand-ink">Issuing Authority</td>
                      <td className="px-4 py-2.5 font-semibold text-brand-ink">
                        {analysis.extracted_fields?.issuing_authority?.value || 'Not extracted'}
                      </td>
                      <td className="px-4 py-2.5 text-brand-muted">
                        {documentRecord?.issuing_authority || 'N/A'}
                      </td>
                      <td className="px-4 py-2.5 font-mono">
                        {analysis.extracted_fields?.issuing_authority?.confidence
                          ? `${Math.round(analysis.extracted_fields.issuing_authority.confidence * 100)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                        {analysis.extracted_fields?.issuing_authority?.source_excerpt || '-'}
                      </td>
                    </tr>

                    {/* Issue Date */}
                    <tr className="hover:bg-brand-surface-secondary/50">
                      <td className="px-4 py-2.5 font-bold text-brand-ink">Issue / Execution Date</td>
                      <td className="px-4 py-2.5 font-mono text-brand-teal font-semibold">
                        {analysis.extracted_fields?.issue_date?.value || 'Not extracted'}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-brand-muted">
                        {documentRecord?.issue_date || 'N/A'}
                      </td>
                      <td className="px-4 py-2.5 font-mono">
                        {analysis.extracted_fields?.issue_date?.confidence
                          ? `${Math.round(analysis.extracted_fields.issue_date.confidence * 100)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                        {analysis.extracted_fields?.issue_date?.source_excerpt || '-'}
                      </td>
                    </tr>

                    {/* Document Category */}
                    <tr className="hover:bg-brand-surface-secondary/50">
                      <td className="px-4 py-2.5 font-bold text-brand-ink">Document Category Signature</td>
                      <td className="px-4 py-2.5 font-mono text-brand-ink font-semibold">
                        {analysis.extracted_fields?.document_category?.value || 'Not classified'}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-brand-muted">
                        {documentRecord?.document_type || 'N/A'}
                      </td>
                      <td className="px-4 py-2.5 font-mono">
                        {analysis.extracted_fields?.document_category?.confidence
                          ? `${Math.round(analysis.extracted_fields.document_category.confidence * 100)}%`
                          : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                        {analysis.extracted_fields?.document_category?.source_excerpt || '-'}
                      </td>
                    </tr>

                    {/* Property Identifiers */}
                    {analysis.extracted_fields?.property_identifiers && (
                      <tr className="hover:bg-brand-surface-secondary/50">
                        <td className="px-4 py-2.5 font-bold text-brand-ink">Property / Land Identifiers</td>
                        <td className="px-4 py-2.5 font-semibold text-brand-ink">
                          {analysis.extracted_fields.property_identifiers.value}
                        </td>
                        <td className="px-4 py-2.5 text-brand-muted">-</td>
                        <td className="px-4 py-2.5 font-mono">
                          {Math.round((analysis.extracted_fields.property_identifiers.confidence || 0) * 100)}%
                        </td>
                        <td className="px-4 py-2.5 text-[10px] text-brand-muted font-mono italic max-w-xs truncate">
                          {analysis.extracted_fields.property_identifiers.source_excerpt || '-'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Officer Review Decision Desk (Authorized AICTE Officers Only) */}
            {isOfficer && (
              <div className="p-5 rounded-xl border border-brand-teal/40 bg-brand-surface-secondary space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-brand-teal" />
                    Officer Statutory Decision Desk
                  </h4>
                  <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-brand-teal/10 text-brand-teal border border-brand-teal/30">
                    AICTE Authorized
                  </span>
                </div>

                {reviewSuccess && (
                  <div className="p-3 rounded-lg border border-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Decision recorded successfully in the audit register.</span>
                  </div>
                )}

                <form onSubmit={handleReviewSubmit} className="space-y-4">
                  <div>
                    <label className="block font-bold uppercase text-[10px] tracking-wider text-brand-muted mb-2">
                      Review Determination
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setDecision('CONFIRMED')}
                        className={`p-2.5 rounded-lg border text-left font-semibold transition-all ${
                          decision === 'CONFIRMED'
                            ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 shadow-sm'
                            : 'border-brand-border bg-brand-surface text-brand-text-primary hover:bg-brand-surface-elevated'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold">Confirm Extracted Data</span>
                          {decision === 'CONFIRMED' && <Check className="w-3.5 h-3.5 text-emerald-600" />}
                        </div>
                        <p className="text-[10px] font-normal text-brand-muted">
                          Affirm extracted values are verified and faithful to the deed.
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setDecision('CORRECTED')}
                        className={`p-2.5 rounded-lg border text-left font-semibold transition-all ${
                          decision === 'CORRECTED'
                            ? 'border-sky-600 bg-sky-50 dark:bg-sky-950/40 text-sky-800 dark:text-sky-200 shadow-sm'
                            : 'border-brand-border bg-brand-surface text-brand-text-primary hover:bg-brand-surface-elevated'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold">Correct Values</span>
                          {decision === 'CORRECTED' && <Check className="w-3.5 h-3.5 text-sky-600" />}
                        </div>
                        <p className="text-[10px] font-normal text-brand-muted">
                          Supply corrected regulatory values based on human scrutiny.
                        </p>
                      </button>

                      <button
                        type="button"
                        onClick={() => setDecision('REJECTED')}
                        className={`p-2.5 rounded-lg border text-left font-semibold transition-all ${
                          decision === 'REJECTED'
                            ? 'border-rose-600 bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-200 shadow-sm'
                            : 'border-brand-border bg-brand-surface text-brand-text-primary hover:bg-brand-surface-elevated'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold">Reject Document Evidence</span>
                          {decision === 'REJECTED' && <Check className="w-3.5 h-3.5 text-rose-600" />}
                        </div>
                        <p className="text-[10px] font-normal text-brand-muted">
                          Reject submitted evidence as uncorroborated or deficient.
                        </p>
                      </button>
                    </div>
                  </div>

                  {decision === 'CORRECTED' && (
                    <div className="p-3.5 rounded-lg border border-sky-200 bg-sky-50/50 dark:bg-sky-950/20 space-y-3">
                      <p className="font-bold text-sky-900 dark:text-sky-200 text-xs">
                        Specify Corrected Authoritative Values:
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1">
                            Corrected Expiry Date
                          </label>
                          <input
                            type="date"
                            value={correctExpiry}
                            onChange={(e) => setCorrectExpiry(e.target.value)}
                            className="w-full p-2 border border-brand-border rounded-lg bg-brand-surface text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1">
                            Corrected Document Number
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. REG-PUN-2021-9921"
                            value={correctDocNum}
                            onChange={(e) => setCorrectDocNum(e.target.value)}
                            className="w-full p-2 border border-brand-border rounded-lg bg-brand-surface text-xs"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] uppercase font-bold text-brand-muted mb-1">
                            Corrected Issuing Authority
                          </label>
                          <input
                            type="text"
                            placeholder="e.g. Sub-Registrar Haveli Pune"
                            value={correctAuthority}
                            onChange={(e) => setCorrectAuthority(e.target.value)}
                            className="w-full p-2 border border-brand-border rounded-lg bg-brand-surface text-xs"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="applyRecordCheck"
                      checked={applyToRecord}
                      onChange={(e) => setApplyToRecord(e.target.checked)}
                      className="rounded border-brand-border text-brand-teal focus:ring-brand-teal w-4 h-4"
                    />
                    <label htmlFor="applyRecordCheck" className="text-xs font-semibold text-brand-ink cursor-pointer">
                      Apply confirmed / corrected values to the authoritative Document Vault record
                    </label>
                  </div>

                  <div>
                    <label className="block font-bold uppercase text-[10px] tracking-wider text-brand-muted mb-1">
                      Statutory Reviewer Remarks & Justification (Mandatory)
                    </label>
                    <textarea
                      rows={2}
                      required
                      value={remarks}
                      onChange={(e) => setRemarks(e.target.value)}
                      placeholder="e.g. Verified against sub-registrar seal on page 1. Schedule reflects 33-year tenure commencing 2021."
                      className="w-full p-2.5 border border-brand-border rounded-lg bg-brand-surface text-xs focus:ring-1 focus:ring-brand-teal"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      type="submit"
                      disabled={submittingReview}
                      className="px-4 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white font-bold text-xs shadow-sm transition-colors flex items-center gap-1.5"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      {submittingReview ? 'Recording Decision...' : 'Commit Review Decision'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Audit History Strip if already reviewed */}
            {analysis.reviewer_decision && (
              <div className="p-3.5 rounded-lg border border-brand-border bg-brand-surface text-[11px] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-brand-ink">
                    Recorded Determination: <strong className="text-brand-teal">{analysis.reviewer_decision}</strong>
                  </span>
                  <span className="text-brand-muted font-mono text-[10px]">
                    {analysis.reviewed_at
                      ? new Date(analysis.reviewed_at).toLocaleString('en-IN')
                      : 'Recently'}
                  </span>
                </div>
                <p className="text-brand-muted">
                  Reviewing Officer: <strong className="text-brand-ink">{analysis.reviewed_by_name || 'AICTE Officer'}</strong>
                </p>
                {analysis.reviewer_remarks && (
                  <p className="italic text-brand-muted mt-1">"{analysis.reviewer_remarks}"</p>
                )}
              </div>
            )}

            {/* Regulatory Disclaimer Notice */}
            <div className="p-3 rounded-lg border border-brand-border/60 bg-brand-surface-secondary text-[10px] text-brand-muted space-y-0.5">
              <p className="font-bold text-brand-ink uppercase tracking-wider">Regulatory Architecture Notice</p>
              <p>
                Document intelligence extracts text and corroborates candidate facts locally. Under AICTE PS 26262
                statutory integrity invariants, extraction alone never automatically alters authoritative validity
                dates, approves compliance, or rejects applications without authorized officer review.
              </p>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
};
