import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './queryClient';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';

// Institution Pages
import { InstitutionDashboard } from './pages/institution/InstitutionDashboard';
import { ComplianceOfficerWorkspace } from './pages/institution/ComplianceOfficerWorkspace';
import { MyApplications } from './pages/institution/MyApplications';
import { ApplicationDetail } from './pages/institution/ApplicationDetail';
import { ActionCentre } from './pages/institution/ActionCentre';
import { CompliancePassport } from './pages/institution/CompliancePassport';
import { DocumentsRenewals } from './pages/institution/DocumentsRenewals';
import { NotificationsPage } from './pages/institution/NotificationsPage';
import { SubmissionHistory } from './pages/institution/SubmissionHistory';

// Officer Pages
import { OfficerDashboard } from './pages/officer/OfficerDashboard';
import { RegionalOfficerWorkspace } from './pages/officer/RegionalOfficerWorkspace';
import { BureauOfficerWorkspace } from './pages/officer/BureauOfficerWorkspace';
import { CommitteeMemberWorkspace } from './pages/officer/CommitteeMemberWorkspace';
import { EVCCoordinatorWorkspace } from './pages/officer/EVCCoordinatorWorkspace';
import { CompetentAuthorityWorkspace } from './pages/officer/CompetentAuthorityWorkspace';
import { SystemAdminWorkspace } from './pages/officer/SystemAdminWorkspace';
import { ApplicationRegistry } from './pages/officer/ApplicationRegistry';
import { OfficerApplicationDetail } from './pages/officer/OfficerApplicationDetail';
import { EVCQueue } from './pages/officer/EVCQueue';
import { ComplianceMonitoring } from './pages/officer/ComplianceMonitoring';
import { EscalationsPage } from './pages/officer/EscalationsPage';
import { ReportsPage } from './pages/officer/ReportsPage';
import { AuditTrailPage } from './pages/officer/AuditTrailPage';
import { RuleStudioPage } from './pages/officer/RuleStudioPage';
import { AdminPage } from './pages/officer/AdminPage';
import { NotificationOutboxPage } from './pages/officer/NotificationOutboxPage';
import { MobileFieldInspectionPage } from './pages/officer/MobileFieldInspectionPage';

import { PublicOrderVerification } from './pages/PublicOrderVerification';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-xs text-brand-muted">Authenticating session...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const RootRedirect: React.FC = () => {
  const { user, getWorkspaceHome } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={getWorkspaceHome()} replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/verify-order" element={<PublicOrderVerification />} />
            <Route path="/verify-order/:token" element={<PublicOrderVerification />} />
            <Route path="/" element={<RootRedirect />} />

            {/* Protected Portal Routes under AppLayout */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              {/* Institution Portal */}
              <Route path="/institution/dashboard" element={<InstitutionDashboard />} />
              <Route path="/institution/compliance-workspace" element={<ComplianceOfficerWorkspace />} />
              <Route path="/institution/applications" element={<MyApplications />} />
              <Route path="/institution/applications/:id" element={<ApplicationDetail />} />
              <Route path="/institution/action-centre" element={<ActionCentre />} />
              <Route path="/institution/compliance" element={<CompliancePassport />} />
              <Route path="/institution/documents" element={<DocumentsRenewals />} />
              <Route path="/institution/notifications" element={<NotificationsPage />} />
              <Route path="/institution/history" element={<SubmissionHistory />} />

              {/* AICTE Officer Portal & Dedicated Role Workspaces */}
              <Route path="/officer/dashboard" element={<OfficerDashboard />} />
              <Route path="/officer/regional-workspace" element={<RegionalOfficerWorkspace />} />
              <Route path="/officer/bureau-workspace" element={<BureauOfficerWorkspace />} />
              <Route path="/officer/committee-workspace" element={<CommitteeMemberWorkspace />} />
              <Route path="/officer/evc-workspace" element={<EVCCoordinatorWorkspace />} />
              <Route path="/officer/authority-workspace" element={<CompetentAuthorityWorkspace />} />
              <Route path="/officer/admin-workspace" element={<SystemAdminWorkspace />} />

              {/* Functional Officer Modules */}
              <Route path="/officer/applications" element={<ApplicationRegistry />} />
              <Route path="/officer/applications/:id" element={<OfficerApplicationDetail />} />
              <Route path="/officer/evc" element={<EVCQueue />} />
              <Route path="/officer/evc/field/:id" element={<MobileFieldInspectionPage />} />
              <Route path="/officer/evc/inspections/:id" element={<MobileFieldInspectionPage />} />
              <Route path="/officer/compliance" element={<ComplianceMonitoring />} />
              <Route path="/officer/escalations" element={<EscalationsPage />} />
              <Route path="/officer/reports" element={<ReportsPage />} />
              <Route path="/officer/audit" element={<AuditTrailPage />} />
              <Route path="/officer/rules" element={<RuleStudioPage />} />
              <Route path="/officer/admin" element={<AdminPage />} />
              <Route path="/officer/notifications/outbox" element={<NotificationOutboxPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </QueryClientProvider>
);
};

export default App;
