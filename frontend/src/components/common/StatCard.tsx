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
    teal: 'border-teal-200 dark:border-teal-800/60 bg-teal-50/40 dark:bg-teal-950/25 text-brand-teal dark:text-teal-300',
    amber: 'border-amber-200 dark:border-amber-800/60 bg-amber-50/40 dark:bg-amber-950/25 text-[#C5892B] dark:text-amber-300',
    red: 'border-red-200 dark:border-red-800/60 bg-red-50/40 dark:bg-red-950/25 text-[#B9474F] dark:text-red-300',
  };

  return (
    <div
      onClick={onClick}
      className={`rounded-lg border p-5 transition-all shadow-sm ${
        variantStyles[variant]
      } ${onClick ? 'cursor-pointer hover:shadow-md hover:border-brand-teal' : ''}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-muted">{title}</p>
        {icon && <div className="text-brand-muted">{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-brand-ink">{value}</span>
      </div>
      {subtext && <p className="mt-1 text-xs text-brand-muted">{subtext}</p>}
    </div>
  );
};

export default StatCard;
