import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, Check } from 'lucide-react';
import { api } from '../../api/client';
import { NotificationItem } from '../../types';

export const NotificationsPage: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifs = async () => {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifs();
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-brand-ink">Institutional Notifications & Alerts</h1>
          <p className="text-xs text-brand-muted mt-0.5">
            Real-time regulatory notices, deficiency dispatches, and statutory deadline alerts
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-brand-border shadow-sm divide-y divide-gray-100 overflow-hidden">
        {notifications.length === 0 ? (
          <div className="p-12 text-center text-xs text-brand-muted">
            <Bell className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            No notifications in log.
          </div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 flex items-start justify-between gap-4 transition-colors ${
                !n.is_read ? 'bg-amber-50/20' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg shrink-0 mt-0.5">
                  {n.level === 'DANGER' ? (
                    <AlertTriangle className="w-5 h-5 text-brand-red" />
                  ) : n.level === 'WARNING' ? (
                    <AlertTriangle className="w-5 h-5 text-[#C5892B]" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-brand-teal" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-brand-ink">{n.title}</h4>
                    {!n.is_read && (
                      <span className="w-2 h-2 rounded-full bg-brand-teal" />
                    )}
                  </div>
                  <p className="text-xs text-brand-muted mt-1 leading-relaxed">{n.message}</p>
                  <p className="text-[10px] text-gray-400 mt-1.5">
                    {new Date(n.created_at).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                </div>
              </div>

              {!n.is_read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="px-2.5 py-1 rounded text-xs font-medium text-brand-muted hover:text-brand-ink hover:bg-gray-100 border border-brand-border shrink-0 flex items-center gap-1"
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
