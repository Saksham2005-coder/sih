import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FileText, CheckSquare, FileCheck2, Files,
  Bell, History, Compass, Users, AlertOctagon, BarChart3,
  Sliders, ShieldAlert, ArrowLeftRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { isOfficer, isInstitutionUser, activeRole } = useAuth();
  const location = useLocation();

  const isCurrentOfficerPath = location.pathname.startsWith('/officer');

  const institutionLinks = [
    { to: '/institution/dashboard', label: 'Institution Dashboard', icon: LayoutDashboard },
    { to: '/institution/applications', label: 'My Applications', icon: FileText },
    { to: '/institution/action-centre', label: 'Action Centre', icon: CheckSquare, badge: 'Active' },
    { to: '/institution/compliance', label: 'Compliance Passport', icon: FileCheck2 },
    { to: '/institution/documents', label: 'Documents & Renewals', icon: Files },
    { to: '/institution/notifications', label: 'Notifications', icon: Bell },
    { to: '/institution/history', label: 'Submission History', icon: History },
  ];

  const officerLinks = [
    { to: '/officer/dashboard', label: 'Officer Dashboard', icon: LayoutDashboard },
    { to: '/officer/applications', label: 'Application Registry', icon: FileText },
    { to: '/officer/evc', label: 'EVC Inspection Queue', icon: Compass },
    { to: '/officer/compliance', label: 'Compliance Monitoring', icon: FileCheck2 },
    { to: '/officer/escalations', label: 'Escalations & SLA', icon: AlertOctagon, badge: 'SLA' },
    { to: '/officer/reports', label: 'Reports & Analytics', icon: BarChart3 },
    { to: '/officer/audit', label: 'Immutable Audit Trail', icon: ShieldAlert },
    { to: '/officer/rules', label: 'Rule Studio', icon: Sliders },
    { to: '/officer/admin', label: 'Administration', icon: Users },
  ];

  const links = isCurrentOfficerPath ? officerLinks : institutionLinks;

  return (
    <aside className="w-64 bg-white border-r border-brand-border flex flex-col justify-between shrink-0 shadow-sm min-h-[calc(100vh-4rem)]">
      <div className="p-4">
        {/* Workspace Identifier */}
        <div className="mb-4 px-3 py-2 bg-brand-porcelain rounded-lg border border-brand-border">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-muted">Active Workspace</p>
          <p className="text-xs font-bold text-brand-ink mt-0.5">
            {isCurrentOfficerPath ? 'AICTE Officer Command Center' : 'Institution Portal'}
          </p>
          <p className="text-[11px] text-brand-teal font-medium mt-0.5">
            Role: {activeRole?.replace(/_/g, ' ')}
          </p>
        </div>

        {/* Portal Switcher (Quick Toggle for Demo) */}
        <div className="mb-4">
          <NavLink
            to={isCurrentOfficerPath ? '/institution/dashboard' : '/officer/dashboard'}
            className="flex items-center justify-center gap-2 w-full py-1.5 px-3 rounded-md text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-brand-ink border border-gray-300 transition-colors"
          >
            <ArrowLeftRight className="w-3.5 h-3.5 text-brand-teal" />
            Switch to {isCurrentOfficerPath ? 'Institution Portal' : 'Officer Portal'}
          </NavLink>
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
                  `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-teal text-white shadow-sm font-semibold'
                      : 'text-brand-muted hover:bg-gray-100 hover:text-brand-ink'
                  }`
                }
              >
                <div className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{link.label}</span>
                </div>
                {link.badge && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-[#C5892B] border border-amber-300">
                    {link.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-brand-border bg-brand-porcelain/40">
        <div className="flex items-center justify-between text-[11px] text-brand-muted">
          <span>AICTE PS 26262</span>
          <span>v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};
