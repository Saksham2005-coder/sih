import React, { useEffect, useState } from 'react';
import { AlertOctagon, CheckCircle2, Play, ShieldAlert, Clock, ArrowRight, Activity, Filter, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { AlertEscalationItem, DeadlineEngineStatus } from '../../types';
import { Modal } from '../../components/common/Modal';

export const EscalationsPage: React.FC = () => {
  const [escalations, setEscalations] = useState<AlertEscalationItem[]>([]);
  const [engineStatus, setEngineStatus] = useState<DeadlineEngineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [entityFilter, setEntityFilter] = useState<string>('');
  
  // Acknowledge Modal
  const [ackModalOpen, setAckModalOpen] = useState(false);
  const [selectedEsc, setSelectedEsc] = useState<AlertEscalationItem | null>(null);
  const [ackRemarks, setAckRemarks] = useState('');
  const [submittingAck, setSubmittingAck] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [escData, statusData] = await Promise.all([
        api.getEscalations({
          status_filter: statusFilter || undefined,
          entity_type: entityFilter || undefined,
        }),
        api.getEngineStatus().catch(() => null)
      ]);
      setEscalations(escData);
      if (statusData) setEngineStatus(statusData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, entityFilter]);

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.runDeadlineScan();
      setScanResult(
        `Scan Finished (${res.run_id || 'IDEMPOTENT'}): ${res.scanned_entities} scanned, ${res.reminders_created} reminders, ${res.escalations_created} escalations created, ${res.duplicates_prevented} duplicate alerts prevented (${res.execution_time_ms}ms).`
      );
      loadData();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleOpenAcknowledge = (esc: AlertEscalationItem) => {
    setSelectedEsc(esc);
    setAckRemarks('Escalation reviewed. Communication dispatched to responsible officer for immediate compliance.');
    setAckModalOpen(true);
  };

  const handleAcknowledgeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEsc) return;
    setSubmittingAck(true);
    try {
      await api.acknowledgeEscalation(selectedEsc.id, ackRemarks);
      setAckModalOpen(false);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Acknowledgement failed');
    } finally {
      setSubmittingAck(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-brand-ink">Automated Escalations & SLA Management</h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Idempotent deadline evaluation and progressive hierarchical escalation (RO → BO → Apex)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="p-2 rounded-lg border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface text-brand-muted dark:text-brand-muted hover:text-brand-ink dark:hover:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated shadow-sm transition-colors"
            title="Refresh Escalations"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white text-xs font-semibold shadow-sm transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Running Evaluation...' : 'Trigger Deadline Scan'}
          </button>
        </div>
      </div>

      {scanResult && (
        <div className="p-3 bg-teal-50 dark:bg-brand-teal/15 border border-teal-200 dark:border-brand-teal/30 rounded-lg text-xs text-teal-900 dark:text-teal-200 font-medium">
          {scanResult}
        </div>
      )}

      {/* Engine Status Banner */}
      {engineStatus && (
        <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-4 shadow-sm grid grid-cols-2 sm:grid-cols-5 gap-4 text-xs transition-colors">
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-muted dark:text-brand-muted tracking-wider">Engine State</span>
            <p className="font-bold text-brand-ink dark:text-brand-ink flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${engineStatus.is_running ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              {engineStatus.is_running ? 'Autonomous Loop' : 'On-Demand Only'}
            </p>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-muted dark:text-brand-muted tracking-wider">Scan Cadence</span>
            <p className="font-bold text-brand-ink dark:text-brand-ink mt-0.5">Every {engineStatus.scan_interval_seconds}s</p>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-muted dark:text-brand-muted tracking-wider">Last Scan Time</span>
            <p className="font-bold text-brand-ink dark:text-brand-ink mt-0.5">
              {engineStatus.last_run
                ? new Date(engineStatus.last_run.created_at).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })
                : 'Pending Initial Run'}
            </p>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-muted dark:text-brand-muted tracking-wider">Lifetime Scanned</span>
            <p className="font-bold text-brand-teal mt-0.5">{engineStatus.total_scanned} entities</p>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-brand-muted dark:text-brand-muted tracking-wider">Duplicates Barred</span>
            <p className="font-bold text-emerald-700 dark:text-emerald-400 mt-0.5">{engineStatus.total_duplicates_prevented} duplicate blocks</p>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-white dark:bg-brand-surface p-3 rounded-xl border border-brand-border dark:border-brand-border text-xs transition-colors">
        <Filter className="w-4 h-4 text-brand-muted dark:text-brand-muted" />
        <span className="font-semibold text-brand-ink dark:text-brand-ink">Filter Queue:</span>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1 text-xs text-brand-ink dark:text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal"
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">ACTIVE Escalations</option>
          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
          <option value="RESOLVED">RESOLVED</option>
        </select>

        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1 text-xs text-brand-ink dark:text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal"
        >
          <option value="">All Entities</option>
          <option value="APPLICATION">Applications (Stage SLA)</option>
          <option value="UNDERTAKING">Undertakings (Compliance)</option>
          <option value="DOCUMENT">Prescribed Documents (Expiry)</option>
          <option value="EVC">EVC Inspections</option>
        </select>
      </div>

      {/* Escalations Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border dark:border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Escalation Tier</th>
                <th className="px-6 py-3.5">Target Entity</th>
                <th className="px-6 py-3.5">Trigger Condition</th>
                <th className="px-6 py-3.5">SLA Breach</th>
                <th className="px-6 py-3.5">Recipient Role & Scope</th>
                <th className="px-6 py-3.5">Cycle & Hash</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 dark:divide-brand-border">
              {escalations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-brand-muted dark:text-brand-muted">
                    No escalations recorded for selected filters.
                  </td>
                </tr>
              ) : (
                escalations.map((esc) => (
                  <tr key={esc.id} className="hover:bg-brand-porcelain/50 dark:hover:bg-brand-surface-elevated/50 transition-colors">
                    <td className="px-6 py-4 font-bold text-red-600 dark:text-red-400 flex items-center gap-1.5">
                      <AlertOctagon className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0" />
                      {esc.escalation_level.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 font-semibold text-brand-ink dark:text-brand-ink">
                      {esc.entity_type === 'APPLICATION' ? (
                        <Link to={`/officer/applications/${esc.entity_id}`} className="text-brand-teal hover:underline">
                          App #{esc.entity_id}
                        </Link>
                      ) : (
                        `${esc.entity_type} #${esc.entity_id}`
                      )}
                    </td>
                    <td className="px-6 py-4 text-brand-muted dark:text-brand-muted">
                      {esc.trigger_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 font-bold text-red-600 dark:text-red-400">
                      +{esc.threshold_days} days
                    </td>
                    <td className="px-6 py-4 text-brand-muted dark:text-brand-muted font-medium">
                      <span className="text-brand-ink dark:text-brand-ink">{esc.recipient_role.replace(/_/g, ' ')}</span>
                      {esc.region && (
                        <span className="block text-[10px] text-brand-muted">Region: {esc.region}</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-[9px] text-brand-muted bg-brand-porcelain dark:bg-brand-surface-elevated px-1.5 py-0.5 rounded border border-brand-border/60 dark:border-brand-border">
                        {esc.cycle_id ? `[${esc.cycle_id}] ` : ''}
                        {esc.idempotency_key.substring(0, 10)}...
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          esc.status === 'ACTIVE'
                            ? 'bg-red-100 dark:bg-red-950/40 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800/40'
                            : esc.status === 'ACKNOWLEDGED'
                            ? 'bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40'
                            : 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40'
                        }`}
                      >
                        {esc.status}
                      </span>
                      {esc.resolved_reason && (
                        <span className="block text-[9px] text-brand-muted mt-0.5">{esc.resolved_reason}</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {esc.status === 'ACTIVE' ? (
                        <button
                          onClick={() => handleOpenAcknowledge(esc)}
                          className="px-2.5 py-1 rounded bg-brand-ink hover:bg-gray-800 text-white text-xs font-semibold shadow-sm transition-colors"
                        >
                          Acknowledge
                        </button>
                      ) : esc.status === 'ACKNOWLEDGED' ? (
                        <span className="text-[11px] text-amber-800 dark:text-amber-300 font-semibold flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" /> In Review
                        </span>
                      ) : (
                        <span className="text-[11px] text-emerald-700 dark:text-emerald-400 font-semibold flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Resolved
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Acknowledge Modal */}
      <Modal
        isOpen={ackModalOpen}
        onClose={() => setAckModalOpen(false)}
        title="Acknowledge SLA Escalation"
        subtitle={`${selectedEsc?.entity_type} #${selectedEsc?.entity_id} — ${selectedEsc?.escalation_level}`}
      >
        <form onSubmit={handleAcknowledgeSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink dark:text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Officer Action / Follow-Up Remarks
            </label>
            <textarea
              rows={3}
              required
              value={ackRemarks}
              onChange={(e) => setAckRemarks(e.target.value)}
              className="w-full border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg p-2.5 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setAckModalOpen(false)}
              className="px-4 py-2 border border-brand-border dark:border-brand-border rounded-lg text-brand-ink dark:text-brand-ink font-semibold hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingAck}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-hover shadow-sm transition-colors"
            >
              {submittingAck ? 'Recording...' : 'Record Acknowledgment'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
