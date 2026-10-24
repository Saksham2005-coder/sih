import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, FileText, ArrowRight } from 'lucide-react';
import { api } from '../../api/client';
import { Application } from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';
import { PriorityGauge } from '../../components/common/PriorityGauge';

export const ApplicationRegistry: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('');

  const loadApps = async () => {
    try {
      const data = await api.getApplications({
        stage: stageFilter || undefined,
        search: search || undefined,
      });
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApps();
  }, [stageFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadApps();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-brand-ink">National Application Registry</h1>
        <p className="text-xs text-brand-muted mt-0.5">
          Central regulatory docket across regional offices, scrutiny queues, and statutory committees
        </p>
      </div>

      {/* Filter and Search */}
      <div className="bg-white p-4 rounded-xl border border-brand-border shadow-sm flex flex-col sm:flex-row gap-3 justify-between items-center">
        <form onSubmit={handleSearch} className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-brand-muted" />
          <input
            type="text"
            placeholder="Search by app # or institution..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 border border-brand-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-brand-teal"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-brand-muted shrink-0" />
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="border border-brand-border rounded-lg px-2.5 py-1.5 text-xs text-brand-ink focus:outline-none focus:ring-1 focus:ring-brand-teal w-full sm:w-auto"
          >
            <option value="">All Stages</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="UNDER_SCRUTINY">Under Scrutiny</option>
            <option value="DEFICIENCY_COMMUNICATED">Deficiency Cure Required</option>
            <option value="RESUBMITTED">Resubmitted</option>
            <option value="SCRUTINY_COMPLETED">Scrutiny Completed</option>
            <option value="AWAITING_EVC_SCHEDULE">Awaiting EVC</option>
            <option value="EVC_SCHEDULED">EVC Scheduled</option>
            <option value="EVC_COMPLETED">EVC Completed</option>
            <option value="AWAITING_SAC_CAC_REVIEW">Committee Review</option>
            <option value="AWAITING_COMPETENT_AUTHORITY">Apex Action</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-xl border border-brand-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Application Number</th>
                <th className="px-6 py-3.5">Institution & Region</th>
                <th className="px-6 py-3.5">Type</th>
                <th className="px-6 py-3.5">Stage</th>
                <th className="px-6 py-3.5">Priority Urgency</th>
                <th className="px-6 py-3.5">Deficiencies</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-brand-muted">
                    No matching applications found in registry.
                  </td>
                </tr>
              ) : (
                applications.map((app) => (
                  <tr key={app.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-bold text-brand-ink">
                      {app.application_number}
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-brand-ink">{app.institution_name}</p>
                      <p className="text-[11px] text-brand-muted">{app.region} Region</p>
                    </td>
                    <td className="px-6 py-4 text-brand-muted">
                      {app.application_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.current_stage} />
                    </td>
                    <td className="px-6 py-4">
                      <PriorityGauge score={app.priority_score} factors={app.priority_factors} />
                    </td>
                    <td className="px-6 py-4">
                      {app.open_deficiencies_count > 0 ? (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-[#C5892B] border border-amber-300">
                          {app.open_deficiencies_count} Open
                        </span>
                      ) : (
                        <span className="text-teal-700 text-xs font-medium">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/officer/applications/${app.id}`}
                        className="px-3 py-1.5 rounded-lg bg-brand-teal text-white text-xs font-semibold hover:bg-brand-teal-dark shadow-sm inline-flex items-center gap-1"
                      >
                        Scrutiny Console <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
