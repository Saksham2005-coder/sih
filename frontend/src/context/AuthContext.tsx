import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../api/client';
import { queryClient } from '../queryClient';

interface AuthContextType {
  user: User | null;
  token: string | null;
  activeRole: string | null;
  login: (email: string, password?: string) => Promise<User>;
  logout: () => void;
  switchActiveRole: (role: string) => void;
  isInstitutionUser: boolean;
  isOfficer: boolean;
  isInstitutionAdmin: boolean;
  isComplianceOfficer: boolean;
  isRegionalOfficer: boolean;
  isBureauOfficer: boolean;
  isCommitteeMember: boolean;
  isEvcCoordinator: boolean;
  isCompetentAuthority: boolean;
  isSystemAdmin: boolean;
  getWorkspaceHome: (role?: string) => string;
  hasPermission: (permission: string) => boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('reguflow_token'));
  const [activeRole, setActiveRole] = useState<string | null>(localStorage.getItem('reguflow_active_role'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const profile = await api.getMe();
          setUser(profile);
          if (!activeRole && profile.roles.length > 0) {
            setActiveRole(profile.roles[0]);
            localStorage.setItem('reguflow_active_role', profile.roles[0]);
          }
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    }
    loadUser();
  }, [token]);

  const login = async (email: string, password = 'Password123!'): Promise<User> => {
    setIsLoading(true);
    try {
      // Clear any stale cached queries from a prior session/persona
      queryClient.clear();
      const res = await api.login(email, password);
      localStorage.setItem('reguflow_token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      const initialRole = res.user.roles[0] || 'GUEST';
      setActiveRole(initialRole);
      localStorage.setItem('reguflow_active_role', initialRole);
      return res.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore network errors on logout
    } finally {
      // Invalidate and clear all cached queries
      queryClient.clear();
      localStorage.removeItem('reguflow_token');
      localStorage.removeItem('reguflow_active_role');
      setToken(null);
      setUser(null);
      setActiveRole(null);
    }
  };

  const switchActiveRole = async (role: string) => {
    if (user?.roles.includes(role)) {
      try {
        queryClient.clear();
        const updated = await api.switchActiveRole(role);
        setUser(updated);
        setActiveRole(role);
        localStorage.setItem('reguflow_active_role', role);
      } catch (err) {
        console.error('Failed to switch active role:', err);
      }
    }
  };

  const isOfficer = activeRole
    ? ['REGIONAL_OFFICER', 'BUREAU_OFFICER', 'COMMITTEE_MEMBER', 'EVC_COORDINATOR', 'COMPETENT_AUTHORITY', 'SYSTEM_ADMIN'].includes(activeRole)
    : false;

  const isInstitutionUser = activeRole
    ? ['INSTITUTION_ADMIN', 'COMPLIANCE_OFFICER'].includes(activeRole)
    : false;

  const isInstitutionAdmin = activeRole === 'INSTITUTION_ADMIN';
  const isComplianceOfficer = activeRole === 'COMPLIANCE_OFFICER';
  const isRegionalOfficer = activeRole === 'REGIONAL_OFFICER';
  const isBureauOfficer = activeRole === 'BUREAU_OFFICER';
  const isCommitteeMember = activeRole === 'COMMITTEE_MEMBER';
  const isEvcCoordinator = activeRole === 'EVC_COORDINATOR';
  const isCompetentAuthority = activeRole === 'COMPETENT_AUTHORITY';
  const isSystemAdmin = activeRole === 'SYSTEM_ADMIN';

  const getWorkspaceHome = (role?: string): string => {
    const target = role || activeRole;
    switch (target) {
      case 'INSTITUTION_ADMIN':
        return '/institution/dashboard';
      case 'COMPLIANCE_OFFICER':
        return '/institution/compliance-workspace';
      case 'REGIONAL_OFFICER':
        return '/officer/regional-workspace';
      case 'BUREAU_OFFICER':
        return '/officer/bureau-workspace';
      case 'COMMITTEE_MEMBER':
        return '/officer/committee-workspace';
      case 'EVC_COORDINATOR':
        return '/officer/evc-workspace';
      case 'COMPETENT_AUTHORITY':
        return '/officer/authority-workspace';
      case 'SYSTEM_ADMIN':
        return '/officer/admin-workspace';
      default:
        return isOfficer ? '/officer/dashboard' : '/institution/dashboard';
    }
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activeRole,
        login,
        logout,
        switchActiveRole,
        isInstitutionUser,
        isOfficer,
        isInstitutionAdmin,
        isComplianceOfficer,
        isRegionalOfficer,
        isBureauOfficer,
        isCommitteeMember,
        isEvcCoordinator,
        isCompetentAuthority,
        isSystemAdmin,
        getWorkspaceHome,
        hasPermission,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
