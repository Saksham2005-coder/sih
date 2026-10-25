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

  let tier = factors?.tier || 'Low';
  let colorClass = 'bg-teal-50 dark:bg-teal-950/40 text-brand-teal dark:text-teal-300 border-teal-200 dark:border-teal-800/60';
  let barColor = 'bg-brand-teal dark:bg-teal-400';

  if (score >= 80) {
    tier = 'Critical';
    colorClass = 'bg-red-50 dark:bg-red-950/40 text-[#B9474F] dark:text-red-300 border-red-200 dark:border-red-800/60';
    barColor = 'bg-[#B9474F] dark:bg-red-400';
  } else if (score >= 60) {
    tier = 'High';
    colorClass = 'bg-amber-50 dark:bg-amber-950/40 text-[#C5892B] dark:text-amber-300 border-amber-200 dark:border-amber-800/60';
    barColor = 'bg-[#C5892B] dark:bg-amber-400';
  } else if (score >= 40) {
    tier = 'Medium';
    colorClass = 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800/60';
    barColor = 'bg-blue-600 dark:bg-blue-400';
  }

  return (
    <div className="relative inline-flex items-center gap-2">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5">
          <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colorClass} transition-colors`}>
            {score}/100 • {tier}
          </span>
          <button
            type="button"
            onClick={() => setShowTooltip(!showTooltip)}
            className="text-brand-muted hover:text-brand-ink transition-colors"
            title="Explain Priority Factors"
            aria-label="Explain Priority Factors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div className={`h-full ${barColor}`} style={{ width: `${score}%` }} />
        </div>
      </div>

      {showTooltip && (
        <div className="absolute z-50 left-0 top-8 w-64 p-3 bg-brand-ink text-white text-xs rounded-lg shadow-xl border border-gray-700 dark:border-brand-border animate-fadeIn">
          <div className="flex items-center justify-between pb-1 mb-2 border-b border-gray-700 font-semibold">
            <span>Explainable Priority Factors</span>
            <button onClick={() => setShowTooltip(false)} className="text-gray-400 hover:text-white" aria-label="Close tooltip">✕</button>
          </div>
          {factors?.factors && factors.factors.length > 0 ? (
            <ul className="space-y-1 text-gray-300">
              {factors.factors.map((f, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-brand-teal dark:text-teal-400">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400">Standard operational queue priority baseline (score {score}).</p>
          )}
        </div>
      )}
    </div>
  );
};

export default PriorityGauge;
