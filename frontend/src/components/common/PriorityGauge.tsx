import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

interface PriorityGaugeProps {
  score: number;
  factors?: {
    tier?: string;
    factors?: string[];
  } | null;
}

export const PriorityGauge: React.FC<PriorityGaugeProps> = ({ score, factors }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Semantic Urgency Mapping:
  // Low (<40): Calm Teal | Medium (40-59): Amber | High (60-79): Orange | Critical (>=80): Red
  let tier = factors?.tier || 'Low';
  let colorClass = 'bg-teal-50 dark:bg-teal-950/70 text-teal-800 dark:text-teal-200 border-teal-300 dark:border-teal-700/80';
  let barColor = 'bg-teal-600 dark:bg-teal-400';

  if (score >= 80) {
    tier = 'Critical';
    colorClass = 'bg-red-50 dark:bg-red-950/70 text-red-800 dark:text-red-200 border-red-300 dark:border-red-700/80';
    barColor = 'bg-red-600 dark:bg-red-500';
  } else if (score >= 60) {
    tier = 'High';
    colorClass = 'bg-orange-50 dark:bg-orange-950/70 text-orange-900 dark:text-orange-200 border-orange-300 dark:border-orange-700/80';
    barColor = 'bg-orange-600 dark:bg-orange-500';
  } else if (score >= 40) {
    tier = 'Medium';
    colorClass = 'bg-amber-50 dark:bg-amber-950/70 text-amber-900 dark:text-amber-200 border-amber-300 dark:border-amber-700/80';
    barColor = 'bg-amber-600 dark:bg-amber-500';
  }

  return (
    <div className="relative inline-flex items-center gap-2">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5">
          <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colorClass} transition-colors shadow-xs`}>
            {score}/100 • {tier}
          </span>
          <button
            type="button"
            onClick={() => setShowTooltip(!showTooltip)}
            className="text-brand-muted hover:text-brand-ink transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-teal rounded"
            title="Explain Priority Factors"
            aria-label="Explain Priority Factors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden" role="progressbar" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100}>
          <div className={`h-full ${barColor} transition-all duration-300`} style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
        </div>
      </div>

      {showTooltip && (
        <div className="absolute z-50 left-0 top-8 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl border border-slate-700 animate-fadeIn">
          <div className="flex items-center justify-between pb-1 mb-2 border-b border-slate-800 font-semibold">
            <span>Explainable Priority Factors</span>
            <button onClick={() => setShowTooltip(false)} className="text-slate-400 hover:text-white p-0.5" aria-label="Close tooltip">✕</button>
          </div>
          {factors?.factors && factors.factors.length > 0 ? (
            <ul className="space-y-1 text-slate-300">
              {factors.factors.map((f, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-teal-400 shrink-0">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400">Standard operational queue priority baseline (score {score}).</p>
          )}
        </div>
      )}
    </div>
  );
};

export default PriorityGauge;
