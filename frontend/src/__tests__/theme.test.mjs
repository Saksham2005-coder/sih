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
    assert.match(indexCss, /--brand-teal:\s*#0E746B/, 'Light teal must be Meridian Teal #0E746B');
    assert.match(indexCss, /--brand-amber:\s*#C5892B/, 'Light amber must be Warning #C5892B');
    assert.match(indexCss, /--brand-red:\s*#B9474F/, 'Light red must be Danger #B9474F');
    assert.match(indexCss, /--brand-border:\s*#DFE5E9/, 'Light border must be Slate #DFE5E9');

    // Dark theme token checks
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-ink:\s*#F1F5F8/, 'Dark ink must be high contrast #F1F5F8');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-porcelain:\s*#101820/, 'Dark app bg must be Obsidian #101820');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-surface:\s*#1B2835/, 'Dark primary surface must be #1B2835');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-surface-elevated:\s*#233342/, 'Dark elevated surface must be #233342');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-border:\s*#354653/, 'Dark border must be #354653');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-teal:\s*#14B8A6/, 'Dark teal must be readable #14B8A6');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-amber:\s*#E5A83B/, 'Dark amber must be readable #E5A83B');
    assert.match(indexCss, /\.dark\s*\{[\s\S]*--brand-red:\s*#E05661/, 'Dark red must be readable #E05661');
  });

  it('2. Tailwind configuration enables class-based dark mode and maps brand colors to CSS variables', () => {
    const tailwindConfig = fs.readFileSync(path.join(srcDir, '..', 'tailwind.config.js'), 'utf-8');
    assert.match(tailwindConfig, /darkMode:\s*['"]class['"]/, 'Tailwind must configure darkMode: "class"');
    assert.match(tailwindConfig, /ink:\s*['"]var\(--brand-ink\)['"]/, 'Tailwind ink must map to CSS variable');
    assert.match(tailwindConfig, /surface:\s*['"]var\(--brand-surface\)['"]/, 'Tailwind surface must map to CSS variable');
    assert.match(tailwindConfig, /porcelain:\s*['"]var\(--brand-porcelain\)['"]/, 'Tailwind porcelain must map to CSS variable');
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

  it('5. ThemeToggle provides accessible controls and multiple variants', () => {
    const themeToggle = fs.readFileSync(path.join(srcDir, 'components', 'common', 'ThemeToggle.tsx'), 'utf-8');
    assert.match(themeToggle, /aria-label=/, 'ThemeToggle must include accessible aria-label');
    assert.match(themeToggle, /aria-haspopup=/, 'ThemeToggle dropdown must include aria-haspopup');
    assert.match(themeToggle, /role=["']menu["']/, 'ThemeToggle must include role="menu"');
    assert.match(themeToggle, /Sun.*Moon.*Monitor/, 'ThemeToggle must support Sun, Moon, and Monitor icons');
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
    assert.ok(statCard.includes('dark:bg-brand-surface'), 'StatCard must have dark surface');
    assert.ok(statCard.includes('dark:border-'), 'StatCard must have dark border variants');

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
    assert.ok(sidebar.includes('dark:bg-brand-surface'), 'Sidebar must adapt background in dark mode');
    assert.ok(sidebar.includes('dark:border-brand-border'), 'Sidebar must adapt border in dark mode');

    const appLayout = fs.readFileSync(path.join(srcDir, 'components', 'layout', 'AppLayout.tsx'), 'utf-8');
    assert.ok(appLayout.includes('bg-brand-porcelain'), 'AppLayout must use tokenized porcelain bg');
  });

  it('10. Global index.css contains dark mode normalizations for tables, form controls, and scrollbars', () => {
    const indexCss = fs.readFileSync(path.join(srcDir, 'index.css'), 'utf-8');
    assert.ok(indexCss.includes('.dark table thead'), 'index.css must normalize dark table thead');
    assert.ok(indexCss.includes('.dark input:not'), 'index.css must normalize dark inputs');
    assert.ok(indexCss.includes('.dark select:not'), 'index.css must normalize dark select');
    assert.ok(indexCss.includes('.dark ::-webkit-scrollbar-thumb'), 'index.css must configure dark scrollbars');
    assert.ok(indexCss.includes('prefers-reduced-motion'), 'index.css must support prefers-reduced-motion');
  });
});
