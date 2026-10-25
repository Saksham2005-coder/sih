import React, { useEffect, useState } from 'react';
import { Compass, Calendar, UserCheck, FileCheck, Upload, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import { EVCInspection } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const EVCQueue: React.FC = () => {
  const [inspections, setInspections] = useState<EVCInspection[]>([]);
  const [loading, setLoading] = useState(true);

  // Schedule Modal
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [selectedInspection, setSelectedInspection] = useState<EVCInspection | null>(null);
  const [schedDate, setSchedDate] = useState('');
  const [convener, setConvener] = useState('Prof. Rajesh Sharma (IIT Bombay)');
  const [expert, setExpert] = useState('Dr. Ananya Sen (VJTI Mumbai)');
  const [mode, setMode] = useState('PHYSICAL_ONSITE');
  const [submittingSched, setSubmittingSched] = useState(false);

  // Report Modal
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportNotes, setReportNotes] = useState('');
  const [recommendation, setRecommendation] = useState('RECOMMENDED_APPROVAL');
  const [submittingReport, setSubmittingReport] = useState(false);

  const loadQueue = async () => {
    try {
      const data = await api.getEVCQueue();
      setInspections(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleOpenSchedule = (insp: EVCInspection) => {
    setSelectedInspection(insp);
    setSchedDate('2026-11-05T10:00');
    setScheduleModalOpen(true);
  };

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInspection) return;
    setSubmittingSched(true);
    try {
      await api.scheduleEVC({
        application_id: selectedInspection.application_id,
        inspection_type: mode,
        scheduled_date: new Date(schedDate).toISOString(),
        convener_name: convener,
        expert_member_name: expert,
      });
      setScheduleModalOpen(false);
      loadQueue();
    } catch (err: any) {
      alert(err.message || 'Scheduling failed');
    } finally {
      setSubmittingSched(false);
    }
  };

  const handleOpenReport = (insp: EVCInspection) => {
    setSelectedInspection(insp);
    setReportNotes('On-site verification completed. Infrastructure, labs, and faculty records inspected.');
    setRecommendation('RECOMMENDED_APPROVAL');
    setReportModalOpen(true);
  };

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInspection) return;
    setSubmittingReport(true);
    try {
      await api.submitEVCReport(selectedInspection.id, {
        report_url: '/api/documents/download/evc_signed_inspection_report.pdf',
        report_notes: reportNotes,
        recommendation: recommendation,
      });
      setReportModalOpen(false);
      loadQueue();
    } catch (err: any) {
      alert(err.message || 'Report submission failed');
    } finally {
      setSubmittingReport(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-brand-ink">Expert Visit Committee (EVC) Queue</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Coordinate inspection panel formation, visit schedules, and statutory recommendation reports
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {inspections.length === 0 ? (
          <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-12 text-center text-xs text-brand-muted dark:text-brand-muted transition-colors">
            No applications pending EVC inspection in the queue.
          </div>
        ) : (
          inspections.map((insp) => (
            <div
              key={insp.id}
              className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm hover:border-brand-teal/50 hover:shadow-md transition-all flex flex-col md:flex-row justify-between gap-6"
            >
              <div className="space-y-2 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-brand-ink dark:text-brand-ink">{insp.application_number}</span>
                  <StatusBadge status={insp.status} />
                </div>
                <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink">{insp.institution_name}</h3>
                <p className="text-xs text-brand-muted dark:text-brand-muted">
                  {insp.region} Region • Mode: <span className="font-semibold text-brand-ink dark:text-brand-ink">{insp.inspection_type.replace(/_/g, ' ')}</span>
                </p>

                {insp.scheduled_date && (
                  <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border dark:border-brand-border text-xs space-y-1">
                    <p className="font-semibold text-brand-ink dark:text-brand-ink flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-brand-teal" />
                      Scheduled Visit Date: {new Date(insp.scheduled_date).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </p>
                    <p className="text-brand-muted dark:text-brand-muted">
                      Convener: <span className="text-brand-ink dark:text-brand-ink font-medium">{insp.convener_name || 'TBD'}</span>
                    </p>
                    <p className="text-brand-muted dark:text-brand-muted">
                      Expert Member: <span className="text-brand-ink dark:text-brand-ink font-medium">{insp.expert_member_name || 'TBD'}</span>
                    </p>
                  </div>
                )}

                {insp.recommendation && (
                  <div className="p-3 bg-teal-50 dark:bg-brand-teal/15 border border-teal-200 dark:border-brand-teal/30 rounded-lg text-xs">
                    <p className="font-bold text-teal-900 dark:text-teal-200">
                      Committee Recommendation: {insp.recommendation.replace(/_/g, ' ')}
                    </p>
                    {insp.report_notes && <p className="text-teal-800 dark:text-teal-300 mt-1">{insp.report_notes}</p>}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex md:flex-col justify-end items-end gap-2 shrink-0">
                {insp.status === 'PENDING_ASSIGNMENT' && (
                  <button
                    onClick={() => handleOpenSchedule(insp)}
                    className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-hover text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
                  >
                    <Calendar className="w-3.5 h-3.5" /> Schedule Inspection
                  </button>
                )}

                {insp.status === 'SCHEDULED' && (
                  <button
                    onClick={() => handleOpenReport(insp)}
                    className="px-4 py-2 rounded-lg bg-brand-ink text-white hover:bg-gray-800 text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
                  >
                    <FileCheck className="w-3.5 h-3.5 text-brand-teal" /> Upload Visit Report
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Schedule Modal */}
      <Modal
        isOpen={scheduleModalOpen}
        onClose={() => setScheduleModalOpen(false)}
        title="Schedule EVC Inspection Visit"
        subtitle={`Application ${selectedInspection?.application_number} — ${selectedInspection?.institution_name}`}
      >
        <form onSubmit={handleScheduleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Inspection Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg px-3 py-2 text-xs focus:ring-1 focus:ring-brand-teal"
            >
              <option value="PHYSICAL_ONSITE">Physical On-Site Verification</option>
              <option value="VIRTUAL_REMOTE">Virtual Remote Inspection</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Inspection Date & Time
            </label>
            <input
              type="datetime-local"
              required
              value={schedDate}
              onChange={(e) => setSchedDate(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Committee Convener (Senior Academician)
            </label>
            <input
              type="text"
              required
              value={convener}
              onChange={(e) => setConvener(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Subject / Technical Expert Member
            </label>
            <input
              type="text"
              required
              value={expert}
              onChange={(e) => setExpert(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setScheduleModalOpen(false)}
              className="px-4 py-2 border border-brand-border dark:border-brand-border rounded-lg text-brand-ink dark:text-brand-ink font-semibold hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingSched}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-hover shadow-sm transition-colors"
            >
              {submittingSched ? 'Confirming...' : 'Confirm Schedule'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Report Modal */}
      <Modal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        title="Upload EVC Inspection Findings"
        subtitle={`Application ${selectedInspection?.application_number}`}
      >
        <form onSubmit={handleReportSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Statutory Recommendation Outcome
            </label>
            <select
              value={recommendation}
              onChange={(e) => setRecommendation(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg px-3 py-2 text-xs font-semibold focus:ring-1 focus:ring-brand-teal"
            >
              <option value="RECOMMENDED_APPROVAL">RECOMMENDED_APPROVAL — Infrastructure & Norms Satisfied</option>
              <option value="DEFICIENCY_NOTED">DEFICIENCY_NOTED — Deficiencies Identified on Visit</option>
              <option value="RECOMMENDED_REJECTION">RECOMMENDED_REJECTION — Critical Statutory Non-Compliance</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Inspection Report Notes & Committee Summary
            </label>
            <textarea
              rows={4}
              required
              value={reportNotes}
              onChange={(e) => setReportNotes(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setReportModalOpen(false)}
              className="px-4 py-2 border border-brand-border dark:border-brand-border rounded-lg text-brand-ink dark:text-brand-ink font-semibold hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingReport}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-hover shadow-sm transition-colors"
            >
              {submittingReport ? 'Submitting...' : 'Submit Official Report'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
