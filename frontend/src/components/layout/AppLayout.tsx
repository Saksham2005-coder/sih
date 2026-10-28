import React, { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../context/AuthContext';

export const AppLayout: React.FC = () => {
  const { user, activeRole, getWorkspaceHome } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Guard against route-role desynchronization:
  // When activeRole switches, automatically navigate out of incompatible workspace views
  useEffect(() => {
    if (!user || !activeRole) return;
    const path = location.pathname;

    const roleWorkspaceMap: Record<string, string> = {
      '/institution/dashboard': 'INSTITUTION_ADMIN',
      '/institution/compliance-workspace': 'COMPLIANCE_OFFICER',
      '/officer/regional-workspace': 'REGIONAL_OFFICER',
      '/officer/bureau-workspace': 'BUREAU_OFFICER',
      '/officer/committee-workspace': 'COMMITTEE_MEMBER',
      '/officer/evc-workspace': 'EVC_COORDINATOR',
      '/officer/authority-workspace': 'COMPETENT_AUTHORITY',
      '/officer/admin-workspace': 'SYSTEM_ADMIN',
    };

    const isOfficer = [
      'REGIONAL_OFFICER', 'BUREAU_OFFICER', 'COMMITTEE_MEMBER',
      'EVC_COORDINATOR', 'COMPETENT_AUTHORITY', 'SYSTEM_ADMIN'
    ].includes(activeRole);
    const isInst = ['INSTITUTION_ADMIN', 'COMPLIANCE_OFFICER'].includes(activeRole);

    // If viewing a role-specific workspace of a different role, navigate to current active role workspace
    if (roleWorkspaceMap[path] && roleWorkspaceMap[path] !== activeRole) {
      navigate(getWorkspaceHome(activeRole), { replace: true });
    } else if (isInst && path.startsWith('/officer')) {
      navigate(getWorkspaceHome(activeRole), { replace: true });
    } else if (isOfficer && path.startsWith('/institution')) {
      navigate(getWorkspaceHome(activeRole), { replace: true });
    }
  }, [activeRole, user?.id, location.pathname, getWorkspaceHome, navigate]);

  return (
    <div className="min-h-screen bg-brand-canvas text-brand-text-primary flex flex-col transition-colors duration-150">
      <Header />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <main className="flex-1 min-w-0 p-6 lg:p-8 overflow-y-auto text-brand-text-primary w-full">
          <div className="max-w-7xl mx-auto w-full space-y-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
