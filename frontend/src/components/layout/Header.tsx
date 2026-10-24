import React, { useState, useEffect } from 'react';
import { Bell, Shield, User as UserIcon, LogOut, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { NotificationItem } from '../../types';

export const Header: React.FC = () => {
  const { user, activeRole, switchActiveRole, logout, login } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [demoUsers, setDemoUsers] = useState<any[]>([]);

  useEffect(() => {
    async function fetchNotifs() {
      try {
        const data = await api.getNotifications();
        setNotifications(data);
      } catch {
        // silent fallback
      }
    }
    async function fetchDemoUsers() {
      try {
        const data = await api.getDemoUsers();
        setDemoUsers(data.demo_users);
      } catch {
        // silent
      }
    }
    if (user) {
      fetchNotifs();
      fetchDemoUsers();
    }
  }, [user]);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="sticky top-0 z-40 w-full bg-brand-ink text-white border-b border-gray-800 shadow-md">
      <div className="px-6 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-brand-teal flex items-center justify-center font-bold text-lg text-white shadow-inner">
              R
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight">ReguFlow 360</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-brand-teal/30 text-teal-300 border border-teal-500/30">
                  AICTE PS 26262
                </span>
              </div>
              <p className="text-[11px] text-gray-400">Integrated Regulatory Workflow & Compliance Platform</p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-2 ml-4 pl-4 border-l border-gray-700/60">
            <span className="text-xs text-gray-400">Academic Cycle:</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-800 text-gray-200 border border-gray-700">
              2026-2027
            </span>
          </div>
        </div>

        {/* Actions & Profile */}
        <div className="flex items-center gap-3">
          {/* Demo Persona Quick-Switch */}
          <div className="hidden md:flex items-center gap-1.5 bg-gray-800/80 px-2.5 py-1 rounded-md border border-gray-700 text-xs">
            <span className="text-gray-400 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-brand-teal" /> Demo:
            </span>
            <select
              value={user?.email || ''}
              onChange={(e) => login(e.target.value)}
              className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
            >
              {demoUsers.map((u) => (
                <option key={u.email} value={u.email} className="bg-brand-ink text-white">
                  {u.full_name} ({u.roles[0].replace(/_/g, ' ')})
                </option>
              ))}
            </select>
          </div>

          {/* Active Role Selector if user has multiple roles */}
          {user && user.roles.length > 1 && (
            <div className="flex items-center gap-1 bg-gray-800 px-2 py-1 rounded border border-gray-700 text-xs">
              <Shield className="w-3.5 h-3.5 text-brand-teal" />
              <select
                value={activeRole || ''}
                onChange={(e) => switchActiveRole(e.target.value)}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer text-xs"
              >
                {user.roles.map(r => (
                  <option key={r} value={r} className="bg-brand-ink text-white">
                    {r.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Notifications Drawer Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
              className="relative p-2 rounded-lg text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
              title="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-brand-red text-white text-[10px] font-bold flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>

            {showNotifDropdown && (
              <div className="absolute right-0 mt-2 w-80 bg-white text-brand-ink rounded-lg shadow-2xl border border-brand-border py-2 z-50">
                <div className="px-4 py-2 border-b border-brand-border flex items-center justify-between">
                  <span className="font-semibold text-xs text-brand-ink">Notifications & Alerts</span>
                  <span className="text-[11px] text-brand-muted">{notifications.length} total</span>
                </div>
                <div className="max-h-72 overflow-y-auto divide-y divide-gray-100">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-xs text-brand-muted">No pending alerts.</div>
                  ) : (
                    notifications.map(n => (
                      <div key={n.id} className="p-3 hover:bg-gray-50 text-xs">
                        <div className="flex items-center gap-1.5 font-medium text-brand-ink mb-1">
                          {n.level === 'DANGER' ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-brand-red" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" />
                          )}
                          <span>{n.title}</span>
                        </div>
                        <p className="text-brand-muted line-clamp-2">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User profile & Logout */}
          <div className="flex items-center gap-3 pl-2 border-l border-gray-700">
            <div className="flex flex-col text-right">
              <span className="text-xs font-semibold leading-tight">{user?.full_name}</span>
              <span className="text-[10px] text-gray-400">
                {user?.institution_name || (user?.region ? `${user.region} Region` : 'AICTE Apex')}
              </span>
            </div>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
