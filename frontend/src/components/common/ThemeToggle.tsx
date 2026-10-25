import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  variant?: 'compact' | 'with-label' | 'dropdown' | 'segmented';
}

/**
 * Genuine One-Click Light/Dark Mode Switcher.
 * Switches instantly between Light and Dark themes with zero dropdowns or extra menus.
 * Accessible with visible focus rings, ARIA labels, and keyboard navigation.
 */
export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = '',
  showLabel = false,
  variant,
}) => {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  const labelText = isDark ? 'Switch to Light' : 'Switch to Dark';
  const ariaLabel = isDark
    ? 'Switch to light mode (currently in dark mode)'
    : 'Switch to dark mode (currently in light mode)';

  const displayLabel = showLabel || variant === 'with-label' || variant === 'segmented';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={ariaLabel}
      title={labelText}
      className={`inline-flex items-center justify-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-teal select-none cursor-pointer border-brand-border bg-brand-surface text-brand-ink hover:bg-brand-surface-secondary active:scale-95 ${className}`}
    >
      {isDark ? (
        <Sun className="w-4 h-4 text-amber-400 shrink-0 transition-transform duration-200 hover:rotate-45" />
      ) : (
        <Moon className="w-4 h-4 text-slate-700 dark:text-slate-200 shrink-0 transition-transform duration-200 hover:-rotate-12" />
      )}
      {displayLabel && (
        <span className="truncate">
          {isDark ? 'Light Mode' : 'Dark Mode'}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
