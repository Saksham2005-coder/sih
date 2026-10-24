import React, { useEffect, useState } from 'react';
import { ShieldAlert, Filter, Clock, UserCheck } from 'lucide-react';
import { api } from '../../api/client';
import { AuditEventItem } from '../../types';

export const AuditTrailPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState('');

  const loadAudit = async () => {
    try {
      const data = await api.getAuditTrail({ entity_type: entityFilter || undefined });
      setEvents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, [entityFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink">Immutable Audit Trail</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-brand-teal border border-teal-300">
              Append-Only Ledger
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Non-repudiable audit recording of all stage transitions, deficiency cures, and verifications
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-brand-muted" />
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="border border-brand-border rounded-lg px-2.5 py-1.5 text-xs text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal"
          >
            <option value="">All Entity Types</option>
            <option value="APPLICATION">Application</option>
            <option value="DEFICIENCY">Deficiency</option>
            <option value="UNDERTAKING">Compliance Undertaking</option>
            <option value="DOCUMENT">Document</option>
            <option value="EVC">EVC Inspection</option>
            <option value="RULE">Rule Studio</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Timestamp (IST)</th>
                <th className="px-6 py-3.5">Actor & Role</th>
                <th className="px-6 py-3.5">Action</th>
                <th className="px-6 py-3.5">Entity</th>
                <th className="px-6 py-3.5">Audit Payload & Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-brand-muted">
                    No audit events recorded for current filter.
                  </td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono text-[11px] text-brand-muted whitespace-nowrap">
                      {new Date(ev.created_at).toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{ev.actor_name || 'System Auto'}</p>
                      <p className="text-[10px] text-brand-teal font-medium">
                        {ev.actor_role?.replace(/_/g, ' ') || 'SYSTEM'}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-xs px-2 py-0.5 rounded bg-gray-100 text-brand-ink border border-gray-200">
                        {ev.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-brand-ink">
                      {ev.entity_type} #{ev.entity_id}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-mono text-[10px] text-brand-muted line-clamp-2 max-w-md">
                        {ev.details || '—'}
                      </span>
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
