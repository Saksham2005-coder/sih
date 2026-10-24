import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight, UserCheck, CheckCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@apex.edu.in');
  const [password, setPassword] = useState('Password123!');
  const [demoUsers, setDemoUsers] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadDemos() {
      try {
        const res = await api.getDemoUsers();
        setDemoUsers(res.demo_users);
      } catch {
        // fallback
      }
    }
    loadDemos();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      // Navigate based on selected role
      if (email.includes('aicte.gov.in')) {
        navigate('/officer/dashboard');
      } else {
        navigate('/institution/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (userEmail: string) => {
    setEmail(userEmail);
    setError(null);
    setLoading(true);
    try {
      await login(userEmail, 'Password123!');
      if (userEmail.includes('aicte.gov.in')) {
        navigate('/officer/dashboard');
      } else {
        navigate('/institution/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-porcelain flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-12 h-12 rounded-xl bg-brand-ink flex items-center justify-center shadow-lg mb-4">
          <span className="text-2xl font-bold text-brand-teal">R</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-brand-ink">ReguFlow 360</h2>
        <p className="mt-1 text-xs text-brand-muted">
          Integrated AICTE Approval Workflow, Compliance & Alert System
        </p>
        <span className="inline-block mt-2 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-brand-teal-light text-brand-teal border border-teal-200">
          SIH 2026 Problem Statement 26262
        </span>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-white py-8 px-6 shadow-xl rounded-xl border border-brand-border sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-[#B9474F] font-medium">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-brand-ink uppercase tracking-wider">
                Official Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-lg text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-brand-ink uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-brand-border rounded-lg text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-brand-teal"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-brand-teal hover:bg-brand-teal-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-teal transition-colors"
            >
              {loading ? 'Authenticating...' : 'Sign In to Portal'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Switcher */}
          <div className="mt-8 pt-6 border-t border-brand-border">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-ink flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-brand-teal" />
                1-Click Demo Persona Entry
              </span>
              <span className="text-[11px] text-brand-muted">Dev Credentials</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
              {demoUsers.map((u) => (
                <button
                  key={u.email}
                  type="button"
                  onClick={() => handleQuickDemoLogin(u.email)}
                  className="p-2.5 rounded-lg border border-brand-border hover:border-brand-teal hover:bg-teal-50/50 transition-all text-left flex flex-col justify-between"
                >
                  <div>
                    <p className="text-xs font-semibold text-brand-ink line-clamp-1">{u.full_name}</p>
                    <p className="text-[11px] text-brand-teal font-medium mt-0.5">
                      {u.roles[0]?.replace(/_/g, ' ')}
                    </p>
                  </div>
                  <span className="text-[10px] text-brand-muted mt-1">{u.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
