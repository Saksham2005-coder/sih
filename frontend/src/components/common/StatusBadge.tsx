import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const configs: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    // Application Stages
    SUBMITTED: {
      bg: 'bg-blue-50 border-blue-200 dark:bg-blue-950/80 dark:border-blue-700/80',
      text: 'text-blue-800 dark:text-blue-200',
      dot: 'bg-blue-600 dark:bg-blue-400',
      label: 'Submitted'
    },
    UNDER_SCRUTINY: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-sky-950/80 dark:border-sky-700/80',
      text: 'text-sky-900 dark:text-sky-200',
      dot: 'bg-sky-600 dark:bg-sky-400',
      label: 'Under Scrutiny'
    },
    DEFICIENCY_COMMUNICATED: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-amber-950/80 dark:border-amber-700/80',
      text: 'text-[#99630D] dark:text-amber-200',
      dot: 'bg-[#99630D] dark:bg-amber-400',
      label: 'Deficiency Cure Required'
    },
    RESUBMITTED: {
      bg: 'bg-indigo-50 border-indigo-200 dark:bg-indigo-950/80 dark:border-indigo-700/80',
      text: 'text-indigo-800 dark:text-indigo-200',
      dot: 'bg-indigo-600 dark:bg-indigo-400',
      label: 'Resubmitted'
    },
    SCRUTINY_COMPLETED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-teal-950/80 dark:border-teal-700/80',
      text: 'text-[#0E746B] dark:text-teal-200',
      dot: 'bg-[#0E746B] dark:bg-teal-400',
      label: 'Scrutiny Completed'
    },
    AWAITING_EVC_SCHEDULE: {
      bg: 'bg-purple-50 border-purple-200 dark:bg-purple-950/80 dark:border-purple-700/80',
      text: 'text-purple-800 dark:text-purple-200',
      dot: 'bg-purple-600 dark:bg-purple-400',
      label: 'Awaiting EVC'
    },
    EVC_SCHEDULED: {
      bg: 'bg-purple-50 border-purple-200 dark:bg-purple-950/80 dark:border-purple-700/80',
      text: 'text-purple-900 dark:text-purple-200',
      dot: 'bg-purple-600 dark:bg-purple-400',
      label: 'EVC Scheduled'
    },
    EVC_COMPLETED: {
      bg: 'bg-violet-50 border-violet-200 dark:bg-violet-950/80 dark:border-violet-700/80',
      text: 'text-violet-800 dark:text-violet-200',
      dot: 'bg-violet-600 dark:bg-violet-400',
      label: 'EVC Completed'
    },
    AWAITING_SAC_CAC_REVIEW: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-amber-950/80 dark:border-amber-700/80',
      text: 'text-amber-900 dark:text-amber-200',
      dot: 'bg-amber-600 dark:bg-amber-400',
      label: 'Committee Review'
    },
    AWAITING_COMPETENT_AUTHORITY: {
      bg: 'bg-orange-50 border-orange-300 dark:bg-orange-950/80 dark:border-orange-700/80',
      text: 'text-orange-900 dark:text-orange-200',
      dot: 'bg-orange-600 dark:bg-orange-400',
      label: 'Apex Concurrence'
    },
    APPROVED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-teal-950/80 dark:border-teal-700/80',
      text: 'text-[#0E746B] dark:text-teal-200',
      dot: 'bg-[#0E746B] dark:bg-teal-400',
      label: 'Approved'
    },
    REJECTED: {
      bg: 'bg-red-50 border-red-200 dark:bg-red-950/80 dark:border-red-700/80',
      text: 'text-[#B42332] dark:text-red-200',
      dot: 'bg-[#B42332] dark:bg-red-400',
      label: 'Rejected'
    },
    CLOSED: {
      bg: 'bg-gray-100 border-gray-200 dark:bg-gray-800/80 dark:border-gray-700',
      text: 'text-gray-800 dark:text-gray-200',
      dot: 'bg-gray-500 dark:bg-gray-400',
      label: 'Closed'
    },

    // Compliance Undertakings
    NOT_YET_DUE: {
      bg: 'bg-gray-50 border-gray-200 dark:bg-gray-800/70 dark:border-gray-700',
      text: 'text-gray-800 dark:text-gray-200',
      dot: 'bg-gray-400 dark:bg-gray-400',
      label: 'Not Yet Due'
    },
    DUE_SOON: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-amber-950/80 dark:border-amber-700/80',
      text: 'text-[#99630D] dark:text-amber-200',
      dot: 'bg-[#99630D] dark:bg-amber-400',
      label: 'Due Soon'
    },
    PENDING_VERIFICATION: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-sky-950/80 dark:border-sky-700/80',
      text: 'text-sky-800 dark:text-sky-200',
      dot: 'bg-sky-500 dark:bg-sky-400',
      label: 'Pending Verification'
    },
    VERIFIED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-teal-950/80 dark:border-teal-700/80',
      text: 'text-[#0E746B] dark:text-teal-200',
      dot: 'bg-[#0E746B] dark:bg-teal-400',
      label: 'Verified'
    },
    OVERDUE: {
      bg: 'bg-red-50 border-red-200 dark:bg-red-950/80 dark:border-red-700/80',
      text: 'text-[#B42332] dark:text-red-200',
      dot: 'bg-[#B42332] dark:bg-red-400',
      label: 'Overdue'
    },

    // Documents
    ACTIVE: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-teal-950/80 dark:border-teal-700/80',
      text: 'text-[#0E746B] dark:text-teal-200',
      dot: 'bg-[#0E746B] dark:bg-teal-400',
      label: 'Active & Valid'
    },
    EXPIRING_SOON: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-amber-950/80 dark:border-amber-700/80',
      text: 'text-[#99630D] dark:text-amber-200',
      dot: 'bg-[#99630D] dark:bg-amber-400',
      label: 'Expiring Soon'
    },
    RENEWAL_SUBMITTED: {
      bg: 'bg-blue-50 border-blue-200 dark:bg-blue-950/80 dark:border-blue-700/80',
      text: 'text-blue-800 dark:text-blue-200',
      dot: 'bg-blue-600 dark:bg-blue-400',
      label: 'Renewal Submitted'
    },
    EXPIRED: {
      bg: 'bg-red-50 border-red-200 dark:bg-red-950/80 dark:border-red-700/80',
      text: 'text-[#B42332] dark:text-red-200',
      dot: 'bg-[#B42332] dark:bg-red-400',
      label: 'Expired'
    },

    // Deficiencies
    OPEN: {
      bg: 'bg-red-50 border-red-200 dark:bg-red-950/80 dark:border-red-700/80',
      text: 'text-[#B42332] dark:text-red-200',
      dot: 'bg-[#B42332] dark:bg-red-400',
      label: 'Open Deficiency'
    },
    CURED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-teal-950/80 dark:border-teal-700/80',
      text: 'text-[#0E746B] dark:text-teal-200',
      dot: 'bg-[#0E746B] dark:bg-teal-400',
      label: 'Cured & Resolved'
    },
  };

  const normalized = status.toUpperCase();
  const cfg = configs[normalized] || {
    bg: 'bg-gray-100 border-gray-200 dark:bg-gray-800/80 dark:border-gray-700',
    text: 'text-gray-800 dark:text-gray-200',
    dot: 'bg-gray-500 dark:bg-gray-400',
    label: status.replace(/_/g, ' '),
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.text} ${className} transition-colors select-none`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
      <span>{cfg.label}</span>
    </span>
  );
};

export default StatusBadge;
