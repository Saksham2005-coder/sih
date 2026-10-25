# UI Design System — Civic Precision
## Visual Language, Semantic Tokens & Theme System
**SIH 2026 Problem Statement 26262**  
**Product:** ReguFlow 360  
**Version:** 2.1.0 (Unified Semantic Tokens & Instant One-Click Themes)

---

### 1. Design Philosophy: Civic Precision
ReguFlow 360 is an enterprise statutory compliance platform engineered for AICTE approval workflows, compliance monitoring, deficiency cures, and officer command centers. The interface communicates institutional dignity, operational clarity, and regulatory authority.

**Key Tenets:**
- **High Information Density with Visual Caliber**: Clear grid alignments, crisp borders, legible tabular layouts, and structured metadata chips.
- **Strict Color Semantics**: No decorative rainbow gradients or arbitrary pastels. Colors directly denote regulatory state (Teal for approved/primary, Amber for time-sensitive deficiency/approaching SLA, Orange for high priority triage, Red for overdue/escalated/rejected, Ink for statutory headers).
- **Dual Visual Themes (Light & Dark)**: Engineered for long regulatory working sessions. Both themes preserve brand character without neon glare or inverted contrast washouts.
- **One-Click Instant Theme Switching**: Single-click toggling between Light and Dark mode without menus, dropdowns, or multi-step selections.
- **Zero Dead Clicks**: Every element is purposeful, focusable, keyboard-accessible, and state-synchronized.

---

### 2. Semantic Theme Token Palette

The application uses centralized CSS variables in `index.css` mapped into Tailwind tokens in `tailwind.config.js`:

| Token Identifier | Tailwind Class | Light Theme (Porcelain Canvas) | Dark Theme (Obsidian Operational) | Intended Semantic Purpose |
|---|---|---|---|---|
| **Ink** | `text-brand-ink` / `text-primary` | `#152536` | `#F1F5F8` | Primary text, titles, navigation accents |
| **Canvas / Porcelain** | `bg-brand-porcelain` / `bg-app-bg` | `#F4F6F8` | `#101820` | Application background canvas |
| **Primary Surface** | `bg-brand-surface` / `bg-surface` | `#FFFFFF` | `#1B2835` | Card containers, panels, data tables, modals |
| **Secondary Surface**| `bg-brand-surface-secondary` | `#EDF1F4` | `#152536` | Table headers, chip backgrounds, nested boxes |
| **Elevated Surface** | `bg-brand-surface-elevated` | `#FFFFFF` | `#233342` | Popovers, active dropdown items, row hovers |
| **Border Slate** | `border-brand-border` / `border-main` | `#DFE5E9` | `#354653` | Structural dividers, input strokes, grid lines |
| **Muted Text** | `text-brand-muted` / `text-secondary` | `#526473` | `#B3C0CA` | Metadata subtitles, captions, table headers |
| **Meridian Teal** | `text-brand-teal` / `bg-brand-teal` | `#0E746B` | `#14B8A6` | Primary brand accent, verified status, focus rings |
| **Teal Light Tint** | `bg-teal-50` | `#E6F5F3` | `rgba(20, 184, 166, 0.15)` | Verified badge fills, active item highlights |
| **Teal Dark** | `bg-brand-teal-dark` | `#0B5B54` | `#0D9488` | Active button press, high-emphasis teal |
| **Amber Warning** | `text-[#C5892B]` / `text-warning` | `#C5892B` | `#E5A83B` | Approaching deadlines, open deficiencies |
| **Amber Light Tint** | `bg-amber-50` | `#FEF7ED` | `rgba(229, 168, 59, 0.15)` | Urgency badge fills, SLA alert pills |
| **Signal Red** | `text-[#B9474F]` / `text-danger` | `#B9474F` | `#E05661` | Overdue escalations, rejected applications |
| **Red Light Tint** | `bg-red-50` | `#FDF2F2` | `rgba(224, 86, 97, 0.15)` | Overdue badge fills, critical alerts |

---

### 3. One-Click Theme Controller Architecture

The theme engine provides an instant, single-click toggle between Light and Dark mode across all views:

- **Component**: `ThemeToggle.tsx` renders a single, accessible `<button>` displaying the Sun icon (in dark mode) or Moon icon (in light mode).
- **Zero Dropdowns**: Eliminated multi-step dropdowns, floating menus, or segmented 3-way selectors. A single click immediately inverts the theme.
- **Keyboard Operable**: Fully accessible via standard keyboard navigation (`Tab`, `Enter`, `Space`) with an explicit focus ring (`focus:ring-2 focus:ring-brand-teal`).
- **Screen Reader Support**: Exposes dynamic `aria-label` ("Switch to light mode" / "Switch to dark mode") and `title` tooltip.

#### Persistence & Anti-Flash Boot Sequence
1. Stored under `localStorage.getItem('reguflow_theme')` (`'dark'` or `'light'`).
2. Before React mounts, an inline synchronous boot script in `index.html` resolves the stored preference (or system `prefers-color-scheme: dark`) and applies the `.dark` class to `document.documentElement`. This guarantees zero white flashes or mismatched surfaces on initial load or refresh.
3. Theme transitions are smooth and performant (`150ms ease`), respecting `prefers-reduced-motion`.

---

### 4. Component Standards & Polish

