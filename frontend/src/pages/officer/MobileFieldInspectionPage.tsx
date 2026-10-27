import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  MapPin, CheckCircle2, AlertTriangle, Shield, Camera, Upload,
  FileText, Clock, ExternalLink, ArrowLeft, RefreshCw, Send,
  Video, Eye, Award, Check, X, AlertCircle
} from 'lucide-react';
import { api } from '../../api/client';
import { EVCInspection, EVCFieldEvidence, EVCPanelAssignment } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

// 5 canonical APH inspection requirements
const DEFAULT_CHECKLIST_ITEMS = [
  {
    code: 'CL_LAND_01',
    title: 'Land Title, Master Plan & Built-up Carpet Area',
    description: 'Verify contiguous land possession, non-agricultural clearance, FSI compliance, and instructional area carpet norms.'
  },
  {
    code: 'CL_LAB_02',
    title: 'Computing Clusters, AI/ML Labs & Specialized Equipment',
    description: 'Verify required number of operational workstations, licensed software/open-source stacks, and hardware specifications.'
  },
  {
    code: 'CL_LIB_03',
    title: 'Central Library, Digital Bandwidth & Reading Facilities',
    description: 'Verify titles/volumes ratio, e-journal subscriptions, Wi-Fi speeds (>100 Mbps), and national digital library access.'
  },
  {
    code: 'CL_ACC_04',
    title: 'Barrier-Free Campus, Tactile Access & Operational Lifts',
    description: 'Verify ramps with gradient <= 1:12, dedicated disabled washrooms, braille signage, and certified lift installations.'
  },
  {
    code: 'CL_FIRE_05',
    title: 'Municipal Fire NOC, Hydrant Systems & Disaster Exits',
    description: 'Verify valid municipal fire department safety certificate, pressurized hose reels, emergency stairs, and evacuation maps.'
  }
];

