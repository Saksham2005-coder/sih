import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const configs: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    // Application Stages
    SUBMITTED: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-[#192F43] dark:border-[#2C4D6B]',
      text: 'text-sky-800 dark:text-[#92C8FA]',
      dot: 'bg-sky-600 dark:bg-[#92C8FA]',
      label: 'Submitted'
    },
    UNDER_SCRUTINY: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-[#192F43] dark:border-[#2C4D6B]',
      text: 'text-sky-900 dark:text-[#92C8FA]',
      dot: 'bg-sky-600 dark:bg-[#92C8FA]',
      label: 'Under Scrutiny'
    },
    DEFICIENCY_COMMUNICATED: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-[#352A18] dark:border-[#5C4520]',
      text: 'text-[#99630D] dark:text-[#F2C96D]',
      dot: 'bg-[#99630D] dark:bg-[#F2C96D]',
      label: 'Deficiency Cure Required'
    },
    RESUBMITTED: {
      bg: 'bg-indigo-50 border-indigo-200 dark:bg-[#1B2942] dark:border-[#2D456E]',
      text: 'text-indigo-800 dark:text-[#A5B4FC]',
      dot: 'bg-indigo-600 dark:bg-[#818CF8]',
      label: 'Resubmitted'
    },
    SCRUTINY_COMPLETED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-[#16372D] dark:border-[#265947]',
      text: 'text-[#0E746B] dark:text-[#79D9AD]',
      dot: 'bg-[#0E746B] dark:bg-[#79D9AD]',
      label: 'Scrutiny Completed'
    },
    AWAITING_EVC_SCHEDULE: {
      bg: 'bg-purple-50 border-purple-200 dark:bg-[#281F3B] dark:border-[#4B3B6E]',
      text: 'text-purple-800 dark:text-[#D8B4FE]',
      dot: 'bg-purple-600 dark:bg-[#C084FC]',
      label: 'Awaiting EVC'
    },
    EVC_SCHEDULED: {
      bg: 'bg-purple-50 border-purple-200 dark:bg-[#281F3B] dark:border-[#4B3B6E]',
      text: 'text-purple-900 dark:text-[#D8B4FE]',
      dot: 'bg-purple-600 dark:bg-[#C084FC]',
      label: 'EVC Scheduled'
    },
    EVC_COMPLETED: {
      bg: 'bg-violet-50 border-violet-200 dark:bg-[#281F3B] dark:border-[#4B3B6E]',
      text: 'text-violet-800 dark:text-[#D8B4FE]',
      dot: 'bg-violet-600 dark:bg-[#C084FC]',
      label: 'EVC Completed'
    },
    AWAITING_SAC_CAC_REVIEW: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-[#352A18] dark:border-[#5C4520]',
      text: 'text-amber-900 dark:text-[#F2C96D]',
      dot: 'bg-amber-600 dark:bg-[#F2C96D]',
      label: 'Committee Review'
    },
    AWAITING_COMPETENT_AUTHORITY: {
      bg: 'bg-orange-50 border-orange-300 dark:bg-[#382218] dark:border-[#663820]',
      text: 'text-orange-900 dark:text-[#FBA871]',
      dot: 'bg-orange-600 dark:bg-[#FA8C4C]',
      label: 'Apex Concurrence'
    },
    APPROVED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-[#16372D] dark:border-[#265947]',
      text: 'text-[#0E746B] dark:text-[#79D9AD]',
      dot: 'bg-[#0E746B] dark:bg-[#79D9AD]',
      label: 'Approved'
    },
    REJECTED: {
      bg: 'bg-red-50 border-red-200 dark:bg-[#3A2027] dark:border-[#64313B]',
      text: 'text-[#B42332] dark:text-[#F58F98]',
      dot: 'bg-[#B42332] dark:bg-[#F58F98]',
      label: 'Rejected'
    },
    CLOSED: {
      bg: 'bg-gray-100 border-gray-200 dark:bg-[#1A2A39] dark:border-[#2D4051]',
      text: 'text-gray-800 dark:text-[#B0BECC]',
      dot: 'bg-gray-500 dark:bg-[#8799AA]',
      label: 'Closed'
    },

    // Compliance Undertakings
    NOT_YET_DUE: {
      bg: 'bg-gray-50 border-gray-200 dark:bg-[#1A2A39] dark:border-[#2D4051]',
      text: 'text-gray-800 dark:text-[#B0BECC]',
      dot: 'bg-gray-400 dark:bg-[#8799AA]',
      label: 'Not Yet Due'
    },
    DUE_SOON: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-[#352A18] dark:border-[#5C4520]',
      text: 'text-[#99630D] dark:text-[#F2C96D]',
      dot: 'bg-[#99630D] dark:bg-[#F2C96D]',
      label: 'Due Soon'
    },
    PENDING_VERIFICATION: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-[#192F43] dark:border-[#2C4D6B]',
      text: 'text-sky-800 dark:text-[#92C8FA]',
      dot: 'bg-sky-500 dark:bg-[#92C8FA]',
      label: 'Pending Verification'
    },
    VERIFIED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-[#16372D] dark:border-[#265947]',
      text: 'text-[#0E746B] dark:text-[#79D9AD]',
      dot: 'bg-[#0E746B] dark:bg-[#79D9AD]',
      label: 'Verified'
    },
    OVERDUE: {
      bg: 'bg-red-50 border-red-200 dark:bg-[#3A2027] dark:border-[#64313B]',
      text: 'text-[#B42332] dark:text-[#F58F98]',
      dot: 'bg-[#B42332] dark:bg-[#F58F98]',
      label: 'Overdue'
    },

    // Documents
    ACTIVE: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-[#16372D] dark:border-[#265947]',
      text: 'text-[#0E746B] dark:text-[#79D9AD]',
      dot: 'bg-[#0E746B] dark:bg-[#79D9AD]',
      label: 'Active & Valid'
    },
    EXPIRING_SOON: {
      bg: 'bg-amber-50 border-amber-300 dark:bg-[#352A18] dark:border-[#5C4520]',
      text: 'text-[#99630D] dark:text-[#F2C96D]',
      dot: 'bg-[#99630D] dark:bg-[#F2C96D]',
      label: 'Expiring Soon'
    },
    RENEWAL_SUBMITTED: {
      bg: 'bg-sky-50 border-sky-200 dark:bg-[#192F43] dark:border-[#2C4D6B]',
      text: 'text-sky-800 dark:text-[#92C8FA]',
      dot: 'bg-sky-600 dark:bg-[#92C8FA]',
      label: 'Renewal Submitted'
    },
    EXPIRED: {
      bg: 'bg-red-50 border-red-200 dark:bg-[#3A2027] dark:border-[#64313B]',
      text: 'text-[#B42332] dark:text-[#F58F98]',
      dot: 'bg-[#B42332] dark:bg-[#F58F98]',
      label: 'Expired'
    },

    // Deficiencies
    OPEN: {
      bg: 'bg-red-50 border-red-200 dark:bg-[#3A2027] dark:border-[#64313B]',
      text: 'text-[#B42332] dark:text-[#F58F98]',
      dot: 'bg-[#B42332] dark:bg-[#F58F98]',
      label: 'Open Deficiency'
    },
    CURED: {
      bg: 'bg-teal-50 border-teal-200 dark:bg-[#16372D] dark:border-[#265947]',
      text: 'text-[#0E746B] dark:text-[#79D9AD]',
      dot: 'bg-[#0E746B] dark:bg-[#79D9AD]',
      label: 'Cured & Resolved'
    },
  };

  const normalized = status.toUpperCase();
  const cfg = configs[normalized] || {
    bg: 'bg-gray-100 border-gray-200 dark:bg-[#1A2A39] dark:border-[#2D4051]',
    text: 'text-gray-800 dark:text-[#B0BECC]',
    dot: 'bg-gray-500 dark:bg-[#8799AA]',
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
