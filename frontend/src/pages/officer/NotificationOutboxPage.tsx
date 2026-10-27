import React, { useState, useEffect } from 'react';
import {
  Mail, MessageSquare, Bell, RefreshCw, Send, AlertTriangle,
  CheckCircle2, Clock, XCircle, ShieldCheck, Server, Radio,
  Filter, Search, ExternalLink, RotateCcw, Info
} from 'lucide-react';
import { api } from '../../api/client';
import {
  NotificationOutboxItem,
  NotificationOutboxSummary,
  NotificationChannelStatus,
} from '../../types';

export const NotificationOutboxPage: React.FC = () => {
  const [items, setItems] = useState<NotificationOutboxItem[]>([]);
  const [summary, setSummary] = useState<NotificationOutboxSummary | null>(null);
  const [channelStatus, setChannelStatus] = useState<NotificationChannelStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDispatching, setIsDispatching] = useState(false);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Filters
  const [channelFilter, setChannelFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<NotificationOutboxItem | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [outboxData, summaryData, channelsData] = await Promise.all([
        api.getNotificationOutbox({
          channel: channelFilter !== 'ALL' ? channelFilter : undefined,
          status: statusFilter !== 'ALL' ? statusFilter : undefined,
          limit: 100,
        }),
        api.getOutboxSummary(),
        api.getNotificationChannelsStatus(),
      ]);
      setItems(outboxData);
      setSummary(summaryData);
      setChannelStatus(channelsData);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load notification outbox records');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [channelFilter, statusFilter]);

  const handleManualRetry = async (id: number) => {
    setRetryingId(id);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await api.retryOutboxItem(id);
      setSuccessMsg(`Dispatch #${id} queued for retry. Current status: ${updated.status}`);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || `Failed to retry outbox item #${id}`);
    } finally {
      setRetryingId(null);
    }
  };

  const handleTriggerDispatch = async () => {
    setIsDispatching(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await api.triggerOutboxDispatch();
      setSuccessMsg(`Outbox worker executed: ${res.summary.accepted || 0} accepted, ${res.summary.simulated || 0} simulated, ${res.summary.retry_scheduled || 0} retried.`);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to trigger outbox dispatch worker');
    } finally {
      setIsDispatching(false);
    }
  };

  const filteredItems = items.filter(item => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.subject?.toLowerCase().includes(term) ||
      item.recipient_email?.toLowerCase().includes(term) ||
      item.recipient_phone?.toLowerCase().includes(term) ||
      item.idempotency_key?.toLowerCase().includes(term) ||
      item.template_code?.toLowerCase().includes(term) ||
      String(item.entity_id).includes(term)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACCEPTED_BY_PROVIDER':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-[#0E746B]/15 text-[#0E746B] dark:text-[#39C6B4] border border-[#0E746B]/30">
            <CheckCircle2 className="w-3 h-3" /> Accepted by Relay
          </span>
        );
      case 'SIMULATED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/15 text-blue-700 dark:text-blue-300 border border-blue-500/30">
            <Server className="w-3 h-3" /> Simulated (Sandbox)
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3" /> Not Configured
          </span>
        );
      case 'RETRY_SCHEDULED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/15 text-purple-700 dark:text-purple-300 border border-purple-500/30">
            <Clock className="w-3 h-3" /> Backoff Retry
          </span>
        );
      case 'DEAD_LETTER':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-red-500/15 text-red-700 dark:text-red-300 border border-red-500/30">
            <XCircle className="w-3 h-3" /> Dead Letter
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/15 text-slate-700 dark:text-slate-300 border border-slate-500/30">
            <Clock className="w-3 h-3" /> Queued
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            {status}
          </span>
        );
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'EMAIL':
        return <Mail className="w-4 h-4 text-blue-500" />;
      case 'SMS':
        return <MessageSquare className="w-4 h-4 text-emerald-500" />;
      case 'IN_APP':
        return <Bell className="w-4 h-4 text-amber-500" />;
      default:
        return <Send className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Page Header */}
      <div className="bg-brand-surface p-6 rounded-xl border border-brand-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-brand-teal/10 rounded-lg text-brand-teal">
              <Radio className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-brand-text-primary tracking-tight">
                Reliable Notification Outbox & Event Telemetry
              </h1>
              <p className="text-xs text-brand-text-muted mt-0.5">
                Transactional outbox architecture, provider delivery evidence, retry backoff state, and real-time SSE stream.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={isLoading}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg border border-brand-border bg-brand-surface-secondary text-brand-text-primary hover:bg-brand-surface-secondary/80 flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleTriggerDispatch}
            disabled={isDispatching}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-brand-teal text-white hover:bg-brand-teal/90 flex items-center gap-2 shadow-sm transition-colors disabled:opacity-50"
          >
            <Send className={`w-3.5 h-3.5 ${isDispatching ? 'animate-spin' : ''}`} />
            Trigger Dispatch Cycle
          </button>
        </div>
      </div>

      {/* Alert Banners */}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-xs text-red-800 dark:text-red-200 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>{errorMsg}</div>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          <div>{successMsg}</div>
        </div>
      )}

      {/* Delivery Channels Health & Transport Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Email SMTP Channel */}
        {(() => {
          const emailCh = channelStatus?.channels.find(c => c.channel === 'EMAIL');
          const isConf = emailCh?.is_configured;
          return (
            <div className="bg-brand-surface p-4 rounded-xl border border-brand-border shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="flex items-center gap-2 text-xs font-bold text-brand-text-primary">
                    <Mail className="w-4 h-4 text-blue-500" />
                    Email Transport (SMTP)
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isConf ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30'
                  }`}>
                    {isConf ? 'CONFIGURED' : 'NOT CONFIGURED'}
                  </span>
                </div>
                <p className="text-[11px] text-brand-text-muted">
                  MTA Relay: <span className="font-mono text-brand-text-primary">{emailCh?.details?.host || 'NOT_CONFIGURED'}:{emailCh?.details?.port || 587}</span>
                </p>
                <p className="text-[11px] text-brand-text-muted mt-0.5">
                  Sender: <span className="text-brand-text-primary">{emailCh?.details?.sender || 'AICTE ReguFlow 360'}</span>
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-brand-border text-[10px] text-brand-text-muted flex items-center gap-1.5">
                <Info className="w-3 h-3 text-blue-500 shrink-0" />
                <span>Status 250 records relay acceptance, never falsely claims recipient delivery.</span>
              </div>
            </div>
          );
        })()}

        {/* SMS Gateway Adapter Boundary */}
        {(() => {
          const smsCh = channelStatus?.channels.find(c => c.channel === 'SMS');
          const isConf = smsCh?.is_configured;
          return (
            <div className="bg-brand-surface p-4 rounded-xl border border-brand-border shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="flex items-center gap-2 text-xs font-bold text-brand-text-primary">
                    <MessageSquare className="w-4 h-4 text-emerald-500" />
                    SMS Gateway (CDAC/NIC)
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isConf ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30' : 'bg-blue-500/15 text-blue-700 dark:text-blue-300 border border-blue-500/30'
                  }`}>
                    {isConf ? 'GATEWAY ACTIVE' : 'SIMULATED / SANDBOX'}
                  </span>
                </div>
                <p className="text-[11px] text-brand-text-muted">
                  Gateway: <span className="font-mono text-brand-text-primary">{smsCh?.details?.gateway_url || 'SANDBOX_ADAPTER'}</span>
                </p>
                <p className="text-[11px] text-brand-text-muted mt-0.5">
                  Sender ID: <span className="font-mono font-bold text-brand-text-primary">{smsCh?.details?.sender_id || 'AICTEN'}</span>
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-brand-border text-[10px] text-brand-text-muted flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-emerald-500 shrink-0" />
                <span>Adapter boundary configured. Never claims carrier delivery without live provider evidence.</span>
              </div>
            </div>
          );
        })()}

        {/* Live SSE Stream Telemetry */}
        {(() => {
          const sseCh = channelStatus?.channels.find(c => c.channel === 'SSE_STREAM');
          return (
            <div className="bg-brand-surface p-4 rounded-xl border border-brand-border shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="flex items-center gap-2 text-xs font-bold text-brand-text-primary">
                    <Radio className="w-4 h-4 text-purple-500" />
                    Live SSE Pub/Sub Broker
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30">
                    ACTIVE
                  </span>
                </div>
                <p className="text-[11px] text-brand-text-muted">
                  Active Subscribers: <span className="font-bold text-brand-text-primary">{channelStatus?.active_sse_subscribers || 0}</span>
                </p>
                <p className="text-[11px] text-brand-text-muted mt-0.5">
                  Heartbeat: <span className="text-brand-text-primary">15s ping interval | Process-local AsyncIO broker</span>
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-brand-border text-[10px] text-brand-text-muted flex items-center gap-1.5">
                <Radio className="w-3 h-3 text-purple-500 shrink-0" />
                <span>Process-local broker; cross-worker state is synchronized via database-backed polling fallback.</span>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Metrics Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-brand-text-muted">Total Dispatches</span>
            <div className="text-xl font-bold text-brand-text-primary mt-1">{summary.total}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-slate-500">Queued</span>
            <div className="text-xl font-bold text-slate-600 dark:text-slate-300 mt-1">{summary.queued}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-emerald-600">Accepted by Relay</span>
            <div className="text-xl font-bold text-emerald-600 mt-1">{summary.accepted_by_provider}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-blue-600">Simulated</span>
            <div className="text-xl font-bold text-blue-600 mt-1">{summary.simulated}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-amber-600">Unconfigured</span>
            <div className="text-xl font-bold text-amber-600 mt-1">{summary.not_configured}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-purple-600">Backoff Retry</span>
            <div className="text-xl font-bold text-purple-600 mt-1">{summary.retry_scheduled}</div>
          </div>
          <div className="bg-brand-surface p-3.5 rounded-lg border border-brand-border">
            <span className="text-[10px] font-semibold uppercase text-red-600">Dead Letter</span>
            <div className="text-xl font-bold text-red-600 mt-1">{summary.dead_letter}</div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-brand-surface p-4 rounded-xl border border-brand-border shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Channel Filter */}
          <div className="flex items-center gap-1.5 text-xs text-brand-text-muted">
            <Filter className="w-3.5 h-3.5" />
            <span>Channel:</span>
            <select
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
              className="bg-brand-surface-secondary text-brand-text-primary px-2.5 py-1.5 rounded-md border border-brand-border focus:outline-none text-xs"
            >
              <option value="ALL">All Channels</option>
              <option value="EMAIL">Email (SMTP)</option>
              <option value="SMS">SMS Gateway</option>
              <option value="IN_APP">In-App Alerts</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-brand-text-muted">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-brand-surface-secondary text-brand-text-primary px-2.5 py-1.5 rounded-md border border-brand-border focus:outline-none text-xs"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACCEPTED_BY_PROVIDER">Accepted by Relay</option>
              <option value="SIMULATED">Simulated</option>
              <option value="NOT_CONFIGURED">Not Configured</option>
              <option value="RETRY_SCHEDULED">Backoff Retry</option>
              <option value="DEAD_LETTER">Dead Letter</option>
              <option value="QUEUED">Queued</option>
            </select>
          </div>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 text-brand-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search subject, recipient, idempotency key..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-brand-surface-secondary text-brand-text-primary text-xs pl-9 pr-3 py-1.5 rounded-md border border-brand-border focus:outline-none focus:border-brand-teal"
          />
        </div>
      </div>

      {/* Outbox Table */}
      <div className="bg-brand-surface rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-brand-surface-secondary border-b border-brand-border text-[11px] font-semibold text-brand-text-muted uppercase tracking-wider">
                <th className="py-3 px-4">Channel & Recipient</th>
                <th className="py-3 px-4">Event & Template</th>
                <th className="py-3 px-4">Delivery Status</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Next Retry / Sent</th>
                <th className="py-3 px-4">Outcome / Provider ID</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-divider">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-brand-text-muted">
                    No notification outbox records found matching filters.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-brand-surface-secondary/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-md bg-brand-surface-secondary shrink-0">
                          {getChannelIcon(item.channel)}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-brand-text-primary truncate">
                            {item.recipient_email || item.recipient_phone || 'In-App Broadcast'}
                          </p>
                          <p className="text-[10px] text-brand-text-muted truncate">
                            {item.region ? `${item.region} Region` : 'Apex / National'} {item.institution_id ? `• Inst #${item.institution_id}` : ''}
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <p className="font-medium text-brand-text-primary truncate max-w-xs">{item.subject}</p>
                      <span className="font-mono text-[10px] text-brand-text-muted">{item.template_code}</span>
                    </td>

                    <td className="py-3 px-4">
                      {getStatusBadge(item.status)}
                    </td>

                    <td className="py-3 px-4">
                      <span className="font-mono font-semibold text-brand-text-primary">
                        {item.attempt_count} / {item.max_attempts}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-[11px] text-brand-text-muted">
                      {item.sent_at ? (
                        <span className="text-emerald-600 font-medium">Sent: {new Date(item.sent_at).toLocaleTimeString()}</span>
                      ) : item.next_retry_at ? (
                        <span className="text-purple-600 font-medium">Retry: {new Date(item.next_retry_at).toLocaleTimeString()}</span>
                      ) : (
                        <span>{new Date(item.created_at).toLocaleTimeString()}</span>
                      )}
                    </td>

                    <td className="py-3 px-4 max-w-xs">
                      {item.provider_message_id ? (
                        <p className="font-mono text-[10px] text-brand-text-muted truncate" title={item.provider_message_id}>
                          {item.provider_message_id}
                        </p>
                      ) : item.last_error_message ? (
                        <p className="text-[10px] text-red-600 truncate" title={item.last_error_message}>
                          {item.last_error_message}
                        </p>
                      ) : (
                        <span className="text-brand-text-muted text-[10px]">-</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="px-2 py-1 rounded text-[11px] font-medium border border-brand-border bg-brand-surface-secondary text-brand-text-primary hover:bg-brand-surface-secondary/80 transition-colors"
                        >
                          Inspect
                        </button>
                        {(item.status === 'DEAD_LETTER' || item.status === 'FAILED' || item.status === 'NOT_CONFIGURED') && (
                          <button
                            onClick={() => handleManualRetry(item.id)}
                            disabled={retryingId === item.id}
                            className="px-2.5 py-1 rounded text-[11px] font-semibold bg-brand-teal text-white hover:bg-brand-teal/90 flex items-center gap-1 transition-colors disabled:opacity-50"
                            title="Re-enqueue for manual dispatch retry"
                          >
                            <RotateCcw className={`w-3 h-3 ${retryingId === item.id ? 'animate-spin' : ''}`} />
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Item Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
          <div className="bg-brand-surface rounded-xl border border-brand-border shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-brand-border">
              <div className="flex items-center gap-2">
                {getChannelIcon(selectedItem.channel)}
                <h3 className="text-sm font-bold text-brand-text-primary">
                  Outbox Dispatch #{selectedItem.id} Details
                </h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-brand-text-muted hover:text-brand-text-primary text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-brand-text-muted font-medium">Idempotency Key:</span>
                <p className="font-mono text-[11px] text-brand-text-primary break-all bg-brand-surface-secondary p-1.5 rounded mt-0.5">
                  {selectedItem.idempotency_key}
                </p>
              </div>
              <div>
                <span className="text-brand-text-muted font-medium">Correlation ID:</span>
                <p className="font-mono text-[11px] text-brand-text-primary break-all bg-brand-surface-secondary p-1.5 rounded mt-0.5">
                  {selectedItem.correlation_id}
                </p>
              </div>
            </div>

            <div className="text-xs space-y-1">
              <span className="text-brand-text-muted font-medium">Subject:</span>
              <p className="font-semibold text-brand-text-primary">{selectedItem.subject}</p>
            </div>

            <div className="text-xs space-y-1">
              <span className="text-brand-text-muted font-medium">Rendered Plain Text Body:</span>
              <pre className="p-3 bg-brand-surface-secondary rounded border border-brand-border font-mono text-[11px] whitespace-pre-wrap text-brand-text-primary max-h-48 overflow-y-auto">
                {selectedItem.body_text}
              </pre>
            </div>

            {selectedItem.link_url && (
              <div className="text-xs flex items-center gap-2">
                <span className="text-brand-text-muted font-medium">Deep Link URL:</span>
                <a
                  href={selectedItem.link_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-teal hover:underline flex items-center gap-1 font-mono"
                >
                  {selectedItem.link_url} <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}

            <div className="pt-3 border-t border-brand-border flex items-center justify-between text-xs">
              <div>
                <span className="text-brand-text-muted">Status: </span>
                {getStatusBadge(selectedItem.status)}
              </div>
              <div className="flex gap-2">
                {(selectedItem.status === 'DEAD_LETTER' || selectedItem.status === 'FAILED') && (
                  <button
                    onClick={() => {
                      handleManualRetry(selectedItem.id);
                      setSelectedItem(null);
                    }}
                    className="px-3 py-1.5 rounded bg-brand-teal text-white font-semibold text-xs flex items-center gap-1.5 hover:bg-brand-teal/90"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Re-enqueue for Retry
                  </button>
                )}
                <button
                  onClick={() => setSelectedItem(null)}
                  className="px-3 py-1.5 rounded border border-brand-border text-brand-text-primary text-xs font-semibold hover:bg-brand-surface-secondary"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationOutboxPage;