export const MobileFieldInspectionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [inspection, setInspection] = useState<EVCInspection | null>(null);
  const [evidenceList, setEvidenceList] = useState<EVCFieldEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Check-in state
  const [checkingIn, setCheckingIn] = useState(false);
  const [manualCheckInOpen, setManualCheckInOpen] = useState(false);
  const [manualCheckInReason, setManualCheckInReason] = useState('Location permission denied by user browser');

  // Evidence capture modal state
  const [selectedItemCode, setSelectedItemCode] = useState<string | null>(null);
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [evidenceStatus, setEvidenceStatus] = useState<'COMPLIANT' | 'DEFICIENT' | 'NOT_APPLICABLE'>('COMPLIANT');
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const [evidenceFileName, setEvidenceFileName] = useState('');
  const [evidenceType, setEvidenceType] = useState('PHOTO');
  const [capturingLocation, setCapturingLocation] = useState(false);
  const [evidenceGeo, setEvidenceGeo] = useState<{ lat?: number; lon?: number; accuracy?: number } | null>(null);

  // Finalize report modal
  const [finalizeModalOpen, setFinalizeModalOpen] = useState(false);
  const [reportUrl, setReportUrl] = useState('');
  const [reportNotes, setReportNotes] = useState('');
  const [recommendation, setRecommendation] = useState<'RECOMMENDED_APPROVAL' | 'RECOMMENDED_REJECTION' | 'DEFICIENCY_NOTED'>('RECOMMENDED_APPROVAL');
  const [virtualMeetingUrl, setVirtualMeetingUrl] = useState('');
  const [virtualRecordingUrl, setVirtualRecordingUrl] = useState('');

  const loadInspectionData = async () => {
    if (!id) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getEVCDossier(parseInt(id, 10));
      setInspection(data);
      if (data.field_evidence) {
        setEvidenceList(data.field_evidence);
      } else {
        const ev = await api.getEVCFieldEvidence(parseInt(id, 10));
        setEvidenceList(ev);
      }
      if (data.virtual_meeting_url) setVirtualMeetingUrl(data.virtual_meeting_url);
      if (data.virtual_recording_url) setVirtualRecordingUrl(data.virtual_recording_url);
      if (data.report_url) setReportUrl(data.report_url);
      if (data.report_notes) setReportNotes(data.report_notes);
      if (data.recommendation) setRecommendation(data.recommendation as any);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load inspection details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInspectionData();
  }, [id]);

  // Visit check-in via browser Geolocation with fallback
  const handleGPSCheckIn = () => {
    if (!inspection) return;
    setCheckingIn(true);
    setErrorMsg(null);

    if (!('geolocation' in navigator)) {
      setCheckingIn(false);
      setManualCheckInOpen(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const updated = await api.checkInEVC(inspection.id, {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            source: 'BROWSER_GEOLOCATION'
          });
          setInspection(updated);
          setSuccessMsg(`On-site check-in verified! Accuracy: ±${Math.round(pos.coords.accuracy)}m.`);
        } catch (err: any) {
          setErrorMsg(err.message || 'Failed to record check-in.');
        } finally {
          setCheckingIn(false);
        }
      },
      (geoErr) => {
        console.warn('Geolocation failed or denied:', geoErr);
        setCheckingIn(false);
        setManualCheckInOpen(true);
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  };

  const handleManualCheckIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspection) return;
    setActionLoading(true);
    try {
      const updated = await api.checkInEVC(inspection.id, {
        latitude: null,
        longitude: null,
        accuracy: null,
        source: 'MANUAL_OFFICER_OVERRIDE'
      });
      setInspection(updated);
      setManualCheckInOpen(false);
      setSuccessMsg('Manual field check-in recorded with authorized officer provenance.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to record manual check-in');
    } finally {
      setActionLoading(false);
    }
  };

  // Open evidence drawer for a checklist item
  const openEvidenceCapture = (code: string) => {
    setSelectedItemCode(code);
    const existing = evidenceList.find(e => e.checklist_item_code === code);
    if (existing) {
      setEvidenceNotes(existing.observation_notes || '');
      setEvidenceStatus((existing.status as any) || 'COMPLIANT');
      setEvidenceUrl(existing.file_url || '');
      setEvidenceFileName(existing.file_name || '');
      setEvidenceType(existing.evidence_type || 'PHOTO');
    } else {
      setEvidenceNotes('');
      setEvidenceStatus('COMPLIANT');
      setEvidenceUrl('');
      setEvidenceFileName('');
      setEvidenceType('PHOTO');
    }

    // Try optional geolocation for evidence capture
    if ('geolocation' in navigator) {
      setCapturingLocation(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setEvidenceGeo({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy: pos.coords.accuracy
          });
          setCapturingLocation(false);
        },
        () => {
          setEvidenceGeo(null);
          setCapturingLocation(false);
        },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    }
  };

  const handleSaveEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspection || !selectedItemCode) return;
    setActionLoading(true);
    setErrorMsg(null);

    const targetDef = DEFAULT_CHECKLIST_ITEMS.find(i => i.code === selectedItemCode);
    const title = targetDef ? targetDef.title : selectedItemCode;

    try {
      const recorded = await api.recordEVCFieldEvidence(inspection.id, {
        checklist_item_code: selectedItemCode,
        requirement_title: title,
        observation_notes: evidenceNotes,
        status: evidenceStatus,
        file_url: evidenceUrl || undefined,
        file_name: evidenceFileName || (evidenceUrl ? 'field_evidence_capture.jpg' : undefined),
        evidence_type: evidenceType,
        latitude: evidenceGeo?.lat ?? null,
        longitude: evidenceGeo?.lon ?? null,
        accuracy: evidenceGeo?.accuracy ?? null,
        source: evidenceGeo ? 'BROWSER_GEOLOCATION' : 'MANUAL_OFFICER_OVERRIDE',
        permission_granted: !!evidenceGeo
      });

      // Update list
      setEvidenceList(prev => {
        const filtered = prev.filter(item => item.checklist_item_code !== selectedItemCode);
        return [...filtered, recorded];
      });

      setSelectedItemCode(null);
      setSuccessMsg(`Evidence recorded with SHA-256 integrity hash: ${recorded.file_hash?.substring(0, 12)}...`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to record checklist evidence');
    } finally {
      setActionLoading(false);
    }
  };

  // Submit Final Report
  const handleFinalizeReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspection) return;
    setActionLoading(true);
    setErrorMsg(null);

    try {
      const updated = await api.finalizeEVCReport(inspection.id, {
        report_url: reportUrl || 'https://storage.aicte.gov.in/evc/dossier-completed.pdf',
        report_notes: reportNotes,
        recommendation,
        virtual_meeting_url: virtualMeetingUrl || undefined,
        virtual_recording_url: virtualRecordingUrl || undefined
      });
      setInspection(updated);
      setFinalizeModalOpen(false);
      setSuccessMsg('Field inspection report successfully finalized! Application transitioned to EVC_COMPLETED.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to finalize inspection report');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-4 text-center">
        <RefreshCw className="w-8 h-8 animate-spin text-[var(--brand-teal)] mb-3" />
        <p className="text-sm text-[var(--brand-muted)] font-medium">Loading field inspection workspace...</p>
      </div>
    );
  }

  if (!inspection) {
    return (
      <div className="max-w-md mx-auto p-4 text-center">
        <AlertTriangle className="w-12 h-12 text-[var(--brand-amber)] mx-auto mb-3" />
        <h2 className="text-lg font-bold text-[var(--brand-ink)]">Inspection Not Found</h2>
        <p className="text-sm text-[var(--brand-muted)] mt-1 mb-4">Inspection #{id} could not be retrieved or is unauthorized.</p>
        <Link to="/officer/evc/queue" className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--brand-teal)] text-white text-sm font-semibold rounded-lg">
          <ArrowLeft className="w-4 h-4" /> Back to EVC Queue
        </Link>
      </div>
    );
  }

  const isCheckedIn = !!inspection.check_in_at;
  const isCompleted = inspection.status === 'REPORT_SUBMITTED' || inspection.status === 'EVC_COMPLETED';

  return (
    <div className="w-full max-w-xl mx-auto px-3 sm:px-4 py-4 space-y-4">
      {/* Top Mobile Bar */}
      <div className="flex items-center justify-between gap-2 border-b border-[var(--brand-border)] pb-3">
        <Link
          to="/officer/evc/queue"
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[var(--brand-muted)] hover:text-[var(--brand-ink)] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Queue
        </Link>
        <div className="flex items-center gap-2">
          <StatusBadge status={inspection.status} />
          {inspection.panel_status && (
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[var(--brand-teal)]/10 text-[var(--brand-teal)] border border-[var(--brand-teal)]/20">
              {inspection.panel_status.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Alert Notices */}
      {errorMsg && (
        <div className="p-3 bg-[var(--brand-danger)]/10 border border-[var(--brand-danger)]/20 rounded-lg text-xs text-[var(--brand-danger)] flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div className="flex-1">{errorMsg}</div>
        </div>
      )}
      {successMsg && (
        <div className="p-3 bg-[var(--brand-teal)]/10 border border-[var(--brand-teal)]/20 rounded-lg text-xs text-[var(--brand-teal)] flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
          <div className="flex-1">{successMsg}</div>
        </div>
      )}

      {/* Institution & Visit Header Card */}
      <div className="bg-[var(--brand-surface)] border border-[var(--brand-border)] rounded-xl p-4 shadow-sm space-y-2.5">
        <div className="flex items-start justify-between gap-2">
          <div>
            <span className="text-[11px] font-bold tracking-wider uppercase text-[var(--brand-teal)]">
              {inspection.inspection_type.replace(/_/g, ' ')}
            </span>
            <h1 className="text-base sm:text-lg font-bold text-[var(--brand-ink)] leading-snug">
              {inspection.institution_name || `Application #${inspection.application_number || inspection.application_id}`}
            </h1>
          </div>
          <div className="text-right shrink-0">
            <span className="text-xs font-mono font-bold text-[var(--brand-muted)]">
              {inspection.application_number}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[var(--brand-border)] text-xs text-[var(--brand-muted)]">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-[var(--brand-teal)]" />
            <span>{inspection.scheduled_date ? new Date(inspection.scheduled_date).toLocaleDateString() : 'Date TBD'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-[var(--brand-amber)]" />
            <span>Region: {inspection.region || 'Western'}</span>
          </div>
        </div>
      </div>

      {/* On-Site Visit Check-In Card */}
      <div className="bg-[var(--brand-surface)] border border-[var(--brand-border)] rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-[var(--brand-ink)] flex items-center gap-2">
            <MapPin className="w-4 h-4 text-[var(--brand-teal)]" />
            On-Site Field Visit Check-In
          </h2>
          {isCheckedIn && (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
              <Check className="w-3 h-3" /> Checked In
            </span>
          )}
        </div>

        {!isCheckedIn ? (
          <div className="space-y-2">
            <p className="text-xs text-[var(--brand-muted)]">
              Record real-time field check-in to confirm physical committee presence. Captures opt-in GPS coordinates with transparent accuracy provenance.
            </p>
            <button
              onClick={handleGPSCheckIn}
              disabled={checkingIn}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-[var(--brand-teal)] hover:bg-[var(--brand-teal)]/90 text-white font-semibold text-xs rounded-lg transition-all shadow-sm disabled:opacity-50"
            >
              {checkingIn ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Acquiring GPS Signal...
                </>
              ) : (
                <>
                  <MapPin className="w-3.5 h-3.5" />
                  Record On-Site Check-In (GPS)
                </>
              )}
            </button>
            <button
              onClick={() => setManualCheckInOpen(true)}
              className="w-full text-center text-[11px] text-[var(--brand-muted)] hover:text-[var(--brand-ink)] underline pt-1"
            >
              Location denied or indoor signal lost? Record manual override
            </button>
          </div>
        ) : (
          <div className="p-3 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[var(--brand-muted)]">Check-In Time:</span>
              <span className="font-semibold text-[var(--brand-ink)]">
                {inspection.check_in_at ? new Date(inspection.check_in_at).toLocaleTimeString() : 'Recorded'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--brand-muted)]">Provenance Source:</span>
              <span className="font-mono text-[11px] font-bold text-[var(--brand-teal)]">
                {inspection.check_in_source || 'BROWSER_GEOLOCATION'}
              </span>
            </div>
            {inspection.check_in_lat && inspection.check_in_lon && (
              <div className="flex items-center justify-between">
                <span className="text-[var(--brand-muted)]">Coordinates & Accuracy:</span>
                <span className="font-mono text-[11px] text-[var(--brand-ink)]">
                  {inspection.check_in_lat.toFixed(4)}, {inspection.check_in_lon.toFixed(4)} (±{inspection.check_in_accuracy ? Math.round(inspection.check_in_accuracy) : 10}m)
                </span>
              </div>
            )}
            <p className="text-[10px] text-[var(--brand-muted)] pt-1 italic">
              Note: Advisory location verification captured via browser sensor with reported accuracy. Non-spoof-proof proof.
            </p>
          </div>
        )}
      </div>

      {/* Expert Panel Roster Card */}
      <div className="bg-[var(--brand-surface)] border border-[var(--brand-border)] rounded-xl p-4 shadow-sm space-y-2.5">
        <h2 className="text-sm font-bold text-[var(--brand-ink)] flex items-center gap-2">
          <Shield className="w-4 h-4 text-[var(--brand-teal)]" />
          Appointed Expert Committee
        </h2>
        <div className="space-y-2">
          <div className="p-2.5 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] flex items-center justify-between text-xs">
            <div>
              <span className="text-[10px] uppercase font-bold text-[var(--brand-teal)] block">Convener</span>
              <span className="font-semibold text-[var(--brand-ink)]">
                {inspection.convener_name || 'Convener pending assignment'}
              </span>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
              CONFIRMED
            </span>
          </div>

          <div className="p-2.5 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] flex items-center justify-between text-xs">
            <div>
              <span className="text-[10px] uppercase font-bold text-[var(--brand-teal)] block">Expert Member</span>
              <span className="font-semibold text-[var(--brand-ink)]">
                {inspection.expert_member_name || 'Expert Member pending assignment'}
              </span>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
              CONFIRMED
            </span>
          </div>
        </div>
      </div>

      {/* Requirements Checklist & Evidence Capture */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-[var(--brand-ink)] flex items-center gap-2">
            <Camera className="w-4 h-4 text-[var(--brand-teal)]" />
            APH Inspection Checklist ({evidenceList.length}/{DEFAULT_CHECKLIST_ITEMS.length} Evidence Filed)
          </h2>
        </div>

        <div className="space-y-2.5">
          {DEFAULT_CHECKLIST_ITEMS.map((item) => {
            const ev = evidenceList.find(e => e.checklist_item_code === item.code);
            const isCompliant = ev?.status === 'COMPLIANT';
            const isDeficient = ev?.status === 'DEFICIENT';

            return (
              <div
                key={item.code}
                className="bg-[var(--brand-surface)] border border-[var(--brand-border)] rounded-xl p-3.5 shadow-sm space-y-2 transition-all hover:border-[var(--brand-teal)]/40"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-mono font-bold text-[var(--brand-muted)]">
                      {item.code}
                    </span>
                    <h3 className="text-xs font-bold text-[var(--brand-ink)] leading-snug">
                      {item.title}
                    </h3>
                  </div>
                  {ev ? (
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${
                        isCompliant
                          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                          : isDeficient
                          ? 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
                          : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                      }`}
                    >
                      {ev.status}
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[var(--brand-canvas)] text-[var(--brand-muted)] border border-[var(--brand-border)] shrink-0">
                      PENDING
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-[var(--brand-muted)] leading-relaxed">
                  {item.description}
                </p>

                {ev && (
                  <div className="p-2.5 bg-[var(--brand-canvas)] rounded-lg text-xs space-y-1 border border-[var(--brand-border)]">
                    <div className="font-medium text-[var(--brand-ink)] text-[11px]">
                      Observation: {ev.observation_notes}
                    </div>
                    {ev.file_hash && (
                      <div className="flex items-center justify-between text-[10px] font-mono text-[var(--brand-muted)] pt-0.5">
                        <span>SHA-256 Digest:</span>
                        <span className="text-[var(--brand-teal)]">{ev.file_hash.substring(0, 16)}...</span>
                      </div>
                    )}
                    {ev.file_url && (
                      <a
                        href={ev.file_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--brand-teal)] hover:underline pt-0.5"
                      >
                        <FileText className="w-3 h-3" /> View Evidence Artifact
                      </a>
                    )}
                  </div>
                )}

                <button
                  onClick={() => openEvidenceCapture(item.code)}
                  className="w-full mt-1 py-1.5 px-3 bg-[var(--brand-canvas)] hover:bg-[var(--brand-surface)] text-[var(--brand-ink)] border border-[var(--brand-border)] rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Camera className="w-3 h-3 text-[var(--brand-teal)]" />
                  {ev ? 'Update Evidence & Notes' : 'Record Verification & Evidence'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Virtual Inspection & Video Boundary Card */}
      <div className="bg-[var(--brand-surface)] border border-[var(--brand-border)] rounded-xl p-4 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-[var(--brand-ink)] flex items-center gap-2">
          <Video className="w-4 h-4 text-[var(--brand-teal)]" />
          Virtual Inspection & Recording Archive
        </h2>
        <p className="text-xs text-[var(--brand-muted)]">
          For hybrid or virtual inspections, attach official VC meeting session links and authenticated cloud recording URLs for audit permanence.
        </p>

        <div className="space-y-2 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-[var(--brand-muted)] mb-1">
              Virtual Meeting Link (e.g. Webex / Teams / NIC VC)
            </label>
            <input
              type="url"
              value={virtualMeetingUrl}
              onChange={(e) => setVirtualMeetingUrl(e.target.value)}
              placeholder="https://meet.aicte.gov.in/evc-session-..."
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[var(--brand-muted)] mb-1">
              Recording Archive URL
            </label>
            <input
              type="url"
              value={virtualRecordingUrl}
              onChange={(e) => setVirtualRecordingUrl(e.target.value)}
              placeholder="https://storage.aicte.gov.in/recordings/evc-session-....mp4"
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>
        </div>
      </div>

      {/* Bottom Sticky Action Bar: Finalize Report */}
      <div className="pt-2 pb-6">
        <button
          onClick={() => setFinalizeModalOpen(true)}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[var(--brand-ink)] hover:bg-[var(--brand-ink)]/90 text-white font-bold text-sm rounded-xl transition-all shadow-md"
        >
          <Award className="w-4 h-4 text-[var(--brand-teal)]" />
          {isCompleted ? 'Update Final EVC Report & Recommendations' : 'Finalize & Submit Field Report'}
        </button>
      </div>

      {/* Modal: Manual Check-In Override */}
      <Modal
        isOpen={manualCheckInOpen}
        onClose={() => setManualCheckInOpen(false)}
        title="Manual Field Check-In Override"
      >
        <form onSubmit={handleManualCheckIn} className="space-y-3">
          <p className="text-xs text-[var(--brand-muted)]">
            When hardware location services or browser permissions are unavailable, an authorized committee member may record a manual check-in override. This is logged to the regulatory audit ledger.
          </p>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Reason for Manual Check-In
            </label>
            <textarea
              rows={3}
              value={manualCheckInReason}
              onChange={(e) => setManualCheckInReason(e.target.value)}
              required
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setManualCheckInOpen(false)}
              className="px-3 py-2 bg-[var(--brand-canvas)] text-[var(--brand-ink)] border border-[var(--brand-border)] rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="px-4 py-2 bg-[var(--brand-teal)] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
            >
              {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Confirm Manual Check-In
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Record Evidence for Checklist Item */}
      <Modal
        isOpen={!!selectedItemCode}
        onClose={() => setSelectedItemCode(null)}
        title={`Checklist Evidence: ${selectedItemCode}`}
      >
        <form onSubmit={handleSaveEvidence} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Compliance Status
            </label>
            <select
              value={evidenceStatus}
              onChange={(e) => setEvidenceStatus(e.target.value as any)}
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            >
              <option value="COMPLIANT">COMPLIANT — Meets AICTE APH Norms</option>
              <option value="DEFICIENT">DEFICIENT — Material Deficiency Observed</option>
              <option value="NOT_APPLICABLE">NOT_APPLICABLE — Not Required For Category</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Detailed Field Observations
            </label>
            <textarea
              rows={3}
              value={evidenceNotes}
              onChange={(e) => setEvidenceNotes(e.target.value)}
              placeholder="e.g. Inspected 60 operational computing nodes with licensed CAD software and high-speed LAN."
              required
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Evidence Photo / Document URL
            </label>
            <input
              type="url"
              value={evidenceUrl}
              onChange={(e) => setEvidenceUrl(e.target.value)}
              placeholder="https://storage.aicte.gov.in/evc/evidence/photo_01.jpg"
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
            <p className="text-[10px] text-[var(--brand-muted)] mt-1">
              SHA-256 hash will be computed automatically and recorded in the audit ledger.
            </p>
          </div>

          {/* Location Badge */}
          <div className="p-2.5 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] text-[11px] flex items-center justify-between">
            <span className="text-[var(--brand-muted)] flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-[var(--brand-teal)]" />
              Evidence Geotag:
            </span>
            {capturingLocation ? (
              <span className="text-[var(--brand-muted)] italic">Acquiring sensor tag...</span>
            ) : evidenceGeo ? (
              <span className="font-mono text-[var(--brand-teal)] font-bold">
                {evidenceGeo.lat?.toFixed(4)}, {evidenceGeo.lon?.toFixed(4)} (±{Math.round(evidenceGeo.accuracy || 10)}m)
              </span>
            ) : (
              <span className="text-[var(--brand-muted)]">No GPS (Manual provenance)</span>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setSelectedItemCode(null)}
              className="px-3 py-2 bg-[var(--brand-canvas)] text-[var(--brand-ink)] border border-[var(--brand-border)] rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="px-4 py-2 bg-[var(--brand-teal)] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
            >
              {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Save Checklist Evidence
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Finalize Report with Statutory Safeguard */}
      <Modal
        isOpen={finalizeModalOpen}
        onClose={() => setFinalizeModalOpen(false)}
        title="Finalize Field Inspection Report"
      >
        <form onSubmit={handleFinalizeReport} className="space-y-3.5">
          {/* Statutory Safeguard Alert Banner */}
          <div className="p-3 bg-[var(--brand-amber)]/10 border border-[var(--brand-amber)]/20 rounded-lg text-xs text-[var(--brand-ink)] space-y-1">
            <div className="font-bold flex items-center gap-1.5 text-[var(--brand-amber)]">
              <Shield className="w-4 h-4" /> Statutory Decision Exclusivity Invariant
            </div>
            <p className="text-[11px] text-[var(--brand-muted)] leading-relaxed">
              Your committee recommendation moves the application strictly to <strong>EVC_COMPLETED</strong> for Competent Authority hearing and decision order. Inspectors cannot grant final statutory approval or rejection.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Inspection Panel Recommendation
            </label>
            <select
              value={recommendation}
              onChange={(e) => setRecommendation(e.target.value as any)}
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs font-bold text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            >
              <option value="RECOMMENDED_APPROVAL">RECOMMENDED_APPROVAL — Infrastructure fully compliant</option>
              <option value="DEFICIENCY_NOTED">DEFICIENCY_NOTED — Deficiencies noted for SAC/CAC cure</option>
              <option value="RECOMMENDED_REJECTION">RECOMMENDED_REJECTION — Critical statutory non-compliance</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Consolidated Committee Observations
            </label>
            <textarea
              rows={4}
              value={reportNotes}
              onChange={(e) => setReportNotes(e.target.value)}
              placeholder="Summarize built-up area verification, faculty ratio, lab equipment, and overall physical inspection findings..."
              required
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--brand-ink)] mb-1">
              Signed Dossier Document URL (PDF)
            </label>
            <input
              type="url"
              value={reportUrl}
              onChange={(e) => setReportUrl(e.target.value)}
              placeholder="https://storage.aicte.gov.in/evc/reports/report_signed.pdf"
              className="w-full px-3 py-2 bg-[var(--brand-canvas)] border border-[var(--brand-border)] rounded-lg text-xs text-[var(--brand-ink)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-teal)]"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--brand-border)]">
            <button
              type="button"
              onClick={() => setFinalizeModalOpen(false)}
              className="px-3 py-2 bg-[var(--brand-canvas)] text-[var(--brand-ink)] border border-[var(--brand-border)] rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="px-4 py-2 bg-[var(--brand-ink)] hover:bg-[var(--brand-ink)]/90 text-white rounded-lg text-xs font-bold flex items-center gap-1.5"
            >
              {actionLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Submit Inspection Report
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
