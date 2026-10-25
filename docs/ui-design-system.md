# UI Design System — Civic Precision
## Visual Language, Semantic Tokens & Theme System
**SIH 2026 Problem Statement 26262**  
**Product:** ReguFlow 360  
**Version:** 2.0.0 (Light & Dark Theme Architecture)

---

### 1. Design Philosophy: Civic Precision
ReguFlow 360 is an enterprise statutory compliance platform. The interface communicates institutional dignity, operational clarity, and regulatory authority.

**Key Tenets:**
- **High Information Density with Visual Caliber**: Clear grid alignments, crisp borders, legible tabular layouts, and structured metadata chips.
- **Strict Color Semantics**: No decorative rainbow gradients or arbitrary pastels. Colors directly denote regulatory state (Teal for approved/primary, Amber for time-sensitive deficiency/approaching SLA, Red for overdue/escalated/rejected, Ink for statutory headers).
- **Dual Visual Themes (Light & Dark)**: Engineered for long regulatory working sessions. Both themes preserve brand character without neon glare or inverted contrast washouts.
- **Zero Dead Clicks**: Every element is purposeful, focusable, keyboard-accessible, and state-synchronized.

---

### 2. Semantic Theme Token Palette

| Token Identifier | CSS Variable | Light Theme (Porcelain Canvas) | Dark Theme (Obsidian Operational) | Intended Semantic Purpose |
|---|---|---|---|---|
| **Ink** | `--brand-ink` | `#152536` | `#F1F5F8` | Primary text, titles, navigation accents |
| **Canvas / Porcelain** | `--brand-porcelain` | `#F4F6F8` | `#101820` | Application background |
| **Primary Surface** | `--brand-surface` | `#FFFFFF` | `#1B2835` | Card containers, panels, data tables, modals |
| **Secondary Surface**| `--brand-surface-secondary` | `#EDF1F4` | `#152536` | Table headers, chip backgrounds, nested boxes |
| **Elevated Surface** | `--brand-surface-elevated` | `#FFFFFF` | `#233342` | Popovers, active dropdown items, row hovers |
| **Border Slate** | `--brand-border` | `#DFE5E9` | `#354653` | Structural dividers, input strokes, grid lines |
| **Muted Text** | `--brand-muted` | `#526473` | `#B3C0CA` | Metadata subtitles, captions, table headers |
| **Meridian Teal** | `--brand-teal` | `#0E746B` | `#14B8A6` | Primary brand accent, verified status, focus rings |
| **Teal Light Tint** | `--brand-teal-light` | `#E6F5F3` | `rgba(20, 184, 166, 0.15)` | Verified badge fills, active item highlights |
| **Teal Dark** | `--brand-teal-dark` | `#0B5B54` | `#0D9488` | Active button press, high-emphasis teal |
| **Amber Warning** | `--brand-amber` | `#C5892B` | `#E5A83B` | Approaching deadlines, open deficiencies |
| **Amber Light Tint** | `--brand-amber-light` | `#FEF7ED` | `rgba(229, 168, 59, 0.15)` | Urgency badge fills, SLA alert pills |
| **Signal Red** | `--brand-red` | `#B9474F` | `#E05661` | Overdue escalations, rejected applications |
| **Red Light Tint** | `--brand-red-light` | `#FDF2F2` | `rgba(224, 86, 97, 0.15)` | Overdue badge fills, critical alerts |

---

### 3. Theme Controller Architecture

The theme engine supports three explicit modes:
1. **Light**: Clean, bright regulatory workspace with high-contrast `#152536` ink over `#F4F6F8`.
2. **Dark**: Restrained operational workspace with `#F1F5F8` text over `#101820` canvas and `#1B2835` cards.
3. **System**: Synchronizes live with operating system color preference (`prefers-color-scheme: dark`) via event listeners.

#### Persistence & Anti-Flash Boot Sequence
1. Preference is stored under `localStorage.getItem('reguflow_theme')`.
2. Before React hydrates, an inline synchronous boot script in `index.html` resolves the stored preference and applies the `.dark` class to `document.documentElement` if dark mode is active. This eliminates any white flash on cold loads or reloads.
3. Theme transitions are smooth and subtle (`0.15s ease`), respecting `prefers-reduced-motion` settings.

---

### 4. Canonical Status Badges Across Themes

All 24 canonical statuses in `StatusBadge` adapt dynamically to provide high contrast in both themes:

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

---

### 5. Accessibility & Invariants
- **Contrast**: Both text-on-surface and badge-text combinations meet WCAG 2.1 AA / AAA contrast requirements.
- **Keyboard Navigation**: ThemeToggle is fully operable via `Tab`, `Enter`, `Space`, and `Escape`.
- **Screen Reader Support**: All toggles expose semantic `aria-label`, `aria-pressed`, `aria-expanded`, and `role="menu"` attributes.
- **No Reliance on Color Alone**: Every badge features explicit semantic labels alongside indicator dots.
- **Workflow State Preservation**: Switching themes mutates zero form inputs, active filters, or query states.
