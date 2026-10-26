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
    default: 'border-brand-border bg-brand-surface text-brand-text-primary',
    teal: 'border-brand-teal/40 bg-brand-surface text-brand-text-primary',
    amber: 'border-amber-300 dark:border-[#5C4520] bg-brand-surface text-brand-text-primary',
    red: 'border-red-300 dark:border-[#64313B] bg-brand-surface text-brand-text-primary',
  };

  const iconColors = {
    default: 'text-brand-text-muted',
    teal: 'text-brand-teal',
    amber: 'text-[#99630D] dark:text-[#F2C96D]',
    red: 'text-[#B42332] dark:text-[#F58F98]',
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
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-text-muted">{title}</p>
        {icon && <div className={iconColors[variant]}>{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-brand-text-primary">{value}</span>
      </div>
      {subtext && <p className="mt-1 text-xs text-brand-text-secondary">{subtext}</p>}
    </div>
  );
};

export default StatCard;
