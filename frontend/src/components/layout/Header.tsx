import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bell, Shield, LogOut, CheckCircle2, AlertTriangle, Layers,
  Radio, RefreshCw, Send, ExternalLink, X, Compass
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { NotificationItem, LiveSSEEventSummary } from '../../types';
import { ThemeToggle } from '../common/ThemeToggle';

export const Header: React.FC = () => {
  const { user, activeRole, switchActiveRole, logout, login, getWorkspaceHome } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [demoUsers, setDemoUsers] = useState<any[]>([]);
  const [isSseActive, setIsSseActive] = useState<boolean>(false);
  const [liveToast, setLiveToast] = useState<LiveSSEEventSummary | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const toastTimeoutRef = useRef<any>(null);

  const handleDemoUserChange = async (targetEmail: string) => {
    try {
      const loggedIn = await login(targetEmail);
      const defaultRole = loggedIn?.roles?.[0];
      const dest = getWorkspaceHome(defaultRole);
      navigate(dest);
    } catch (err) {
      console.error('Failed to switch demo persona:', err);
    }
  };

  const handleRoleChange = async (newRole: string) => {
    try {
      await switchActiveRole(newRole);
      const dest = getWorkspaceHome(newRole);
      navigate(dest);
    } catch (err) {
      console.error('Failed to switch role:', err);
    }
  };

  const isOfficer = user?.roles?.some(r => [
    'REGIONAL_OFFICER', 'BUREAU_OFFICER', 'COMMITTEE_MEMBER',
    'EVC_COORDINATOR', 'COMPETENT_AUTHORITY', 'SYSTEM_ADMIN'
  ].includes(r));

  const fetchNotifs = async () => {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch {
      // silent fallback
    }
  };

  const fetchDemoUsers = async () => {
    try {
      const data = await api.getDemoUsers();
      setDemoUsers(data.demo_users);
    } catch {
      // silent
    }
  };

  // Initial load
  useEffect(() => {
    if (user) {
      fetchNotifs();
      fetchDemoUsers();
    }
  }, [user]);

  // Real-Time Server-Sent Events (SSE) + Interval Polling Fallback
  useEffect(() => {
    if (!user) return;

    const token = localStorage.getItem('reguflow_token');
    if (!token) return;

    let isCancelled = false;
    let es: EventSource | null = null;
    let fallbackInterval: any = null;

    const setupSSE = async () => {
      try {
        const ticketRes = await api.getStreamTicket();
        if (isCancelled) return;
        const sseUrl = `/api/notifications/stream?ticket=${encodeURIComponent(ticketRes.ticket)}`;
        es = new EventSource(sseUrl);
        eventSourceRef.current = es;

        es.onopen = () => {
          setIsSseActive(true);
        };

        es.addEventListener('connected', () => {
          setIsSseActive(true);
        });

        es.addEventListener('notification', (event: MessageEvent) => {
          try {
            const payload: LiveSSEEventSummary = JSON.parse(event.data);
            // Show live toast banner
            setLiveToast(payload);
            if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
            toastTimeoutRef.current = setTimeout(() => {
              setLiveToast(null);
            }, 6000);

            // Refresh persistent notifications list
            fetchNotifs();
          } catch {
            // ignore parsing error
          }
        });

        es.onerror = () => {
          // SSE disconnected, fallback to active polling
          setIsSseActive(false);
          if (es) {
            es.close();
            es = null;
          }
        };
      } catch {
        setIsSseActive(false);
      }
    };

    setupSSE();

    // Polling fallback every 25 seconds for unread count synchronization
    fallbackInterval = setInterval(async () => {
      try {
        const countData = await api.getNotificationUnreadCount();
        const localUnread = notifications.filter(n => !n.is_read).length;
        if (countData.unread_count !== localUnread) {
          fetchNotifs();
        }
      } catch {
        // silent
      }
    }, 25000);

    return () => {
      isCancelled = true;
      if (es) {
        es.close();
      }
      if (fallbackInterval) {
        clearInterval(fallbackInterval);
      }
      if (toastTimeoutRef.current) {
        clearTimeout(toastTimeoutRef.current);
      }
    };
  }, [user]);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-[var(--brand-header-bg)] text-[var(--brand-header-text)] border-b border-[var(--brand-header-border)] shadow-md transition-colors">
        <div className="px-6 h-16 flex items-center justify-between">
          {/* Brand identity */}
          <div className="flex items-center gap-3">
            <img
              src="/aicte-logo.png"
              alt="AICTE Official Logo"
              className="w-10 h-10 object-contain shrink-0 rounded-full bg-white/95 p-0.5 shadow-sm border border-brand-border/40"
            />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[var(--brand-header-text)] flex items-center gap-1.5">
                  <span className="font-semibold text-white tracking-normal">आवेदनसेतु</span>
                  <span className="text-gray-400 font-light text-xs">/</span>
                  <span className="text-[#39C6B4]">AvedanSetu</span>
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#143633] text-[#39C6B4] border border-[#225650]">
                  AICTE PS 26262
                </span>
              </div>
              <p className="text-[11px] text-[var(--brand-header-muted)]">अखिल भारतीय तकनीकी शिक्षा परिषद • AICTE Regulatory Portal</p>
            </div>

            <div className="hidden xl:flex items-center gap-2 ml-3 pl-3 border-l border-[#274059]">
              <span className="text-xs text-[var(--brand-header-muted)]">Academic Cycle:</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#182C40] text-[var(--brand-header-text)] border border-[#274059]">
                2026-2027
              </span>
            </div>
          </div>

          {/* Actions & Profile */}
          <div className="flex items-center gap-3">
            {/* Judge Demo Centre & Live Workflow Explorer Link */}
            <Link
              to="/demo/explorer"
              className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#143633] text-[#39C6B4] border border-[#225650] hover:bg-[#1a4743] hover:text-[#52e0ce] text-xs font-bold transition-colors shadow-xs"
              title="Open Judge Regulatory Demonstration Centre & Live Workflow Explorer"
            >
              <Compass className="w-3.5 h-3.5" /> Demo Centre
            </Link>

            {/* Demo Persona Quick-Switch */}
            <div className="hidden md:flex items-center gap-1.5 bg-[#182C40] px-2.5 py-1 rounded-md border border-[#274059] text-xs">
              <span className="text-[var(--brand-header-muted)] flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-[#39C6B4]" /> Demo:
              </span>
              <select
                value={user?.email || ''}
                onChange={(e) => handleDemoUserChange(e.target.value)}
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
                  onChange={(e) => handleRoleChange(e.target.value)}
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

            {/* Notifications Drawer Toggle with Live Telemetry Indicator */}
            <div className="relative">
              <button
                onClick={() => setShowNotifDropdown(!showNotifDropdown)}
                className="relative p-2 rounded-lg text-[var(--brand-header-muted)] hover:text-white hover:bg-[#182C40] transition-colors"
                title={isSseActive ? 'Real-Time SSE Live Stream Active' : 'Notifications (Polling fallback active)'}
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-brand-red text-white text-[10px] font-bold flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
                {/* Real-time SSE Connection Status Dot */}
                <span
                  className={`absolute bottom-1 right-1 w-2 h-2 rounded-full ${
                    isSseActive ? 'bg-emerald-400 ring-2 ring-[#101E2D] animate-pulse' : 'bg-amber-400 ring-2 ring-[#101E2D]'
                  }`}
                  title={isSseActive ? 'Live SSE Connected' : 'Polling Sync Fallback Active'}
                />
              </button>

              {showNotifDropdown && (
                <div className="absolute right-0 mt-2 w-88 sm:w-96 bg-brand-surface-elevated text-brand-text-primary rounded-xl shadow-2xl border border-brand-border py-2 z-50 animate-fadeIn">
                  <div className="px-4 py-2 border-b border-brand-border flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-brand-text-primary">Notifications & Live Stream</span>
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        isSseActive ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-600 border border-amber-500/30'
                      }`}>
                        <Radio className="w-2.5 h-2.5 animate-pulse" />
                        {isSseActive ? 'SSE LIVE' : 'POLLING SYNC'}
                      </span>
                    </div>
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
                              <AlertTriangle className="w-3.5 h-3.5 text-[#F58F98] shrink-0" />
                            ) : (
                              <CheckCircle2 className="w-3.5 h-3.5 text-[#39C6B4] shrink-0" />
                            )}
                            <span className="truncate">{n.title}</span>
                          </div>
                          <p className="text-brand-text-secondary line-clamp-2">{n.message}</p>
                          {n.link_url && (
                            <Link
                              to={n.link_url}
                              onClick={() => setShowNotifDropdown(false)}
                              className="text-[10px] text-brand-teal hover:underline mt-1 inline-flex items-center gap-1"
                            >
                              Open Case <ExternalLink className="w-2.5 h-2.5" />
                            </Link>
                          )}
                        </div>
                      ))
                    )}
                  </div>

                  {/* Dropdown Footer: Quick Link to Outbox for Officers */}
                  {isOfficer && (
                    <div className="px-4 py-2 border-t border-brand-border bg-brand-surface-secondary/50 flex items-center justify-between text-[11px]">
                      <span className="text-brand-text-muted">Reliable Delivery Engine</span>
                      <Link
                        to="/officer/notifications/outbox"
                        onClick={() => setShowNotifDropdown(false)}
                        className="font-semibold text-brand-teal hover:underline flex items-center gap-1"
                      >
                        Notification Outbox <ExternalLink className="w-3 h-3" />
                      </Link>
                    </div>
                  )}
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

      {/* Floating Real-Time SSE Toast Banner */}
      {liveToast && (
        <div className="fixed bottom-6 right-6 z-50 max-w-sm w-full bg-brand-surface-elevated text-brand-text-primary border border-brand-teal/40 rounded-xl shadow-2xl p-4 animate-slideUp">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-md bg-brand-teal/15 text-brand-teal">
                <Radio className="w-4 h-4 animate-pulse" />
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-teal">
                  Live Event Received (SSE)
                </span>
                <h4 className="text-xs font-bold text-brand-text-primary line-clamp-1">{liveToast.title}</h4>
              </div>
            </div>
            <button
              onClick={() => setLiveToast(null)}
              className="text-brand-text-muted hover:text-brand-text-primary p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className="text-[11px] text-brand-text-secondary mt-2 line-clamp-2">
            {liveToast.message}
          </p>
          {liveToast.link_url && (
            <div className="mt-2.5 pt-2 border-t border-brand-border flex justify-end">
              <Link
                to={liveToast.link_url}
                onClick={() => setLiveToast(null)}
                className="text-[11px] font-semibold text-brand-teal hover:underline inline-flex items-center gap-1"
              >
                View Updated Case <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default Header;