#### 4.1 Buttons
- **Primary**: `bg-brand-teal text-white hover:bg-brand-teal-dark shadow-sm transition-colors rounded-lg font-semibold text-xs`
- **Secondary / Outline**: `border border-brand-border bg-white dark:bg-brand-surface text-brand-ink dark:text-brand-text hover:bg-gray-50 dark:hover:bg-brand-surface-elevated transition-colors rounded-lg font-semibold text-xs`
- **Ghost**: `text-brand-muted hover:text-brand-ink dark:hover:text-brand-text hover:bg-gray-100 dark:hover:bg-brand-surface-elevated rounded-lg transition-colors`
- **Danger**: `bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-[#B9474F] dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/60`

#### 4.2 Cards (`StatCard.tsx`)
- Unified card surface (`bg-white dark:bg-brand-surface border border-brand-border p-5 rounded-xl shadow-sm`).
- Crisp accent borders:
  - Default: `border-brand-border`
  - Teal: `border-brand-border border-t-2 border-t-brand-teal`
  - Amber: `border-brand-border border-t-2 border-t-[#C5892B]`
  - Red: `border-brand-border border-t-2 border-t-[#B9474F]`
- Subtle 150ms micro-lift on hover (`hover:-translate-y-0.5 hover:shadow-md transition-all duration-150`).

#### 4.3 Priority Indicators (`PriorityGauge.tsx`)
- Standardized 0–100 operational triage scores with high-contrast, non-washed-out styling:
  - Low (0–39): Teal pill and bar (`bg-teal-50 dark:bg-teal-950/60 text-brand-teal border-teal-200 dark:border-teal-800/80`)
  - Medium (40–69): Amber pill and bar (`bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800/80`)
  - High (70–84): Orange pill and bar (`bg-orange-50 dark:bg-orange-950/60 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800/80`)
  - Critical (85–100): Red pill and bar (`bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 border-red-200 dark:border-red-900/80`)
- Accessible attributes: `role="progressbar"`, `aria-valuenow`, `aria-valuemin={0}`, `aria-valuemax={100}`, `aria-valuetext`.

#### 4.4 Status Badges (`StatusBadge.tsx`)
All 24 canonical statuses adapt dynamically to provide high contrast in both themes:

| Status Group | Status Name | Light Token Set | Dark Token Set |
|---|---|---|---|
| **Application Stages** | `SUBMITTED`, `RESUBMITTED` | `bg-blue-50 border-blue-200 text-blue-700` | `dark:bg-blue-950/40 dark:border-blue-800/60 dark:text-blue-300` |
| | `UNDER_SCRUTINY` | `bg-sky-50 border-sky-200 text-sky-800` | `dark:bg-sky-950/40 dark:border-sky-800/60 dark:text-sky-300` |
| | `DEFICIENCY_COMMUNICATED` | `bg-amber-50 border-amber-200 text-[#C5892B]` | `dark:bg-amber-950/40 dark:border-amber-800/60 dark:text-amber-300` |
| | `SCRUTINY_COMPLETED`, `APPROVED` | `bg-teal-50 border-teal-200 text-[#0E746B]` | `dark:bg-teal-950/40 dark:border-teal-800/60 dark:text-teal-300` |
| | `AWAITING_EVC_SCHEDULE`, `EVC_SCHEDULED` | `bg-purple-50 border-purple-200 text-purple-700` | `dark:bg-purple-950/40 dark:border-purple-800/60 dark:text-purple-300` |
| | `REJECTED`, `OPEN` | `bg-red-50 border-red-200 text-[#B9474F]` | `dark:bg-red-950/40 dark:border-red-800/60 dark:text-red-300` |
| **Undertakings** | `NOT_YET_DUE`, `CLOSED` | `bg-gray-50 border-gray-200 text-gray-700` | `dark:bg-gray-800/60 dark:border-gray-700 dark:text-gray-300` |
| | `DUE_SOON`, `EXPIRING_SOON` | `bg-amber-50 border-amber-200 text-[#C5892B]` | `dark:bg-amber-950/40 dark:border-amber-800/60 dark:text-amber-300` |
| | `VERIFIED`, `ACTIVE`, `CURED` | `bg-teal-50 border-teal-200 text-[#0E746B]` | `dark:bg-teal-950/40 dark:border-teal-800/60 dark:text-teal-300` |
| | `OVERDUE`, `EXPIRED` | `bg-red-50 border-red-200 text-[#B9474F]` | `dark:bg-red-950/40 dark:border-red-800/60 dark:text-red-300` |

#### 4.5 Modals & Dialogs (`Modal.tsx`)
- Dark mode backdrop with subtle blur (`bg-black/60 backdrop-blur-xs`).
- Dialog surface: `bg-white dark:bg-brand-surface border border-brand-border shadow-xl rounded-xl`.
- Accessible close button with focus ring and contrasting hover states.

#### 4.6 Shell Layout (`AppLayout.tsx`)
- Eliminated desktop whitespace voids by removing restrictive max-width from the outer `<main>` element and scoping `max-w-7xl` inside a centered container with uniform responsive padding (`px-4 sm:px-6 lg:px-8 py-8`).

---

### 5. Accessibility & Invariants
- **Contrast**: Both text-on-surface and badge-text combinations meet WCAG 2.1 AA / AAA contrast standards.
- **Keyboard Navigation**: ThemeToggle is fully operable via `Tab`, `Enter`, and `Space`. Modals trap focus and close on `Escape`.
- **Screen Reader Support**: All interactive elements expose semantic `aria-label`, `aria-pressed`, `aria-valuenow`, and descriptive titles.
- **No Reliance on Color Alone**: Every badge features explicit semantic text labels alongside geometric indicator dots.
- **Workflow State Preservation**: Switching themes mutates zero form inputs, active filters, URL parameters, or query caches.
