# UI Design System — Civic Precision
## Visual Language, Semantic Tokens & Component Guidelines
**SIH 2026 Problem Statement 26262**  
**Product:** ReguFlow 360  
**Version:** 1.0.0

---

### 1. Design Philosophy: Civic Precision
ReguFlow 360 is an enterprise statutory compliance platform. The interface must communicate institutional dignity, operational clarity, and regulatory authority.

**Key Tenets:**
- **High Information Density with Visual Caliber**: Clear grid alignments, crisp borders, legible tabular layouts, and structured metadata chips.
- **Strict Color Semantics**: No decorative rainbow gradients or arbitrary pastels. Colors directly denote regulatory state (Teal for approved/primary, Amber for time-sensitive deficiency/approaching SLA, Red for overdue/escalated/rejected, Ink for statutory headers).
- **Zero Dead Clicks**: Every element is purposeful, focusable, keyboard-accessible, and state-synchronized.

---

### 2. Semantic Color Palette

| Token Name | Hex Code | Tailwind Utility Class | Intended Purpose |
|---|---|---|---|
| **Midnight Ink** | `#152536` | `bg-brand-ink` / `text-brand-ink` | Navigation headers, primary titles, statutory accents |
| **Cool Porcelain** | `#F4F6F8` | `bg-brand-porcelain` | Page backgrounds, subtle card fills |
| **White Surface** | `#FFFFFF` | `bg-white` | Elevated card bodies, modals, data tables |
| **Meridian Teal** | `#0E746B` | `bg-brand-teal` / `text-brand-teal` | Primary brand accent, verified status, active navigation |
| **Teal Light** | `#E6F5F3` | `bg-brand-teal-light` | Verified badge backgrounds, active item highlights |
| **Amber Warning**| `#C5892B` | `bg-brand-amber` / `text-brand-amber` | Approaching deadlines, open deficiencies, pending reviews |
| **Amber Light** | `#FEF7ED` | `bg-brand-amber-light` | Warning alert backgrounds, urgency pills |
| **Signal Red** | `#B9474F` | `bg-brand-red` / `text-brand-red` | Overdue escalations, rejected applications, critical alerts |
| **Red Light** | `#FDF2F2` | `bg-brand-red-light` | Danger alert backgrounds, overdue tags |
| **Border Slate** | `#DFE5E9` | `border-brand-border` | Subtle component dividers, table grids, inputs |
| **Muted Text** | `#526473` | `text-brand-muted` | Supporting captions, metadata subtitles, table headers |

---

### 3. Typography & Spacing
- **Font Stack**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `sans-serif`
- **Scale**:
  - `Display / Page Title`: `24px` (`text-2xl`), font-semibold, letter-spacing `-0.02em`
  - `Section Header`: `18px` (`text-lg`), font-semibold, letter-spacing `-0.01em`
  - `Body / Form Label`: `14px` (`text-sm`), font-normal / medium
  - `Caption / Metadata`: `12px` (`text-xs`), font-medium
- **Layout Spacing**:
  - Grid gutters: `gap-4` (16px) or `gap-6` (24px)
  - Card padding: `p-5` or `p-6`
  - Table cell padding: `px-4 py-3.5`

---

### 4. Canonical Status Badges

```tsx
// Status badge mapping ensures unified color and contrast
export const StatusBadge = ({ status }: { status: string }) => {
  const configs: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    APPROVED: { bg: "bg-teal-50 border-teal-200", text: "text-[#0E746B]", dot: "bg-[#0E746B]", label: "Approved" },
    VERIFIED: { bg: "bg-teal-50 border-teal-200", text: "text-[#0E746B]", dot: "bg-[#0E746B]", label: "Verified" },
    SUBMITTED: { bg: "bg-blue-50 border-blue-200", text: "text-blue-700", dot: "bg-blue-600", label: "Submitted" },
    UNDER_SCRUTINY: { bg: "bg-sky-50 border-sky-200", text: "text-sky-800", dot: "bg-sky-600", label: "Under Scrutiny" },
    DEFICIENCY_COMMUNICATED: { bg: "bg-amber-50 border-amber-200", text: "text-[#C5892B]", dot: "bg-[#C5892B]", label: "Deficiency Cure Required" },
    OVERDUE: { bg: "bg-red-50 border-red-200", text: "text-[#B9474F]", dot: "bg-[#B9474F]", label: "Overdue" },
    REJECTED: { bg: "bg-red-50 border-red-200", text: "text-[#B9474F]", dot: "bg-[#B9474F]", label: "Rejected" },
    EVC_SCHEDULED: { bg: "bg-purple-50 border-purple-200", text: "text-purple-700", dot: "bg-purple-600", label: "EVC Scheduled" },
  };
  // Fallback defaults provided
};
```

---

### 5. Standard Component Guidelines
- **Header & Navbar**: Midnight Ink top-bar branding with active academic cycle (`2026-2027`), real-time notification drawer, active user role switcher, and tenant badge.
- **Sidebar**: Distinct iconography (`lucide-react`), section grouping, unread notification counter badges, collapsible toggle.
- **Data Table**: Sticky table header, row hover feedback (`hover:bg-[#F9FAFB]`), pagination toolbar, multi-filter dropdowns, and search input with instant debounce.
- **Explainable Priority Gauge**: Color-coded pill (`Low: 0-39`, `Medium: 40-69`, `High: 70-89`, `Critical: 90-100`) with hoverable or clickable factor breakdown.
- **Action Timeline**: Chronological vertical line with actor attribution, role badge, timestamp formatted in `Asia/Kolkata`, and linked document evidence.
