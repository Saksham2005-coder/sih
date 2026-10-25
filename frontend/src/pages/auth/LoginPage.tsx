import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck, Building2, ArrowRight, Lock, Mail,
  UserCheck, Sparkles, CheckCircle2, ChevronDown, KeyRound, AlertCircle
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { ThemeToggle } from '../../components/common/ThemeToggle';

type PortalType = 'institution' | 'officer';

interface DemoUserItem {
  email: string;
  full_name: string;
  roles: string[];
  institution_name?: string | null;
  region?: string | null;
  default_password?: string;
}

export const LoginPage: React.FC = () => {
  const { login, getWorkspaceHome } = useAuth();
  const navigate = useNavigate();

  // Portal selection: 'institution' or 'officer'
  const [portalType, setPortalType] = useState<PortalType>('institution');

  // Input states
  const [email, setEmail] = useState('admin@apex.edu.in');
  const [password, setPassword] = useState('Password123!');
  const [demoUsers, setDemoUsers] = useState<DemoUserItem[]>([]);
  const [selectedPersonaEmail, setSelectedPersonaEmail] = useState<string>('admin@apex.edu.in');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Load available demo personas
  useEffect(() => {
    async function loadDemos() {
      try {
        const res = await api.getDemoUsers();
        if (res && res.demo_users) {
          // Filter out suspended test accounts
          const activeUsers = res.demo_users.filter((u: DemoUserItem) => u.roles && u.roles.length > 0);
          setDemoUsers(activeUsers);
        }
      } catch {
        // Fallback demo users if offline
        setDemoUsers([
          {
            email: 'admin@apex.edu.in',
            full_name: 'Dr. Arvind Kulkarni',
            roles: ['INSTITUTION_ADMIN'],
            institution_name: 'Apex Institute of Technology & Management',
            region: 'Western',
            default_password: 'Password123!',
          },
          {
            email: 'ro.western@aicte.gov.in',
            full_name: 'Shri Suresh Deshmukh',
            roles: ['REGIONAL_OFFICER'],
            region: 'Western',
            default_password: 'Password123!',
          },
        ]);
      }
    }
    loadDemos();
  }, []);

  // Filter personas based on selected portal type
  const institutionPersonas = demoUsers.filter((u) =>
    u.roles.some((r) => ['INSTITUTION_ADMIN', 'COMPLIANCE_OFFICER'].includes(r))
  );

  const officerPersonas = demoUsers.filter((u) =>
    u.roles.some((r) =>
      ['REGIONAL_OFFICER', 'BUREAU_OFFICER', 'COMMITTEE_MEMBER', 'EVC_COORDINATOR', 'COMPETENT_AUTHORITY', 'SYSTEM_ADMIN'].includes(r)
    )
  );

  const currentPersonaList = portalType === 'institution' ? institutionPersonas : officerPersonas;

  // When portal type changes, switch default persona and email
  const handlePortalSwitch = (type: PortalType) => {
    setPortalType(type);
    setError(null);
    const targetList = type === 'institution' ? institutionPersonas : officerPersonas;
    if (targetList.length > 0) {
      const defaultUser = targetList[0];
      setSelectedPersonaEmail(defaultUser.email);
      setEmail(defaultUser.email);
      setPassword(defaultUser.default_password || 'Password123!');
    }
  };

  // When persona is picked from dropdown
  const handlePersonaSelect = (selectedEmail: string) => {
    setSelectedPersonaEmail(selectedEmail);
    const userObj = demoUsers.find((u) => u.email === selectedEmail);
    if (userObj) {
      setEmail(userObj.email);
      setPassword(userObj.default_password || 'Password123!');
      setError(null);
    }
  };

  const currentSelectedUser = demoUsers.find((u) => u.email === selectedPersonaEmail);

  const executeLogin = async (targetEmail: string, targetPass: string) => {
    setError(null);
    setLoading(true);
    try {
      const loggedInUser = await login(targetEmail, targetPass);
      const destination = getWorkspaceHome(loggedInUser?.roles?.[0]);
      navigate(destination);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeLogin(email, password);
  };

  const handleInstantPersonaLogin = () => {
    if (currentSelectedUser) {
      executeLogin(currentSelectedUser.email, currentSelectedUser.default_password || 'Password123!');
    }
  };

  return (
    <div className="relative min-h-screen bg-brand-porcelain flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 transition-colors">
      {/* Top Right Accessible One-Click Theme Switcher */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle showLabel className="shadow-sm" />
      </div>

      {/* Top Header Branding */}
      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-ink text-brand-teal shadow-xl mb-3 border border-gray-700/50">
          <span className="text-3xl font-extrabold tracking-tight">R</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-brand-ink">
          ReguFlow 360
        </h1>
        <p className="mt-1 text-xs text-brand-muted max-w-md mx-auto">
          AICTE Integrated Approval Workflow, Compliance Monitoring & Escalation Engine
        </p>
        <div className="mt-2.5 flex items-center justify-center gap-2">
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-bold bg-brand-teal-light text-brand-teal border border-teal-200 dark:border-teal-800">
            <CheckCircle2 className="w-3 h-3" /> SIH 2026 Problem Statement 26262
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
            Academic Year 2026-2027
          </span>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white dark:bg-brand-surface py-8 px-6 shadow-2xl rounded-2xl border border-brand-border sm:px-10 transition-colors">

          {/* TWO OPTIONS: INSTITUTION PORTAL vs AICTE OFFICERS PORTAL */}
          <div className="mb-6">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-brand-muted mb-2 text-center">
              Select Your Access Portal
            </label>
            <div className="grid grid-cols-2 gap-3 p-1.5 bg-brand-porcelain dark:bg-brand-surface-secondary rounded-xl border border-brand-border">
              {/* Option 1: Institution Portal */}
              <button
                type="button"
                id="tab-institution"
                onClick={() => handlePortalSwitch('institution')}
                className={`flex flex-col items-center justify-center py-3 px-3 rounded-lg text-xs font-bold transition-all ${
                  portalType === 'institution'
                    ? 'bg-brand-teal text-white shadow-md'
                    : 'text-brand-muted hover:text-brand-ink hover:bg-white/80 dark:hover:bg-brand-surface-elevated'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4" />
                  <span>Institution Portal</span>
                </div>
                <span className={`text-[10px] font-normal mt-0.5 ${portalType === 'institution' ? 'text-teal-100' : 'text-gray-400'}`}>
                  Universities & Colleges
                </span>
              </button>

              {/* Option 2: AICTE Officers Portal */}
              <button
                type="button"
                id="tab-officer"
                onClick={() => handlePortalSwitch('officer')}
                className={`flex flex-col items-center justify-center py-3 px-3 rounded-lg text-xs font-bold transition-all ${
                  portalType === 'officer'
                    ? 'bg-brand-ink text-white shadow-md'
                    : 'text-brand-muted hover:text-brand-ink hover:bg-white/80 dark:hover:bg-brand-surface-elevated'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-teal" />
                  <span>AICTE Officers Portal</span>
                </div>
                <span className={`text-[10px] font-normal mt-0.5 ${portalType === 'officer' ? 'text-gray-300' : 'text-gray-400'}`}>
                  RO, Bureau, EVC & Council
                </span>
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-xs text-[#B9474F] dark:text-red-300 font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* PERSONA SELECTOR DROPDOWN */}
          <div className="mb-6 p-4 rounded-xl border border-teal-200/80 dark:border-teal-800/60 bg-teal-50/40 dark:bg-teal-950/20">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-brand-ink flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-brand-teal" />
                Select Persona (Pre-Configured Demo Roles)
              </label>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-100 dark:bg-teal-950/60 text-brand-teal dark:text-teal-300 border border-teal-200 dark:border-teal-800/60">
                1-Click Ready
              </span>
            </div>

            <div className="relative">
              <select
                id="persona-select"
                value={selectedPersonaEmail}
                onChange={(e) => handlePersonaSelect(e.target.value)}
                className="w-full appearance-none px-3.5 py-2.5 bg-white dark:bg-brand-surface-secondary border border-brand-border rounded-lg text-xs font-semibold text-brand-ink shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal pr-10 cursor-pointer"
              >
                {currentPersonaList.map((u) => {
                  const roleName = u.roles?.[0]?.replace(/_/g, ' ') || 'USER';
                  const contextDetail = u.institution_name || (u.region ? `${u.region} Region` : 'AICTE Headquarters');
                  return (
                    <option key={u.email} value={u.email} className="text-brand-ink bg-white dark:bg-brand-surface py-1">
                      {u.full_name} — {roleName} ({contextDetail})
                    </option>
                  );
                })}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-500 absolute right-3 top-3 pointer-events-none" />
            </div>

            {/* Persona Details & 1-Click Action */}
            {currentSelectedUser && (
              <div className="mt-3 pt-3 border-t border-teal-100 dark:border-teal-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                <div className="text-left">
                  <p className="text-xs font-bold text-brand-ink">
                    {currentSelectedUser.full_name}
                  </p>
                  <p className="text-[11px] text-brand-muted mt-0.5">
                    <span className="font-semibold text-brand-teal">
                      {currentSelectedUser.roles?.[0]?.replace(/_/g, ' ')}
                    </span>
                    {' • '}
                    <span>
                      {currentSelectedUser.institution_name || `${currentSelectedUser.region || 'HQ'} Region`}
                    </span>
                  </p>
                </div>

                <button
                  type="button"
                  id="btn-persona-login"
                  onClick={handleInstantPersonaLogin}
                  disabled={loading}
                  className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-teal hover:bg-brand-teal-dark shadow-sm transition-all shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  {loading ? 'Entering...' : `Enter as ${currentSelectedUser.full_name.split(' ')[0]}`}
                </button>
              </div>
            )}
          </div>

          {/* MANUAL CREDENTIAL FORM */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-bold text-brand-ink uppercase tracking-wider mb-1">
                Official Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setSelectedPersonaEmail(e.target.value);
                  }}
                  placeholder="name@apex.edu.in or officer@aicte.gov.in"
                  className="block w-full pl-9 pr-3 py-2.5 bg-white dark:bg-brand-surface-secondary border border-brand-border rounded-lg text-xs font-medium text-brand-ink shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-brand-ink uppercase tracking-wider mb-1">
                Account Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="block w-full pl-9 pr-3 py-2.5 bg-white dark:bg-brand-surface-secondary border border-brand-border rounded-lg text-xs font-medium text-brand-ink shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-md text-xs font-bold text-white transition-all ${
                portalType === 'institution'
                  ? 'bg-brand-teal hover:bg-brand-teal-dark'
                  : 'bg-brand-ink dark:bg-brand-surface-elevated hover:bg-gray-800 dark:hover:bg-brand-teal border border-transparent dark:border-brand-border'
              }`}
            >
              <KeyRound className="w-4 h-4" />
              {loading ? 'Authenticating Official Session...' : `Sign In to ${portalType === 'institution' ? 'Institution Portal' : 'AICTE Officer Command Centre'}`}
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          </form>

          {/* Footer Security Note */}
          <div className="mt-6 pt-5 border-t border-brand-border text-center">
            <p className="text-[11px] text-brand-muted">
              Role-Scoped & Multi-Tenant Isolated • 256-Bit SHA Hashing • Immutable Audit Logging
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
