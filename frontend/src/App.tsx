import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';

// Institution Pages
import { InstitutionDashboard } from './pages/institution/InstitutionDashboard';
import { MyApplications } from './pages/institution/MyApplications';
import { ApplicationDetail } from './pages/institution/ApplicationDetail';
import { ActionCentre } from './pages/institution/ActionCentre';
import { CompliancePassport } from './pages/institution/CompliancePassport';
import { DocumentsRenewals } from './pages/institution/DocumentsRenewals';
import { NotificationsPage } from './pages/institution/NotificationsPage';
import { SubmissionHistory } from './pages/institution/SubmissionHistory';

// Officer Pages
import { OfficerDashboard } from './pages/officer/OfficerDashboard';
import { ApplicationRegistry } from './pages/officer/ApplicationRegistry';
import { OfficerApplicationDetail } from './pages/officer/OfficerApplicationDetail';
import { EVCQueue } from './pages/officer/EVCQueue';
import { ComplianceMonitoring } from './pages/officer/ComplianceMonitoring';
import { EscalationsPage } from './pages/officer/EscalationsPage';
import { ReportsPage } from './pages/officer/ReportsPage';
import { AuditTrailPage } from './pages/officer/AuditTrailPage';
import { RuleStudioPage } from './pages/officer/RuleStudioPage';
import { AdminPage } from './pages/officer/AdminPage';

const queryClient = new QueryClient();

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
  const { user, isOfficer } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (isOfficer) return <Navigate to="/officer/dashboard" replace />;
  return <Navigate to="/institution/dashboard" replace />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
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
              <Route path="/institution/applications" element={<MyApplications />} />
              <Route path="/institution/applications/:id" element={<ApplicationDetail />} />
              <Route path="/institution/action-centre" element={<ActionCentre />} />
              <Route path="/institution/compliance" element={<CompliancePassport />} />
              <Route path="/institution/documents" element={<DocumentsRenewals />} />
              <Route path="/institution/notifications" element={<NotificationsPage />} />
              <Route path="/institution/history" element={<SubmissionHistory />} />

              {/* AICTE Officer Portal */}
              <Route path="/officer/dashboard" element={<OfficerDashboard />} />
              <Route path="/officer/applications" element={<ApplicationRegistry />} />
              <Route path="/officer/applications/:id" element={<OfficerApplicationDetail />} />
              <Route path="/officer/evc" element={<EVCQueue />} />
              <Route path="/officer/compliance" element={<ComplianceMonitoring />} />
              <Route path="/officer/escalations" element={<EscalationsPage />} />
              <Route path="/officer/reports" element={<ReportsPage />} />
              <Route path="/officer/audit" element={<AuditTrailPage />} />
              <Route path="/officer/rules" element={<RuleStudioPage />} />
              <Route path="/officer/admin" element={<AdminPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
