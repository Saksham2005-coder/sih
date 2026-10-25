import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, Check, Filter, ExternalLink, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import { NotificationItem } from '../../types';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string>('');

  const loadNotifs = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications({
        unread_only: unreadOnly || undefined,
        level: levelFilter || undefined,
      });
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifs();
  }, [unreadOnly, levelFilter]);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink">Institutional Notifications & Alerts</h1>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-red text-white">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Real-time regulatory notices, deficiency dispatches, and statutory deadline alerts
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
              unreadOnly
                ? 'bg-brand-teal text-white border-brand-teal'
                : 'bg-white dark:bg-brand-surface text-brand-ink dark:text-brand-ink border-brand-border dark:border-brand-border hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated'
            }`}
          >
            {unreadOnly ? 'Showing Unread' : 'Show Unread Only'}
          </button>

          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="border border-brand-border dark:border-brand-border rounded-lg px-2.5 py-1.5 text-xs text-brand-ink dark:text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal bg-white dark:bg-brand-surface-elevated"
          >
            <option value="">All Severities</option>
            <option value="DANGER">Critical (Danger)</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Informational</option>
          </select>

          <button
            onClick={loadNotifs}
            className="p-1.5 rounded-lg border border-brand-border dark:border-brand-border bg-white dark:bg-brand-surface text-brand-muted dark:text-brand-muted hover:text-brand-ink dark:hover:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated transition-colors"
            title="Refresh notifications"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications List */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm divide-y divide-brand-border/60 dark:divide-brand-border overflow-hidden transition-colors">
        {notifications.length === 0 ? (
          <div className="p-12 text-center text-xs text-brand-muted dark:text-brand-muted">
            <Bell className="w-8 h-8 text-brand-muted/40 mx-auto mb-2" />
            No notifications found for selected filters.
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 flex flex-col sm:flex-row sm:items-start justify-between gap-4 transition-colors ${
                !n.is_read
                  ? 'bg-amber-50/40 dark:bg-amber-950/20'
                  : 'hover:bg-brand-porcelain/40 dark:hover:bg-brand-surface-elevated/40'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg shrink-0 mt-0.5">
                  {n.level === 'DANGER' ? (
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  ) : n.level === 'WARNING' ? (
                    <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-brand-teal" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-brand-ink dark:text-brand-ink">{n.title}</h4>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-brand-teal" />
                    )}
                    {n.delivery_channel && n.delivery_channel !== 'IN_APP' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-brand-porcelain dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted border border-brand-border/60 dark:border-brand-border">
                        {n.delivery_channel}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-brand-muted dark:text-brand-muted mt-1 leading-relaxed">{n.message}</p>
                  
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-brand-muted dark:text-brand-muted">
                    <span>
                      {new Date(n.created_at).toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </span>
                    {n.link_url && (
                      <Link
                        to={n.link_url}
                        className="text-brand-teal font-semibold hover:underline flex items-center gap-1"
                      >
                        Take Action <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>

              {!n.is_read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="px-2.5 py-1 rounded text-xs font-medium text-brand-muted dark:text-brand-muted hover:text-brand-ink dark:hover:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated border border-brand-border dark:border-brand-border shrink-0 self-end sm:self-auto flex items-center gap-1 transition-colors"
                >
                  <Check className="w-3.5 h-3.5" /> Mark Read
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
