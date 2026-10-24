import React, { useState } from 'react';
import { AlertCircle, HelpCircle } from 'lucide-react';

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
  let colorClass = 'bg-teal-50 text-brand-teal border-teal-200';
  let barColor = 'bg-brand-teal';

  if (score >= 80) {
    tier = 'Critical';
    colorClass = 'bg-red-50 text-[#B9474F] border-red-200';
    barColor = 'bg-[#B9474F]';
  } else if (score >= 60) {
    tier = 'High';
    colorClass = 'bg-amber-50 text-[#C5892B] border-amber-200';
    barColor = 'bg-[#C5892B]';
  } else if (score >= 40) {
    tier = 'Medium';
    colorClass = 'bg-blue-50 text-blue-700 border-blue-200';
    barColor = 'bg-blue-600';
  }

  return (
    <div className="relative inline-flex items-center gap-2">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5">
          <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colorClass}`}>
            {score}/100 • {tier}
          </span>
          <button
            type="button"
            onClick={() => setShowTooltip(!showTooltip)}
            className="text-brand-muted hover:text-brand-ink"
            title="Explain Priority Factors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div className={`h-full ${barColor}`} style={{ width: `${score}%` }} />
        </div>
      </div>

      {showTooltip && (
        <div className="absolute z-50 left-0 top-8 w-64 p-3 bg-brand-ink text-white text-xs rounded-lg shadow-xl border border-gray-700">
          <div className="flex items-center justify-between pb-1 mb-2 border-b border-gray-700 font-semibold">
            <span>Explainable Priority Factors</span>
            <button onClick={() => setShowTooltip(false)} className="text-gray-400 hover:text-white">✕</button>
          </div>
          {factors?.factors && factors.factors.length > 0 ? (
            <ul className="space-y-1 text-gray-300">
              {factors.factors.map((f, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-brand-teal">•</span>
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
