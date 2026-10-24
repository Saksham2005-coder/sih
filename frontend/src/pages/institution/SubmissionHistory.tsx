import React, { useEffect, useState } from 'react';
import { History, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../../api/client';
import { Application } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';

export const SubmissionHistory: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const apps = await api.getApplications();
        setApplications(apps);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-brand-ink">Statutory Submission History</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Immutable audit record of all applications, deficiency cures, and regulatory approvals
        </p>
      </div>

      <div className="bg-white rounded-xl border border-brand-border shadow-sm p-6 space-y-6">
        {applications.map((app) => (
          <div key={app.id} className="border-b border-brand-border pb-6 last:border-none last:pb-0">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
              <div>
                <span className="font-bold text-sm text-brand-ink">{app.application_number}</span>
                <span className="text-xs text-brand-muted ml-2">({app.application_type.replace(/_/g, ' ')})</span>
              </div>
              <StatusBadge status={app.current_stage} />
            </div>

            <p className="text-xs text-brand-muted mb-2">
              Submitted on: {new Date(app.submitted_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
            </p>

            {app.approved_at && (
              <p className="text-xs text-teal-800 font-semibold flex items-center gap-1.5 mt-1">
                <CheckCircle2 className="w-4 h-4 text-brand-teal" /> Final Statutory Approval Granted on{' '}
                {new Date(app.approved_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
