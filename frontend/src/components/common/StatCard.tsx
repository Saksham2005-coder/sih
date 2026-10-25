import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'teal' | 'amber' | 'red';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  variant = 'default',
  onClick,
}) => {
  const variantStyles = {
    default: 'border-brand-border bg-white dark:bg-brand-surface text-brand-ink',
    teal: 'border-teal-300 dark:border-teal-700/80 bg-white dark:bg-brand-surface text-brand-ink',
    amber: 'border-amber-300 dark:border-amber-700/80 bg-white dark:bg-brand-surface text-brand-ink',
    red: 'border-red-300 dark:border-red-700/80 bg-white dark:bg-brand-surface text-brand-ink',
  };

  const iconColors = {
    default: 'text-brand-muted',
    teal: 'text-brand-teal dark:text-teal-400',
    amber: 'text-[#99630D] dark:text-amber-400',
    red: 'text-[#B42332] dark:text-red-400',
  };

  return (
    <div
      onClick={onClick}
      className={`rounded-xl border p-5 shadow-sm transition-all duration-150 ${variantStyles[variant]} ${
        onClick
          ? 'cursor-pointer hover:shadow-md hover:border-brand-teal hover:-translate-y-0.5'
          : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-muted">{title}</p>
        {icon && <div className={iconColors[variant]}>{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-brand-ink">{value}</span>
      </div>
      {subtext && <p className="mt-1 text-xs text-brand-muted">{subtext}</p>}
    </div>
  );
};

export default StatCard;
