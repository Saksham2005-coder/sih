import React, { useEffect, useState } from 'react';
import { AlertOctagon, CheckCircle2, Play, ShieldAlert, Clock, ArrowRight } from 'lucide-react';
import { api } from '../../api/client';
import { AlertEscalationItem } from '../../types';
import { Modal } from '../../components/common/Modal';

export const EscalationsPage: React.FC = () => {
  const [escalations, setEscalations] = useState<AlertEscalationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  const loadEscalations = async () => {
    try {
      const data = await api.getEscalations();
      setEscalations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEscalations();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.runDeadlineScan();
      setScanResult(
        `Idempotent Scan Finished: ${res.scanned_entities} scanned, ${res.reminders_created} reminders, ${res.escalations_created} escalations created, ${res.duplicates_prevented} duplicate alerts prevented (${res.execution_time_ms}ms).`
      );
      loadEscalations();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await api.acknowledgeEscalation(id);
      loadEscalations();
    } catch (err: any) {
      alert(err.message || 'Acknowledgement failed');
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

        <button
          onClick={handleScan}
          disabled={scanning}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-ink text-white text-xs font-semibold hover:bg-gray-800 shadow-sm transition-colors"
        >
          <Play className={`w-3.5 h-3.5 text-brand-teal ${scanning ? 'animate-spin' : ''}`} />
          {scanning ? 'Running Evaluation...' : 'Trigger Deadline Scan'}
        </button>
      </div>

      {scanResult && (
        <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg text-xs text-teal-800 font-medium">
          {scanResult}
        </div>
      )}

      {/* Escalations Table */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Escalation Tier</th>
                <th className="px-6 py-3.5">Entity</th>
                <th className="px-6 py-3.5">Trigger Condition</th>
                <th className="px-6 py-3.5">Breach Days</th>
                <th className="px-6 py-3.5">Target Role</th>
                <th className="px-6 py-3.5">Idempotency Key</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {escalations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-brand-muted">
                    No active escalations recorded.
                  </td>
                </tr>
              ) : (
                escalations.map((esc) => (
                  <tr key={esc.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-bold text-brand-red flex items-center gap-1.5">
                      <AlertOctagon className="w-4 h-4 text-brand-red shrink-0" />
                      {esc.escalation_level.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 font-semibold text-brand-ink">
                      {esc.entity_type} #{esc.entity_id}
                    </td>
                    <td className="px-6 py-4 text-brand-muted">
                      {esc.trigger_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 font-bold text-brand-red">
                      +{esc.threshold_days} days
                    </td>
                    <td className="px-6 py-4 text-brand-muted font-medium">
                      {esc.recipient_role.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
                        {esc.idempotency_key.substring(0, 12)}...
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          esc.status === 'ACTIVE'
                            ? 'bg-red-100 text-brand-red border border-red-200'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {esc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {esc.status === 'ACTIVE' ? (
                        <button
                          onClick={() => handleAcknowledge(esc.id)}
                          className="px-2.5 py-1 rounded bg-brand-ink hover:bg-gray-800 text-white text-xs font-semibold shadow-sm"
                        >
                          Acknowledge
                        </button>
                      ) : (
                        <span className="text-[11px] text-teal-800 font-semibold flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged
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
    </div>
  );
};
