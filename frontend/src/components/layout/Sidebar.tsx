import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FileText, CheckSquare, FileCheck2, Files,
  Bell, History, Compass, Users, AlertOctagon, BarChart3,
  Sliders, ShieldAlert, Gavel, Cpu, Globe, Award, Calendar
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, activeRole } = useAuth();

  interface NavItem {
    to: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
  }

  let workspaceTitle = 'Institution Portal';
  let workspaceSubtitle = user?.institution_name || 'Apex Institute';
  let links: NavItem[] = [];

  switch (activeRole) {
    case 'INSTITUTION_ADMIN':
      workspaceTitle = 'Institutional Administration';
      workspaceSubtitle = user?.institution_name || 'Apex Institute';
      links = [
        { to: '/institution/dashboard', label: 'Institution Dashboard', icon: LayoutDashboard },
        { to: '/institution/applications', label: 'My Applications', icon: FileText },
        { to: '/institution/action-centre', label: 'Action Centre', icon: CheckSquare, badge: 'Active' },
        { to: '/institution/compliance', label: 'Compliance Passport', icon: FileCheck2 },
        { to: '/institution/documents', label: 'Documents & Renewals', icon: Files },
        { to: '/institution/notifications', label: 'Notifications', icon: Bell },
        { to: '/institution/history', label: 'Submission History', icon: History },
      ];
      break;

    case 'COMPLIANCE_OFFICER':
      workspaceTitle = 'Compliance & Evidence Office';
      workspaceSubtitle = user?.institution_name || 'Apex Institute';
      links = [
        { to: '/institution/compliance-workspace', label: 'Compliance Command', icon: FileCheck2 },
        { to: '/institution/compliance', label: 'Compliance Passport', icon: CheckSquare },
        { to: '/institution/documents', label: 'Documents & Renewals', icon: Files },
        { to: '/institution/action-centre', label: 'Action Centre', icon: AlertOctagon, badge: 'Cures' },
        { to: '/institution/notifications', label: 'Notifications', icon: Bell },
        { to: '/institution/history', label: 'Submission History', icon: History },
      ];
      break;

    case 'REGIONAL_OFFICER':
      workspaceTitle = 'Regional Command Centre';
      workspaceSubtitle = `${user?.region || 'Western'} Regional Office`;
      links = [
        { to: '/officer/regional-workspace', label: 'Regional Command', icon: LayoutDashboard },
        { to: '/officer/applications', label: 'Regional Applications', icon: FileText },
        { to: '/officer/compliance', label: 'Compliance Verification', icon: FileCheck2 },
        { to: '/officer/evc', label: 'EVC Inspection Queue', icon: Compass },
        { to: '/officer/escalations', label: 'Regional Escalations', icon: AlertOctagon, badge: 'SLA' },
        { to: '/officer/reports', label: 'Reports & Analytics', icon: BarChart3 },
        { to: '/officer/notifications/outbox', label: 'Notification Outbox', icon: Bell, badge: 'Live' },
        { to: '/officer/audit', label: 'Immutable Audit Trail', icon: ShieldAlert },
      ];
      break;

    case 'BUREAU_OFFICER':
      workspaceTitle = 'National Bureau Oversight';
      workspaceSubtitle = 'Approval Operations Directorate';
      links = [
        { to: '/officer/bureau-workspace', label: 'Bureau Oversight', icon: Globe },
        { to: '/officer/applications', label: 'National Registry', icon: FileText },
        { to: '/officer/compliance', label: 'Compliance Monitoring', icon: FileCheck2 },
        { to: '/officer/evc', label: 'EVC Inspection Queue', icon: Compass },
        { to: '/officer/escalations', label: 'Multi-Tier Escalations', icon: AlertOctagon, badge: 'SLA' },
        { to: '/officer/reports', label: 'Performance & Trends', icon: BarChart3 },
        { to: '/officer/notifications/outbox', label: 'Notification Outbox', icon: Bell, badge: 'Live' },
        { to: '/officer/audit', label: 'Immutable Audit Trail', icon: ShieldAlert },
      ];
      break;

    case 'COMMITTEE_MEMBER':
      workspaceTitle = 'Standing Hearing Committee';
      workspaceSubtitle = 'SAC / CAC Panel Member';
      links = [
        { to: '/officer/committee-workspace', label: 'Hearing Command', icon: Users },
        { to: '/officer/applications', label: 'Assigned Docket', icon: FileText },
        { to: '/officer/evc', label: 'Assigned EVC Panels', icon: Compass },
        { to: '/institution/notifications', label: 'Notifications', icon: Bell },
      ];
      break;

    case 'EVC_COORDINATOR':
      workspaceTitle = 'EVC Coordination Office';
      workspaceSubtitle = `${user?.region || 'Western'} EVC Directorate`;
      links = [
        { to: '/officer/evc-workspace', label: 'EVC Scheduling Command', icon: Compass },
        { to: '/officer/evc', label: 'Inspection Queue & Rosters', icon: Calendar },
        { to: '/officer/applications', label: 'Eligible Applications', icon: FileText },
        { to: '/institution/notifications', label: 'Notifications', icon: Bell },
      ];
      break;

    case 'COMPETENT_AUTHORITY':
      workspaceTitle = 'Apex Competent Authority';
      workspaceSubtitle = 'Member Secretary Directorate';
      links = [
        { to: '/officer/authority-workspace', label: 'Statutory Order Command', icon: Gavel },
        { to: '/officer/applications', label: 'Decision Queue', icon: FileText },
        { to: '/officer/reports', label: 'Case Dossiers & Briefs', icon: BarChart3 },
        { to: '/officer/escalations', label: 'Council Escalations', icon: Award, badge: 'L3' },
        { to: '/officer/audit', label: 'Immutable Audit Trail', icon: ShieldAlert },
      ];
      break;

    case 'SYSTEM_ADMIN':
      workspaceTitle = 'Platform System Admin';
      workspaceSubtitle = 'Security & Telemetry Engine';
      links = [
        { to: '/officer/admin-workspace', label: 'System Admin Workspace', icon: Cpu },
        { to: '/officer/admin', label: 'Diagnostics & Accounts', icon: Users },
        { to: '/officer/rules', label: 'Regulatory Rule Studio', icon: Sliders },
        { to: '/officer/escalations', label: 'SLA Engine & Scans', icon: AlertOctagon },
        { to: '/officer/notifications/outbox', label: 'Outbox & Delivery', icon: Bell, badge: 'Live' },
        { to: '/officer/audit', label: 'Immutable Audit Explorer', icon: ShieldAlert },
        { to: '/officer/reports', label: 'System Analytics', icon: BarChart3 },
      ];
      break;

    default:
      links = [
        { to: '/institution/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/institution/applications', label: 'Applications', icon: FileText },
      ];
  }

  return (
    <aside className="w-64 bg-brand-sidebar-bg border-r border-brand-border flex flex-col justify-between shrink-0 shadow-sm min-h-[calc(100vh-4rem)] transition-colors">
      <div className="p-4">
        {/* Scoped Workspace Identifier */}
        <div className="mb-4 px-3 py-2.5 bg-brand-surface-secondary rounded-lg border border-brand-border">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-text-muted">Operational Scope</p>
          <p className="text-xs font-bold text-brand-text-primary mt-0.5 truncate">
            {workspaceTitle}
          </p>
          <p className="text-[11px] text-brand-teal font-medium mt-0.5 truncate">
            {workspaceSubtitle}
          </p>
          <div className="mt-1.5 pt-1.5 border-t border-brand-border flex items-center justify-between text-[10px]">
            <span className="font-semibold text-brand-text-muted">Role:</span>
            <span className="font-mono font-bold text-brand-text-primary bg-brand-surface px-1.5 py-0.5 rounded border border-brand-border">
              {activeRole}
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors duration-150 ${
                    isActive
                      ? 'bg-brand-sidebar-active-bg text-brand-sidebar-active-text border border-brand-teal/40 shadow-xs font-semibold'
                      : 'text-brand-sidebar-muted hover:bg-brand-surface-secondary hover:text-brand-text-primary'
                  }`
                }
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{link.label}</span>
                </div>
                {link.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-brand-warning-surface text-brand-warning-text border border-amber-300 dark:border-brand-warning-border">
                    {link.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-brand-border bg-brand-surface-secondary/40">
        <div className="flex items-center justify-between text-[11px] text-brand-text-muted">
          <span>AICTE PS 26262</span>
          <span>v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
