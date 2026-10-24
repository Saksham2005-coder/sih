import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Clock, CheckSquare, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../../api/client';
import { Application, ComplianceUndertaking, DocumentRecord } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';

export const ActionCentre: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [undertakings, setUndertakings] = useState<ComplianceUndertaking[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [apps, under, docs] = await Promise.all([
          api.getApplications(),
          api.getUndertakings(),
          api.getDocuments(),
        ]);
        setApplications(apps.filter(a => a.current_stage === 'DEFICIENCY_COMMUNICATED' || a.open_deficiencies_count > 0));
        setUndertakings(under.filter(u => u.status === 'OVERDUE' || u.status === 'DUE_SOON'));
        setDocuments(docs.filter(d => d.status === 'EXPIRING_SOON' || d.status === 'EXPIRED'));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalActions = applications.length + undertakings.length + documents.length;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-brand-ink">Institutional Action Centre</h1>
          {totalActions > 0 && (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-[#C5892B] border border-amber-300">
              {totalActions} Required Actions
            </span>
          )}
        </div>
        <p className="text-xs text-brand-muted mt-0.5">
          Consolidated statutory obligations requiring immediate institutional response
        </p>
      </div>

      {totalActions === 0 ? (
        <div className="bg-white rounded-xl border border-brand-border p-12 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-teal-50 text-brand-teal flex items-center justify-center mx-auto mb-3">
            <CheckSquare className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-brand-ink">All Actions Clear</h3>
          <p className="text-xs text-brand-muted mt-1">
            There are no pending deficiency cures, overdue undertakings, or expiring statutory documents.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Applications Requiring Deficiency Cure */}
          {applications.length > 0 && (
            <div className="bg-white rounded-xl border border-brand-border shadow-sm p-6">
              <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-[#C5892B]" />
                Application Deficiency Cures ({applications.length})
              </h3>
              <div className="divide-y divide-gray-100">
                {applications.map(app => (
                  <div key={app.id} className="py-3 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs font-bold text-brand-ink">{app.application_number}</p>
                      <p className="text-[11px] text-brand-muted">
                        {app.open_deficiencies_count} itemized deficiencies communicated. Cure and resubmission required.
                      </p>
                    </div>
                    <Link
                      to={`/institution/applications/${app.id}`}
                      className="px-3 py-1.5 rounded-lg bg-[#C5892B] text-white text-xs font-semibold hover:bg-amber-700 inline-flex items-center gap-1 shrink-0"
                    >
                      Cure & Resubmit <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Time-Bound Undertakings Requiring Evidence */}
          {undertakings.length > 0 && (
            <div className="bg-white rounded-xl border border-brand-border shadow-sm p-6">
              <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-brand-teal" />
                Time-Bound Undertakings ({undertakings.length})
              </h3>
              <div className="divide-y divide-gray-100">
                {undertakings.map(u => (
                  <div key={u.id} className="py-3 flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-bold text-brand-ink">{u.title}</p>
                        <StatusBadge status={u.status} />
                      </div>
                      <p className="text-[11px] text-brand-muted mt-0.5">
                        Due: {new Date(u.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </p>
                    </div>
                    <Link
                      to="/institution/compliance"
                      className="px-3 py-1.5 rounded-lg bg-brand-teal text-white text-xs font-semibold hover:bg-brand-teal-dark inline-flex items-center gap-1 shrink-0"
                    >
                      Upload Evidence <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Expiring Documents Requiring Renewal */}
          {documents.length > 0 && (
            <div className="bg-white rounded-xl border border-brand-border shadow-sm p-6">
              <h3 className="text-sm font-bold text-brand-ink flex items-center gap-2 mb-3">
                <ShieldAlert className="w-4 h-4 text-[#B9474F]" />
                Prescribed Document Renewals ({documents.length})
              </h3>
              <div className="divide-y divide-gray-100">
                {documents.map(d => (
                  <div key={d.id} className="py-3 flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-bold text-brand-ink">{d.title}</p>
                        <StatusBadge status={d.status} />
                      </div>
                      <p className="text-[11px] text-brand-muted mt-0.5">
                        Expiry Date: {d.expiry_date ? new Date(d.expiry_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Expired'}
                      </p>
                    </div>
                    <Link
                      to="/institution/documents"
                      className="px-3 py-1.5 rounded-lg border border-brand-teal text-brand-teal text-xs font-semibold hover:bg-teal-50 inline-flex items-center gap-1 shrink-0"
                    >
                      Submit Renewal <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
