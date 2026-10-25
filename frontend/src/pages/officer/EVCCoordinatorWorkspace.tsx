import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Compass, Calendar, Users, CheckCircle2,
  AlertTriangle, RefreshCw, ArrowRight, PlusCircle,
  FileText, Clock, Building
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { Application, EVCInspection, EvcAnalyticsData } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const EVCCoordinatorWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState<Application[]>([]);
  const [inspections, setInspections] = useState<EVCInspection[]>([]);
  const [analytics, setAnalytics] = useState<EvcAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  // Scheduling modal state
  const [schedulingApp, setSchedulingApp] = useState<Application | null>(null);
  const [inspectionType, setInspectionType] = useState('PHYSICAL_ONSITE');
  const [scheduledDate, setScheduledDate] = useState('');
  const [convenerName, setConvenerName] = useState('');
  const [expertName, setExpertName] = useState('');
  const [scheduling, setScheduling] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [apps, queue, evcStats] = await Promise.all([
        api.getApplications(),
        api.getEVCQueue(),
        api.getEvcAnalytics(),
      ]);
      setApplications(apps);
      setInspections(queue);
      setAnalytics(evcStats);
    } catch (err) {
      console.error('Failed to load EVC coordinator data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
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
            Active Coordinator: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (EVC COORDINATOR) • Panel Roster, Schedule SLAs & Inspection Reports
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

      {/* Primary Section: Eligible Applications Awaiting EVC Schedule */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Applications Awaiting EVC Panel Assignment</h3>
            <p className="text-xs text-brand-muted">Cases that have successfully satisfied initial scrutiny and require physical or virtual on-site verification</p>
          </div>
          <span className="text-xs font-bold text-brand-teal bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200">
            {awaitingScheduleApps.length} Ready to Schedule
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Application Type</th>
                <th className="px-6 py-3.5">Current Stage</th>
                <th className="px-6 py-3.5 text-right">Coordination Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {awaitingScheduleApps.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-brand-muted">
                    Zero applications currently awaiting EVC scheduling.
                  </td>
                </tr>
              ) : (
                awaitingScheduleApps.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50/80">
                    <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                      <Link to={`/officer/applications/${app.id}`} className="hover:text-brand-teal">
                        {app.application_number}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{app.institution_name}</p>
                      <span className="text-[10px] text-brand-muted">{app.region} Region</span>
                    </td>
                    <td className="px-6 py-4 font-medium text-brand-ink">
                      {app.application_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.current_stage} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setSchedulingApp(app);
                          // Default date 7 days in future
                          const d = new Date();
                          d.setDate(d.getDate() + 7);
                          d.setHours(10, 0, 0, 0);
                          setScheduledDate(d.toISOString().slice(0, 16));
                          setConvenerName('Prof. Rajesh Sharma (IIT Bombay)');
                          setExpertName('Dr. Ananya Sen (VJTI)');
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors"
                      >
                        <Calendar className="w-3.5 h-3.5" /> Schedule Panel Visit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Secondary Section: Active EVC Inspection Roster */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink">Active Scheduled Visits & Inspection Reports</h3>
            <p className="text-xs text-brand-muted">Scheduled inspection dates, panel convener assignments, and submitted evaluation dossiers</p>
          </div>
          <Link
            to="/officer/evc"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            EVC Registry <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application</th>
                <th className="px-6 py-3.5">Institution</th>
                <th className="px-6 py-3.5">Inspection Type</th>
                <th className="px-6 py-3.5">Scheduled Date</th>
                <th className="px-6 py-3.5">Convener & Expert</th>
                <th className="px-6 py-3.5">Inspection Status</th>
                <th className="px-6 py-3.5 text-right">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {inspections.map((insp) => (
                <tr key={insp.id} className="hover:bg-gray-50/80">
                  <td className="px-6 py-4 font-mono font-bold text-brand-ink">
                    {insp.application_number}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.institution_name}</p>
                    <span className="text-[10px] text-brand-muted">{insp.region}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-brand-ink border border-gray-200">
                      {insp.inspection_type.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-medium">
                    {insp.scheduled_date ? new Date(insp.scheduled_date).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Unscheduled'}
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink">{insp.convener_name || 'Pending Assignment'}</p>
                    <p className="text-[10px] text-brand-muted">{insp.expert_member_name}</p>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={insp.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    {insp.recommendation ? (
                      <span className="text-xs font-bold text-brand-teal">
                        {insp.recommendation.replace(/_/g, ' ')}
                      </span>
                    ) : (
                      <span className="text-[11px] text-brand-muted">Visit Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Schedule EVC Inspection */}
      {schedulingApp && (
        <Modal
          isOpen={true}
          onClose={() => setSchedulingApp(null)}
          title={`Schedule EVC Inspection: ${schedulingApp.application_number}`}
        >
          <form onSubmit={handleScheduleInspection} className="space-y-4 text-xs">
            <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border space-y-1">
              <p className="font-semibold text-brand-ink">Institution: {schedulingApp.institution_name}</p>
              <p className="text-brand-muted">Type: {schedulingApp.application_type.replace(/_/g, ' ')}</p>
              <p className="text-brand-teal font-medium">Region: {schedulingApp.region} Regional Jurisdiction</p>
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Inspection Mode</label>
              <select
                value={inspectionType}
                onChange={(e) => setInspectionType(e.target.value)}
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal"
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
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal"
              />
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Panel Convener Name & Affiliation</label>
              <input
                type="text"
                required
                value={convenerName}
                onChange={(e) => setConvenerName(e.target.value)}
                placeholder="e.g. Prof. Rajesh Sharma (IIT Bombay)"
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal"
              />
            </div>

            <div>
              <label className="block font-bold text-brand-ink mb-1">Subject Expert Member Name & Affiliation</label>
              <input
                type="text"
                required
                value={expertName}
                onChange={(e) => setExpertName(e.target.value)}
                placeholder="e.g. Dr. Ananya Sen (VJTI Mumbai)"
                className="w-full px-3 py-2 border border-brand-border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
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
                className="px-4 py-2 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark font-semibold shadow-sm transition-colors"
              >
                {scheduling ? 'Scheduling...' : 'Confirm & Dispatch Panel Roster'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
export default EVCCoordinatorWorkspace;
