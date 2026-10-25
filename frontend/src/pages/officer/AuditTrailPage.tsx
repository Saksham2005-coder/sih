import React, { useEffect, useState } from 'react';
import {
  ShieldAlert, Filter, Clock, UserCheck, Download,
  Search, ChevronLeft, ChevronRight, RefreshCw, Eye
} from 'lucide-react';
import { api } from '../../api/client';
import { AuditEventItem, AuditExplorerData } from '../../types';
import { Modal } from '../../components/common/Modal';

export const AuditTrailPage: React.FC = () => {
  const [data, setData] = useState<AuditExplorerData>({ items: [], total: 0, page: 1, limit: 25 });
  const [loading, setLoading] = useState(true);
  const [entityFilter, setEntityFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState<AuditEventItem | null>(null);

  const loadAudit = async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await api.getAuditExplorer({
        entity_type: entityFilter || undefined,
        action: actionFilter || undefined,
        search: searchTerm || undefined,
        page: targetPage,
        limit: 25
      });
      setData(res);
      setPage(targetPage);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit(1);
  }, [entityFilter, actionFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadAudit(1);
  };

  const handleExportCsv = () => {
    const params = new URLSearchParams();
    if (entityFilter) params.set('entity_type', entityFilter);
    if (actionFilter) params.set('action', actionFilter);
    window.location.href = `/api/audit/export?${params.toString()}`;
  };

  const totalPages = Math.ceil(data.total / data.limit) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink">Unified Audit Explorer & Ledger</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-brand-teal border border-teal-300">
              Append-Only Non-Repudiable
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Traceable, timestamped audit log capturing stage transitions, deficiency cures, rule publications, and verifications
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadAudit(page)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={handleExportCsv}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-ink text-white hover:bg-gray-800 text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-brand-teal" /> Export Sanitized CSV
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4 text-xs transition-colors">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-auto flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 text-brand-muted dark:text-brand-muted absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by actor name, action, or payload..."
              className="w-full pl-9 pr-3 py-2 border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink rounded-lg text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white text-xs font-semibold shrink-0 transition-colors shadow-sm"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-brand-muted dark:text-brand-muted" />
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-ink focus:ring-1 focus:ring-brand-teal"
            >
              <option value="">All Entity Types</option>
              <option value="APPLICATION">Application</option>
              <option value="DEFICIENCY">Deficiency</option>
              <option value="UNDERTAKING">Compliance Undertaking</option>
              <option value="DOCUMENT">Document</option>
              <option value="EVC">EVC Inspection</option>
              <option value="RULE">Rule Studio</option>
              <option value="ESCALATION">Escalation</option>
            </select>
          </div>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface-elevated rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-ink focus:ring-1 focus:ring-brand-teal"
          >
            <option value="">All Actions</option>
            <option value="STAGE_TRANSITION">STAGE_TRANSITION</option>
            <option value="DEFICIENCY_ISSUED">DEFICIENCY_ISSUED</option>
            <option value="DEFICIENCY_CURED">DEFICIENCY_CURED</option>
            <option value="EVIDENCE_SUBMITTED">EVIDENCE_SUBMITTED</option>
            <option value="EVIDENCE_VERIFIED">EVIDENCE_VERIFIED</option>
            <option value="EVC_SCHEDULED">EVC_SCHEDULED</option>
            <option value="EVC_REPORT_SUBMITTED">EVC_REPORT_SUBMITTED</option>
            <option value="ESCALATION_ACKNOWLEDGED">ESCALATION_ACKNOWLEDGED</option>
            <option value="RULE_PUBLISHED">RULE_PUBLISHED</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border dark:border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Timestamp (IST)</th>
                <th className="px-6 py-3.5">Actor & Scope</th>
                <th className="px-6 py-3.5">Action Executed</th>
                <th className="px-6 py-3.5">Entity Reference</th>
                <th className="px-6 py-3.5">Audit Payload Preview</th>
                <th className="px-6 py-3.5 text-right">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-brand-muted">
                    No audit records match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                data.items.map((ev) => (
                  <tr key={ev.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono text-[11px] text-brand-muted whitespace-nowrap">
                      {new Date(ev.created_at).toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink dark:text-brand-ink">{ev.actor_name || 'System Auto'}</p>
                      <p className="text-[10px] text-brand-teal font-medium">
                        {ev.actor_role?.replace(/_/g, ' ') || 'SYSTEM'}
                      </p>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-xs px-2 py-0.5 rounded bg-brand-porcelain dark:bg-brand-surface-elevated text-brand-ink dark:text-brand-ink border border-brand-border/60 dark:border-brand-border">
                        {ev.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-brand-ink dark:text-brand-ink">
                      {ev.entity_type} #{ev.entity_id}
                    </td>
                    <td className="px-6 py-4 max-w-xs">
                      <span className="font-mono text-[10px] text-brand-muted dark:text-brand-muted line-clamp-2">
                        {ev.details || '—'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedEvent(ev)}
                        className="px-2.5 py-1 rounded border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated text-[11px] font-semibold text-brand-ink dark:text-brand-ink inline-flex items-center gap-1 transition-colors"
                      >
                        <Eye className="w-3 h-3 text-brand-teal" /> Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-6 py-3 border-t border-brand-border dark:border-brand-border bg-brand-porcelain/30 dark:bg-brand-surface-elevated/30 flex items-center justify-between text-xs text-brand-muted dark:text-brand-muted">
          <span>
            Showing page <strong className="text-brand-ink dark:text-brand-ink">{data.page}</strong> of <strong className="text-brand-ink dark:text-brand-ink">{totalPages}</strong> ({data.total} total events)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => loadAudit(data.page - 1)}
              disabled={data.page <= 1 || loading}
              className="px-2.5 py-1 rounded border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface text-brand-ink dark:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated disabled:opacity-50 inline-flex items-center gap-1 font-medium transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Prev
            </button>
            <button
              onClick={() => loadAudit(data.page + 1)}
              disabled={data.page >= totalPages || loading}
              className="px-2.5 py-1 rounded border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface text-brand-ink dark:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated disabled:opacity-50 inline-flex items-center gap-1 font-medium transition-colors"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Audit Detail Modal */}
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onClose={() => setSelectedEvent(null)}
          title={`Audit Record #${selectedEvent.id} — ${selectedEvent.action}`}
          subtitle={`${selectedEvent.entity_type} #${selectedEvent.entity_id}`}
        >
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4 p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border">
              <div>
                <span className="text-[10px] text-brand-muted uppercase font-bold">Timestamp (IST)</span>
                <p className="font-mono text-xs text-brand-ink mt-0.5">
                  {new Date(selectedEvent.created_at).toLocaleString('en-IN', {
                    timeZone: 'Asia/Kolkata',
                    dateStyle: 'full',
                    timeStyle: 'medium',
                  })}
                </p>
              </div>
              <div>
                <span className="text-[10px] text-brand-muted uppercase font-bold">Actor Attribution</span>
                <p className="font-semibold text-xs text-brand-ink mt-0.5">
                  {selectedEvent.actor_name || 'System Daemon'} ({selectedEvent.actor_role || 'SYSTEM'})
                </p>
              </div>
            </div>

            <div>
              <h4 className="font-bold text-brand-ink uppercase text-[10px] tracking-wider mb-2">
                Structured Audit Payload & State Delta
              </h4>
              <div className="p-3 bg-gray-900 text-teal-400 font-mono text-[11px] rounded-lg max-h-60 overflow-y-auto">
                <pre className="whitespace-pre-wrap">
                  {(() => {
                    try {
                      return JSON.stringify(JSON.parse(selectedEvent.details || '{}'), null, 2);
                    } catch {
                      return selectedEvent.details || 'No payload recorded';
                    }
                  })()}
                </pre>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] text-brand-muted">
              <div>IP Origin: <strong className="font-mono text-brand-ink">{selectedEvent.ip_address || '127.0.0.1'}</strong></div>
              <div>Institution Scope: <strong className="text-brand-ink">{selectedEvent.institution_id ? `Inst #${selectedEvent.institution_id}` : 'General / Central'}</strong></div>
            </div>

            <div className="flex justify-end pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-1.5 rounded-lg bg-brand-ink text-white font-semibold"
              >
                Close Audit Record
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
