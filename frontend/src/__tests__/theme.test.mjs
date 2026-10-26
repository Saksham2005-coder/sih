import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — Theme System & Token Architecture', () => {

  it('1. CSS Tokens define exact Civic Precision light and dark palettes', () => {
    const indexCss = fs.readFileSync(path.join(srcDir, 'index.css'), 'utf-8');

    // Light theme token checks
    assert.match(indexCss, /--brand-ink:\s*#152536/, 'Light ink must be Midnight Ink #152536');
    assert.match(indexCss, /--brand-porcelain:\s*#F4F6F8/, 'Light porcelain must be Cool Porcelain #F4F6F8');
    assert.match(indexCss, /--brand-header-bg:\s*#101E2D/, 'Light header bg must be #101E2D');
    assert.match(indexCss, /--brand-teal:\s*#0E746B/, 'Light teal must be Meridian Teal #0E746B');
    assert.match(indexCss, /--brand-amber:\s*#C5892B/, 'Light amber must be Warning #C5892B');
    assert.match(indexCss, /--brand-red:\s*#B9474F/, 'Light red must be Danger #B9474F');
    assert.match(indexCss, /--brand-border:\s*#DFE5E9/, 'Light border must be Slate #DFE5E9');

    // Dark theme token checks (Midnight Slate + Meridian Teal canonical palette)
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-canvas:\s*#0C141D/, 'Dark app canvas must be #0C141D');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-header-bg:\s*#101E2D/, 'Dark header bg must be #101E2D');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-sidebar-bg:\s*#111F2E/, 'Dark sidebar bg must be #111F2E');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-surface:\s*#162432/, 'Dark primary surface must be #162432');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-surface-secondary:\s*#1A2A39/, 'Dark secondary surface must be #1A2A39');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-surface-elevated:\s*#223546/, 'Dark elevated surface must be #223546');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-text-primary:\s*#EDF3F8/, 'Dark primary text must be #EDF3F8');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-text-secondary:\s*#B0BECC/, 'Dark secondary text must be #B0BECC');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-border:\s*#2D4051/, 'Dark border must be #2D4051');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-teal:\s*#39C6B4/, 'Dark teal accent must be #39C6B4');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-action:\s*#0D8479/, 'Dark action surface must be #0D8479');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-amber:\s*#F2C96D/, 'Dark amber must be #F2C96D');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-red:\s*#F58F98/, 'Dark red must be #F58F98');
  });

  it('2. Tailwind configuration enables class-based dark mode and maps brand colors to CSS variables', () => {
    const tailwindConfig = fs.readFileSync(path.join(srcDir, '..', 'tailwind.config.js'), 'utf-8');
    assert.match(tailwindConfig, /darkMode:\s*['"]class['"]/, 'Tailwind must configure darkMode: "class"');
    assert.match(tailwindConfig, /ink:\s*['"]var\(--brand-ink\)['"]/, 'Tailwind ink must map to CSS variable');
    assert.match(tailwindConfig, /surface:\s*['"]var\(--brand-surface\)['"]/, 'Tailwind surface must map to CSS variable');
    assert.match(tailwindConfig, /porcelain:\s*['"]var\(--brand-porcelain\)['"]/, 'Tailwind porcelain must map to CSS variable');
    assert.match(tailwindConfig, /canvas:\s*['"]var\(--brand-canvas\)['"]/, 'Tailwind canvas must map to CSS variable');
  });

  it('3. Anti-flash boot script exists in index.html to prevent flash of wrong theme', () => {
    const indexHtml = fs.readFileSync(path.join(srcDir, '..', 'index.html'), 'utf-8');
    assert.match(indexHtml, /localStorage\.getItem\(['"]reguflow_theme['"]\)/, 'Index.html must read reguflow_theme');
    assert.match(indexHtml, /prefers-color-scheme:\s*dark/, 'Index.html must check system media query');
    assert.match(indexHtml, /document\.documentElement\.classList\.add\(['"]dark['"]\)/, 'Index.html must add dark class');
  });

  it('4. ThemeContext handles light, dark, and system modes with persistence and DOM mutation', () => {
    const themeContext = fs.readFileSync(path.join(srcDir, 'context', 'ThemeContext.tsx'), 'utf-8');
    assert.match(themeContext, /THEME_STORAGE_KEY\s*=\s*['"]reguflow_theme['"]/, 'Theme storage key must be reguflow_theme');
    assert.match(themeContext, /localStorage\.getItem\(THEME_STORAGE_KEY\)/, 'ThemeContext must load preference');
    assert.match(themeContext, /localStorage\.setItem\(THEME_STORAGE_KEY/, 'ThemeContext must persist preference');
    assert.match(themeContext, /root\.classList\.add\(['"]dark['"]\)/, 'ThemeContext must add dark class');
    assert.match(themeContext, /root\.classList\.remove\(['"]dark['"]\)/, 'ThemeContext must remove dark class');
    assert.match(themeContext, /root\.setAttribute\(['"]data-theme['"],\s*resolvedTheme\)/, 'ThemeContext must set data-theme');
    assert.match(themeContext, /prefers-color-scheme:\s*dark/, 'ThemeContext must observe system media query');
  });

  it('5. ThemeToggle provides accessible, genuine one-click theme switching without dropdowns', () => {
    const themeToggle = fs.readFileSync(path.join(srcDir, 'components', 'common', 'ThemeToggle.tsx'), 'utf-8');
    assert.match(themeToggle, /aria-label=/, 'ThemeToggle must include accessible aria-label');
    assert.match(themeToggle, /toggleTheme/, 'ThemeToggle must directly invoke toggleTheme on click');
    assert.match(themeToggle, /Sun.*Moon/, 'ThemeToggle must display Sun and Moon icons');
    assert.ok(!themeToggle.includes('role="menu"'), 'ThemeToggle must not use dropdown menu role');
  });

  it('6. All canonical regulatory statuses in StatusBadge have dark-mode contrast tokens', () => {
    const statusBadge = fs.readFileSync(path.join(srcDir, 'components', 'common', 'StatusBadge.tsx'), 'utf-8');
    const requiredStatuses = [
      'SUBMITTED', 'UNDER_SCRUTINY', 'DEFICIENCY_COMMUNICATED', 'RESUBMITTED',
      'SCRUTINY_COMPLETED', 'AWAITING_EVC_SCHEDULE', 'EVC_SCHEDULED', 'EVC_COMPLETED',
      'AWAITING_SAC_CAC_REVIEW', 'AWAITING_COMPETENT_AUTHORITY', 'APPROVED', 'REJECTED',
      'CLOSED', 'NOT_YET_DUE', 'DUE_SOON', 'PENDING_VERIFICATION', 'VERIFIED', 'OVERDUE',
      'ACTIVE', 'EXPIRING_SOON', 'RENEWAL_SUBMITTED', 'EXPIRED', 'OPEN', 'CURED'
    ];

    for (const status of requiredStatuses) {
      assert.ok(statusBadge.includes(status), `StatusBadge must configure ${status}`);
    }

    assert.ok(statusBadge.includes('dark:bg-'), 'StatusBadge must contain dark background tokens');
    assert.ok(statusBadge.includes('dark:text-'), 'StatusBadge must contain dark text tokens');
    assert.ok(statusBadge.includes('dark:border-'), 'StatusBadge must contain dark border tokens');
  });

  it('7. StatCard and PriorityGauge feature dark mode variants', () => {
    const statCard = fs.readFileSync(path.join(srcDir, 'components', 'common', 'StatCard.tsx'), 'utf-8');
    assert.ok(statCard.includes('bg-brand-surface'), 'StatCard must have brand surface');
    assert.ok(statCard.includes('border-brand-border'), 'StatCard must have border tokens');

    const priorityGauge = fs.readFileSync(path.join(srcDir, 'components', 'common', 'PriorityGauge.tsx'), 'utf-8');
    assert.ok(priorityGauge.includes('dark:bg-'), 'PriorityGauge must have dark tier backgrounds');
    assert.ok(priorityGauge.includes('dark:text-'), 'PriorityGauge must have dark tier text');
  });

  it('8. Header and LoginPage expose accessible ThemeToggle', () => {
    const header = fs.readFileSync(path.join(srcDir, 'components', 'layout', 'Header.tsx'), 'utf-8');
    assert.ok(header.includes('<ThemeToggle'), 'Header must render ThemeToggle');

    const loginPage = fs.readFileSync(path.join(srcDir, 'pages', 'auth', 'LoginPage.tsx'), 'utf-8');
    assert.ok(loginPage.includes('<ThemeToggle'), 'LoginPage must render ThemeToggle');
  });

  it('9. Sidebar and AppLayout adapt seamlessly between light and dark themes', () => {
    const sidebar = fs.readFileSync(path.join(srcDir, 'components', 'layout', 'Sidebar.tsx'), 'utf-8');
    assert.ok(sidebar.includes('bg-brand-sidebar-bg'), 'Sidebar must adapt background with semantic token');
    assert.ok(sidebar.includes('border-brand-border'), 'Sidebar must adapt border with semantic token');

    const appLayout = fs.readFileSync(path.join(srcDir, 'components', 'layout', 'AppLayout.tsx'), 'utf-8');
    assert.ok(appLayout.includes('bg-brand-canvas'), 'AppLayout must use tokenized canvas bg');
  });

  it('10. Global index.css contains dark mode normalizations for tables, form controls, and scrollbars', () => {
    const indexCss = fs.readFileSync(path.join(srcDir, 'index.css'), 'utf-8');
    assert.ok(indexCss.includes('.dark table thead'), 'index.css must normalize dark table thead');
    assert.ok(indexCss.includes('.dark input:not'), 'index.css must normalize dark inputs');
    assert.ok(indexCss.includes('.dark select:not'), 'index.css must normalize dark select');
    assert.ok(indexCss.includes('.dark ::-webkit-scrollbar-thumb'), 'index.css must configure dark scrollbars');
    assert.ok(indexCss.includes('prefers-reduced-motion'), 'index.css must support prefers-reduced-motion');
  });

  it('11. Regression test: Header background must not resolve to light background in dark mode', () => {
    const indexCss = fs.readFileSync(path.join(srcDir, 'index.css'), 'utf-8');
    const headerTsx = fs.readFileSync(path.join(srcDir, 'components', 'layout', 'Header.tsx'), 'utf-8');

    // Extract dark theme block
    const darkBlockMatch = indexCss.match(/\.dark\s*\{([\s\S]*?)\}/);
    assert.ok(darkBlockMatch, 'Dark mode CSS block must exist');
    const darkBlock = darkBlockMatch[1];

    // Extract light theme (:root) block
    const rootBlockMatch = indexCss.match(/:root\s*\{([\s\S]*?)\}/);
    assert.ok(rootBlockMatch, ':root CSS block must exist');
    const rootBlock = rootBlockMatch[1];

    // Header background token must be #101E2D in both themes
    const lightHeaderBg = rootBlock.match(/--brand-header-bg:\s*([^;]+);/)[1].trim();
    const darkHeaderBg = darkBlock.match(/--brand-header-bg:\s*([^;]+);/)[1].trim();
    assert.strictEqual(lightHeaderBg, '#101E2D', 'Light header bg must be #101E2D');
    assert.strictEqual(darkHeaderBg, '#101E2D', 'Dark header bg must be #101E2D');

    // Header component must NOT use bg-brand-ink or light background
    assert.ok(!headerTsx.includes('bg-brand-ink'), 'Header must not use bg-brand-ink (prevents light bg collision in dark mode)');
    assert.ok(headerTsx.includes('bg-[var(--brand-header-bg)]') || headerTsx.includes('bg-brand-header-bg'), 'Header must explicitly bind to --brand-header-bg');

    // Header children options must not use bg-brand-ink with white text
    assert.ok(!headerTsx.includes('className="bg-brand-ink text-white"'), 'Header select options must not use colliding bg-brand-ink');
  });

  it('12. Contrast verification: Dark mode palette tokens satisfy WCAG contrast hierarchy', () => {
    function hexToRgb(hex) {
      const bigint = parseInt(hex.replace('#', ''), 16);
      return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
    }
    function luminance([r, g, b]) {
      const a = [r, g, b].map(v => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
    }
    function contrastRatio(hex1, hex2) {
      const lum1 = luminance(hexToRgb(hex1));
      const lum2 = luminance(hexToRgb(hex2));
      const brightest = Math.max(lum1, lum2);
      const darkest = Math.min(lum1, lum2);
      return (brightest + 0.05) / (darkest + 0.05);
    }

    const headerContrast = contrastRatio('#101E2D', '#EDF3F8');
    assert.ok(headerContrast > 10, `Header contrast (${headerContrast.toFixed(2)}) must exceed AAA 7:1`);

    const canvasContrast = contrastRatio('#0C141D', '#EDF3F8');
    assert.ok(canvasContrast > 10, `Canvas contrast (${canvasContrast.toFixed(2)}) must exceed AAA 7:1`);

    const surfaceContrast = contrastRatio('#162432', '#EDF3F8');
    assert.ok(surfaceContrast > 10, `Surface contrast (${surfaceContrast.toFixed(2)}) must exceed AAA 7:1`);

    const actionContrast = contrastRatio('#0D8479', '#FFFFFF');
    assert.ok(actionContrast > 4.5, `Action button contrast (${actionContrast.toFixed(2)}) must exceed AA 4.5:1`);
  });
});
