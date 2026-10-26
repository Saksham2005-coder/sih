import React, { useState, useEffect } from 'react';
import { Bell, Shield, LogOut, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { NotificationItem } from '../../types';
import { ThemeToggle } from '../common/ThemeToggle';

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
    <header className="sticky top-0 z-40 w-full bg-[var(--brand-header-bg)] text-[var(--brand-header-text)] border-b border-[var(--brand-header-border)] shadow-md transition-colors">
      <div className="px-6 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-brand-action flex items-center justify-center font-bold text-lg text-white shadow-inner">
              R
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[var(--brand-header-text)]">ReguFlow 360</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#143633] text-[#39C6B4] border border-[#225650]">
                  AICTE PS 26262
                </span>
              </div>
              <p className="text-[11px] text-[var(--brand-header-muted)]">Integrated Regulatory Workflow & Compliance Platform</p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-2 ml-4 pl-4 border-l border-[#274059]">
            <span className="text-xs text-[var(--brand-header-muted)]">Academic Cycle:</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#182C40] text-[var(--brand-header-text)] border border-[#274059]">
              2026-2027
            </span>
          </div>
        </div>

        {/* Actions & Profile */}
        <div className="flex items-center gap-3">
          {/* Demo Persona Quick-Switch */}
          <div className="hidden md:flex items-center gap-1.5 bg-[#182C40] px-2.5 py-1 rounded-md border border-[#274059] text-xs">
            <span className="text-[var(--brand-header-muted)] flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-[#39C6B4]" /> Demo:
            </span>
            <select
              value={user?.email || ''}
              onChange={(e) => login(e.target.value)}
              className="bg-transparent text-[var(--brand-header-text)] font-medium focus:outline-none cursor-pointer"
            >
              {demoUsers.map((u) => (
                <option key={u.email} value={u.email} className="bg-[#101E2D] text-[#EDF3F8]">
                  {u.full_name} ({u.roles?.[0] ? u.roles[0].replace(/_/g, ' ') : 'USER'})
                </option>
              ))}
            </select>
          </div>

          {/* Active Role Selector if user has multiple roles */}
          {user && user.roles.length > 1 && (
            <div className="flex items-center gap-1 bg-[#182C40] px-2 py-1 rounded border border-[#274059] text-xs">
              <Shield className="w-3.5 h-3.5 text-[#39C6B4]" />
              <select
                value={activeRole || ''}
                onChange={(e) => switchActiveRole(e.target.value)}
                className="bg-transparent text-[var(--brand-header-text)] font-semibold focus:outline-none cursor-pointer text-xs"
              >
                {user.roles.map(r => (
                  <option key={r} value={r} className="bg-[#101E2D] text-[#EDF3F8]">
                    {r.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* One-Click Theme Switcher Toggle */}
          <ThemeToggle showLabel className="border-[#274059] bg-[#182C40] text-[var(--brand-header-text)] hover:bg-[#20364C] hover:text-white shadow-sm" />

          {/* Notifications Drawer Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
              className="relative p-2 rounded-lg text-[var(--brand-header-muted)] hover:text-white hover:bg-[#182C40] transition-colors"
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
              <div className="absolute right-0 mt-2 w-80 bg-brand-surface-elevated text-brand-text-primary rounded-lg shadow-2xl border border-brand-border py-2 z-50 animate-fadeIn">
                <div className="px-4 py-2 border-b border-brand-border flex items-center justify-between">
                  <span className="font-semibold text-xs text-brand-text-primary">Notifications & Alerts</span>
                  <span className="text-[11px] text-brand-text-muted">{notifications.length} total</span>
                </div>
                <div className="max-h-72 overflow-y-auto divide-y divide-brand-divider">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-xs text-brand-text-muted">No pending alerts.</div>
                  ) : (
                    notifications.map(n => (
                      <div key={n.id} className="p-3 hover:bg-brand-surface-secondary text-xs transition-colors">
                        <div className="flex items-center gap-1.5 font-medium text-brand-text-primary mb-1">
                          {n.level === 'DANGER' ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-[#F58F98]" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#39C6B4]" />
                          )}
                          <span>{n.title}</span>
                        </div>
                        <p className="text-brand-text-secondary line-clamp-2">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User profile & Logout */}
          <div className="flex items-center gap-3 pl-2 border-l border-[#274059]">
            <div className="flex flex-col text-right">
              <span className="text-xs font-semibold leading-tight text-[var(--brand-header-text)]">{user?.full_name}</span>
              <span className="text-[10px] text-[var(--brand-header-muted)]">
                {user?.institution_name || (user?.region ? `${user.region} Region` : 'AICTE Apex')}
              </span>
            </div>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-[var(--brand-header-muted)] hover:text-white hover:bg-[#182C40] transition-colors"
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

export default Header;
