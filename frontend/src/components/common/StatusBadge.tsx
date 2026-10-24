import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const configs: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    // Application Stages
    SUBMITTED: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-700', dot: 'bg-blue-600', label: 'Submitted' },
    UNDER_SCRUTINY: { bg: 'bg-sky-50 border-sky-200', text: 'text-sky-800', dot: 'bg-sky-600', label: 'Under Scrutiny' },
    DEFICIENCY_COMMUNICATED: { bg: 'bg-amber-50 border-amber-200', text: 'text-[#C5892B]', dot: 'bg-[#C5892B]', label: 'Deficiency Cure Required' },
    RESUBMITTED: { bg: 'bg-indigo-50 border-indigo-200', text: 'text-indigo-700', dot: 'bg-indigo-600', label: 'Resubmitted' },
    SCRUTINY_COMPLETED: { bg: 'bg-teal-50 border-teal-200', text: 'text-[#0E746B]', dot: 'bg-[#0E746B]', label: 'Scrutiny Completed' },
    AWAITING_EVC_SCHEDULE: { bg: 'bg-purple-50 border-purple-200', text: 'text-purple-700', dot: 'bg-purple-600', label: 'Awaiting EVC' },
    EVC_SCHEDULED: { bg: 'bg-purple-50 border-purple-200', text: 'text-purple-800', dot: 'bg-purple-600', label: 'EVC Scheduled' },
    EVC_COMPLETED: { bg: 'bg-violet-50 border-violet-200', text: 'text-violet-700', dot: 'bg-violet-600', label: 'EVC Completed' },
    AWAITING_SAC_CAC_REVIEW: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-800', dot: 'bg-amber-600', label: 'Committee Review' },
    AWAITING_COMPETENT_AUTHORITY: { bg: 'bg-orange-50 border-orange-200', text: 'text-orange-800', dot: 'bg-orange-600', label: 'Apex Concurrence' },
    APPROVED: { bg: 'bg-teal-50 border-teal-200', text: 'text-[#0E746B]', dot: 'bg-[#0E746B]', label: 'Approved' },
    REJECTED: { bg: 'bg-red-50 border-red-200', text: 'text-[#B9474F]', dot: 'bg-[#B9474F]', label: 'Rejected' },
    CLOSED: { bg: 'bg-gray-100 border-gray-200', text: 'text-gray-700', dot: 'bg-gray-500', label: 'Closed' },

    // Compliance Undertakings
    NOT_YET_DUE: { bg: 'bg-gray-50 border-gray-200', text: 'text-gray-700', dot: 'bg-gray-400', label: 'Not Yet Due' },
    DUE_SOON: { bg: 'bg-amber-50 border-amber-200', text: 'text-[#C5892B]', dot: 'bg-[#C5892B]', label: 'Due Soon' },
    PENDING_VERIFICATION: { bg: 'bg-sky-50 border-sky-200', text: 'text-sky-700', dot: 'bg-sky-500', label: 'Pending Verification' },
    VERIFIED: { bg: 'bg-teal-50 border-teal-200', text: 'text-[#0E746B]', dot: 'bg-[#0E746B]', label: 'Verified' },
    OVERDUE: { bg: 'bg-red-50 border-red-200', text: 'text-[#B9474F]', dot: 'bg-[#B9474F]', label: 'Overdue' },

    // Documents
    ACTIVE: { bg: 'bg-teal-50 border-teal-200', text: 'text-[#0E746B]', dot: 'bg-[#0E746B]', label: 'Active & Valid' },
    EXPIRING_SOON: { bg: 'bg-amber-50 border-amber-200', text: 'text-[#C5892B]', dot: 'bg-[#C5892B]', label: 'Expiring Soon' },
    RENEWAL_SUBMITTED: { bg: 'bg-blue-50 border-blue-200', text: 'text-blue-700', dot: 'bg-blue-600', label: 'Renewal Submitted' },
    EXPIRED: { bg: 'bg-red-50 border-red-200', text: 'text-[#B9474F]', dot: 'bg-[#B9474F]', label: 'Expired' },

    // Deficiencies
    OPEN: { bg: 'bg-red-50 border-red-200', text: 'text-[#B9474F]', dot: 'bg-[#B9474F]', label: 'Open Deficiency' },
    CURED: { bg: 'bg-teal-50 border-teal-200', text: 'text-[#0E746B]', dot: 'bg-[#0E746B]', label: 'Cured & Resolved' },
  };

  const normalized = status.toUpperCase();
  const cfg = configs[normalized] || {
    bg: 'bg-gray-100 border-gray-200',
    text: 'text-gray-700',
    dot: 'bg-gray-500',
    label: status.replace(/_/g, ' '),
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cfg.bg} ${cfg.text} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
};
