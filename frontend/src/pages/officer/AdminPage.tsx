import React, { useEffect, useState } from 'react';
import { Users, Server, CheckCircle2, Shield, Database } from 'lucide-react';
import { api } from '../../api/client';

export const AdminPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [demoUsers, setDemoUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAdminData() {
      try {
        const [h, u] = await Promise.all([
          api.getHealth(),
          api.getDemoUsers(),
        ]);
        setHealth(h);
        setDemoUsers(u.demo_users);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadAdminData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-brand-ink">System Administration & RBAC Management</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Platform health diagnostics, tenant boundaries, and authorized role assignments
        </p>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-xl border border-brand-border p-6 shadow-sm">
        <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2 pb-3 border-b border-brand-border mb-4">
          <Server className="w-4 h-4 text-brand-teal" /> Platform Diagnostics & Health
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">API Core:</span>
            <p className="font-bold text-teal-800 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> {health?.status || 'Online'}
            </p>
          </div>
          <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Database Engine:</span>
            <p className="font-bold text-teal-800 flex items-center gap-1 mt-0.5">
              <Database className="w-3.5 h-3.5 text-brand-teal" /> {health?.database || 'Healthy'}
            </p>
          </div>
          <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Academic Cycle:</span>
            <p className="font-bold text-brand-ink mt-0.5">{health?.academic_cycle || '2026-2027'}</p>
          </div>
          <div className="p-3 bg-brand-porcelain/50 rounded-lg border border-brand-border">
            <span className="text-brand-muted text-[10px] uppercase font-semibold">Version:</span>
            <p className="font-bold text-brand-ink mt-0.5">v{health?.version || '1.0.0'}</p>
          </div>
        </div>
      </div>

      {/* Users & Personas */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border">
          <h3 className="text-sm font-bold text-brand-ink">Configured User Accounts & Workspaces</h3>
          <p className="text-xs text-brand-muted">Demonstration accounts with scoped tenant and role permissions</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Full Name</th>
                <th className="px-6 py-3.5">Email</th>
                <th className="px-6 py-3.5">Assigned Roles</th>
                <th className="px-6 py-3.5">Tenant Scope</th>
                <th className="px-6 py-3.5">Region</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {demoUsers.map((u) => (
                <tr key={u.email} className="hover:bg-gray-50/80">
                  <td className="px-6 py-4 font-bold text-brand-ink">{u.full_name}</td>
                  <td className="px-6 py-4 text-brand-muted">{u.email}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {u.roles.map((r: string) => (
                        <span key={r} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-brand-ink border border-gray-200">
                          {r.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-semibold text-brand-ink">
                    {u.institution_name || 'Apex Regulatory Bureau'}
                  </td>
                  <td className="px-6 py-4 text-brand-muted">{u.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
