import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass, Calendar, Users, CheckCircle2,
  AlertTriangle, RefreshCw, ArrowRight, PlusCircle,
  FileText, Clock, Building, Camera, Shield, Check, X, Info
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Application, EVCInspection, EvcAnalyticsData, EVCExpert, COICheckResult } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const EVCCoordinatorWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [inspections, setInspections] = useState<EVCInspection[]>([]);
  const [analytics, setAnalytics] = useState<EvcAnalyticsData | null>(null);
  const [experts, setExperts] = useState<EVCExpert[]>([]);
  const [loading, setLoading] = useState(true);

  // Scheduling modal state
  const [schedulingApp, setSchedulingApp] = useState<Application | null>(null);
  const [inspectionType, setInspectionType] = useState('PHYSICAL_ONSITE');
  const [scheduledDate, setScheduledDate] = useState('');
  const [convenerName, setConvenerName] = useState('');
  const [expertName, setExpertName] = useState('');
  const [selectedConvenerExpertId, setSelectedConvenerExpertId] = useState<string>('');
  const [selectedMemberExpertId, setSelectedMemberExpertId] = useState<string>('');
  const [scheduling, setScheduling] = useState(false);

  // Explainable COI Assessment modal / state
  const [coiModalOpen, setCoiModalOpen] = useState(false);
  const [coiAssessment, setCoiAssessment] = useState<COICheckResult | null>(null);
  const [checkingCoi, setCheckingCoi] = useState(false);
  const [overrideReason, setOverrideReason] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [apps, queue, evcStats, expertList] = await Promise.all([
        api.getApplications(),
        api.getEVCQueue(),
        api.getEvcAnalytics(),
        api.getEVCExperts().catch(() => [] as EVCExpert[])
      ]);
      setApplications(apps);
      setInspections(queue);
      setAnalytics(evcStats);
      setExperts(expertList);
    } catch (err) {
      console.error('Failed to load EVC coordinator data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When convener dropdown changes
  const handleConvenerSelect = (expertIdStr: string) => {
    setSelectedConvenerExpertId(expertIdStr);
    if (!expertIdStr) return;
    const found = experts.find(e => e.id.toString() === expertIdStr);
    if (found) {
      setConvenerName(`${found.name} (${found.current_institution})`);
    }
  };

  // When expert dropdown changes
  const handleMemberSelect = (expertIdStr: string) => {
    setSelectedMemberExpertId(expertIdStr);
    if (!expertIdStr) return;
    const found = experts.find(e => e.id.toString() === expertIdStr);
    if (found) {
      setExpertName(`${found.name} (${found.current_institution})`);
    }
  };

  // Evaluate COI for selected expert against current application
  const handleEvaluateCOI = async (expertIdStr: string) => {
    if (!expertIdStr || !schedulingApp) return;
    setCheckingCoi(true);
    try {
      const assessment = await api.checkEVCCOI(parseInt(expertIdStr, 10), schedulingApp.id);
      setCoiAssessment(assessment);
      setCoiModalOpen(true);
    } catch (err: any) {
      alert(err.message || 'COI evaluation failed');
    } finally {
      setCheckingCoi(false);
    }
  };

  const handleScheduleInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schedulingApp) return;
    setScheduling(true);
    try {
      await api.scheduleEVC({
        application_id: schedulingApp.id,
        inspection_type: inspectionType,
        scheduled_date: new Date(scheduledDate).toISOString(),
        convener_name: convenerName,
        expert_member_name: expertName,
      });
      setSchedulingApp(null);
      setConvenerName('');
      setExpertName('');
      setSelectedConvenerExpertId('');
      setSelectedMemberExpertId('');
      setScheduledDate('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Inspection scheduling failed');
    } finally {
      setScheduling(false);
    }
  };

  // Applications awaiting EVC scheduling
  const awaitingScheduleApps = applications.filter(a =>
    a.current_stage === 'AWAITING_EVC_SCHEDULE' ||
    (a.evc_required && a.current_stage === 'SCRUTINY_COMPLETED')
  );

  const scheduledInspections = inspections.filter(i => i.status === 'SCHEDULED' || i.status === 'IN_PROGRESS');
  const completedInspections = inspections.filter(i => i.status === 'REPORT_SUBMITTED' || i.status === 'COMPLETED');

  return (
    <div className="space-y-6">
      {/* Workspace Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              EVC INSPECTION COORDINATION DIRECTORATE
            </span>
            <span className="text-xs text-brand-muted">
              Scope: <strong>{user?.region || 'Western'} Region Directorate</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink mt-1">
            Expert Visit Committee (EVC) Scheduling & Panel Command
          </h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Active Coordinator: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (EVC COORDINATOR) • Panel Roster, Explainable COI Checks & Mobile Field Evidence
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Roster
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Awaiting EVC Scheduling"
          value={awaitingScheduleApps.length}
          subtext="Cases ready for panel formation"
          icon={<Clock size={18} />}
          variant={awaitingScheduleApps.length > 0 ? 'amber' : 'default'}
        />
        <StatCard
          title="Scheduled Visits"
          value={scheduledInspections.length}
          subtext="Inspections pending field visit"
          icon={<Calendar size={18} />}
        />
        <StatCard
          title="Completed Inspections"
          value={completedInspections.length}
          subtext="Reports filed & evaluated"
          icon={<CheckCircle2 size={18} />}
        />
        <StatCard
          title="Total Lifetime Visits"
          value={analytics?.total_inspections ?? inspections.length}
          subtext="Academic cycle 2026-2027"
          icon={<Compass size={18} />}
        />
      </div>

      {/* Section 1: Cases Awaiting Panel Assignment */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-brand-teal" />
            <h2 className="text-sm font-bold text-brand-ink">
              Action Queue: Applications Awaiting Committee Appointment ({awaitingScheduleApps.length})
            </h2>
          </div>
        </div>

        {awaitingScheduleApps.length === 0 ? (
          <div className="p-8 text-center text-brand-muted text-xs">
            No applications currently pending EVC scheduling in your regional jurisdiction.
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs min-w-[700px]">
              <thead className="bg-gray-50/75 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] tracking-wider font-semibold border-b border-brand-border">
                <tr>
                  <th className="px-6 py-3.5">Application Number</th>
                  <th className="px-6 py-3.5">Applicant Institution</th>
                  <th className="px-6 py-3.5">Type</th>
                  <th className="px-6 py-3.5">Regional Office</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
                {awaitingScheduleApps.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                    <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                      {app.application_number}
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{app.institution_name}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 dark:bg-brand-surface-secondary text-brand-ink border border-gray-200 dark:border-brand-border">
                        {app.application_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-brand-muted">
                      {app.region} Region
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setSchedulingApp(app);
                          setScheduledDate('2026-11-05T10:00');
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold text-xs shadow-sm transition-colors duration-150"
                      >
                        <PlusCircle className="w-3.5 h-3.5" /> Appoint Panel & Schedule
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 2: Comprehensive EVC Inspections & Field Workspace Roster */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-brand-teal" />
            <h2 className="text-sm font-bold text-brand-ink">
              EVC Inspection Roster & Field Evidence Workspace ({inspections.length})
            </h2>
          </div>
        </div>

        <div className="overflow-x-auto w-full">
          <table className="w-full text-left text-xs min-w-[700px]">
            <thead className="bg-gray-50/75 dark:bg-brand-surface-secondary text-brand-muted uppercase text-[10px] tracking-wider font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">App Number</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Mode</th>
                <th className="px-6 py-3.5">Scheduled Date</th>
                <th className="px-6 py-3.5">Convener & Expert</th>
                <th className="px-6 py-3.5">Status & Panel</th>
                <th className="px-6 py-3.5 text-right">Field Workspace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-brand-border">
              {inspections.map((insp) => (
                <tr key={insp.id} className="hover:bg-gray-50/80 dark:hover:bg-brand-surface-elevated transition-colors duration-150">
                  <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                    {insp.application_number}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.institution_name}</p>
                    <span className="text-[10px] text-brand-muted">{insp.region}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 dark:bg-brand-surface-secondary text-brand-ink border border-gray-200 dark:border-brand-border">
                      {insp.inspection_type.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-medium text-brand-ink">
                    {insp.scheduled_date ? new Date(insp.scheduled_date).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Unscheduled'}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.convener_name || 'Convener Pending'}</p>
                    <p className="text-[10px] text-brand-muted">{insp.expert_member_name || 'Expert Member Pending'}</p>
                  </td>
                  <td className="px-6 py-4 space-y-1">
                    <StatusBadge status={insp.status} />
                    {insp.panel_status && (
                      <div>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                            insp.panel_status === 'PANEL_CONFIRMED'
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                              : insp.panel_status === 'REASSIGNMENT_REQUIRED'
                              ? 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
                              : 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300'
                          }`}
                        >
                          {insp.panel_status.replace(/_/g, ' ')}
                        </span>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/officer/evc/field/${insp.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--brand-teal)]/10 text-[var(--brand-teal)] hover:bg-[var(--brand-teal)] hover:text-white border border-[var(--brand-teal)]/20 font-bold text-xs shadow-sm transition-all"
                    >
                      <Camera className="w-3.5 h-3.5" /> Field App
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Schedule EVC Inspection with Structured COI Engine */}
      {schedulingApp && (
        <Modal
          isOpen={true}
          onClose={() => setSchedulingApp(null)}
          title={`Form EVC Committee & Schedule: ${schedulingApp.application_number}`}
        >
          <form onSubmit={handleScheduleInspection} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 dark:bg-brand-surface-secondary/60 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Institution: {schedulingApp.institution_name}</p>
              <p className="text-brand-muted">Type: {schedulingApp.application_type.replace(/_/g, ' ')}</p>
              <p className="text-brand-teal font-medium">Region: {schedulingApp.region} Regional Jurisdiction</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Inspection Mode</label>
              <select
                value={inspectionType}
                onChange={(e) => setInspectionType(e.target.value)}
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white dark:bg-brand-surface-secondary text-brand-ink"
              >
                <option value="PHYSICAL_ONSITE">Physical On-Site Inspection (Field Panel)</option>
                <option value="VIRTUAL_REMOTE">Virtual Remote Inspection (Live Geotagged Audio/Video)</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Scheduled Date & Time (Future Date Required)</label>
              <input
                type="datetime-local"
                required
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal bg-white dark:bg-brand-surface-secondary text-brand-ink"
              />
            </div>

            {/* Convener Selection & COI */}
            <div className="p-3 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] space-y-2">
              <div className="flex items-center justify-between">
                <label className="font-bold text-brand-ink">Panel Convener (Senior Academician)</label>
                {selectedConvenerExpertId && (
                  <button
                    type="button"
                    onClick={() => handleEvaluateCOI(selectedConvenerExpertId)}
                    disabled={checkingCoi}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-[var(--brand-teal)] hover:underline"
                  >
                    <Shield className="w-3 h-3" /> Check COI Norms
                  </button>
                )}
              </div>

              {experts.length > 0 && (
                <select
                  value={selectedConvenerExpertId}
                  onChange={(e) => handleConvenerSelect(e.target.value)}
                  className="w-full px-3 py-2 border border-brand-border rounded-lg bg-white dark:bg-brand-surface-secondary text-brand-ink text-xs mb-1.5"
                >
                  <option value="">-- Choose from Expert Registry --</option>
                  {experts.map(exp => (
                    <option key={exp.id} value={exp.id.toString()}>
                      {exp.name} • {exp.designation} ({exp.current_institution})
                    </option>
                  ))}
                </select>
              )}

              <input
                type="text"
                required
                value={convenerName}
                onChange={(e) => setConvenerName(e.target.value)}
                placeholder="Or enter custom Convener name & affiliation"
                className="w-full px-3 py-2 border border-brand-border rounded-lg bg-white dark:bg-brand-surface-secondary text-brand-ink text-xs"
              />
            </div>

            {/* Expert Member Selection & COI */}
            <div className="p-3 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)] space-y-2">
              <div className="flex items-center justify-between">
                <label className="font-bold text-brand-ink">Subject / Technical Expert Member</label>
                {selectedMemberExpertId && (
                  <button
                    type="button"
                    onClick={() => handleEvaluateCOI(selectedMemberExpertId)}
                    disabled={checkingCoi}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-[var(--brand-teal)] hover:underline"
                  >
                    <Shield className="w-3 h-3" /> Check COI Norms
                  </button>
                )}
              </div>

              {experts.length > 0 && (
                <select
                  value={selectedMemberExpertId}
                  onChange={(e) => handleMemberSelect(e.target.value)}
                  className="w-full px-3 py-2 border border-brand-border rounded-lg bg-white dark:bg-brand-surface-secondary text-brand-ink text-xs mb-1.5"
                >
                  <option value="">-- Choose from Expert Registry --</option>
                  {experts.map(exp => (
                    <option key={exp.id} value={exp.id.toString()}>
                      {exp.name} • {exp.designation} ({exp.current_institution})
                    </option>
                  ))}
                </select>
              )}

              <input
                type="text"
                required
                value={expertName}
                onChange={(e) => setExpertName(e.target.value)}
                placeholder="Or enter custom Expert Member name & affiliation"
                className="w-full px-3 py-2 border border-brand-border rounded-lg bg-white dark:bg-brand-surface-secondary text-brand-ink text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[var(--brand-border)]">
              <button
                type="button"
                onClick={() => setSchedulingApp(null)}
                className="px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-100 font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={scheduling}
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm"
              >
                {scheduling ? 'Dispatching...' : 'Confirm & Dispatch Panel Roster'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal: Explainable Conflict-of-Interest (COI) Rule Assessment */}
      <Modal
        isOpen={coiModalOpen}
        onClose={() => setCoiModalOpen(false)}
        title="Explainable Conflict-of-Interest (COI) Assessment"
      >
        {coiAssessment && (
          <div className="space-y-3.5 text-xs">
            <div className="p-3 bg-[var(--brand-canvas)] rounded-lg border border-[var(--brand-border)]">
              <p className="font-bold text-[var(--brand-ink)]">{coiAssessment.expert_name}</p>
              <p className="text-[var(--brand-muted)]">{coiAssessment.current_institution}</p>
            </div>

            {/* Verdict Badge */}
            <div
              className={`p-3 rounded-lg border ${
                coiAssessment.is_prohibited
                  ? 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950 dark:text-rose-200 dark:border-rose-900'
                  : 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-900'
              }`}
            >
              <div className="font-bold flex items-center gap-1.5 mb-1">
                {coiAssessment.is_prohibited ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                {coiAssessment.is_prohibited ? 'Conflict of Interest Detected' : 'All Regulatory Norms Satisfied'}
              </div>
              <p className="text-[11px] leading-relaxed">{coiAssessment.summary}</p>
            </div>

            {/* Rule-by-Rule Breakdown */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--brand-muted)] block">
                Auditable Rule Verifications (APH Norms)
              </span>
              {coiAssessment.rules_checked.map((rule) => {
                const passed = rule.status === 'PASSED';
                return (
                  <div
                    key={rule.rule_code}
                    className="p-2.5 rounded-lg border border-[var(--brand-border)] bg-[var(--brand-surface)] flex items-start gap-2"
                  >
                    {passed ? (
                      <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mt-0.5 shrink-0" />
                    ) : (
                      <X className="w-4 h-4 text-rose-600 dark:text-rose-400 mt-0.5 shrink-0" />
                    )}
                    <div className="space-y-0.5 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[var(--brand-ink)] text-[11px]">
                          {rule.rule_name}
                        </span>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                            passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}
                        >
                          {rule.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-[var(--brand-muted)]">{rule.details}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setCoiModalOpen(false)}
                className="px-4 py-2 bg-[var(--brand-teal)] text-white rounded-lg font-semibold text-xs"
              >
                Close Assessment
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
export default EVCCoordinatorWorkspace;
