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
    default: 'border-brand-border bg-white',
    teal: 'border-teal-200 bg-teal-50/40 text-brand-teal',
    amber: 'border-amber-200 bg-amber-50/40 text-[#C5892B]',
    red: 'border-red-200 bg-red-50/40 text-[#B9474F]',
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
