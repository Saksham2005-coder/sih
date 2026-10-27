import { test, describe } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — Judge Demonstration Centre & Live Workflow Explorer UI', () => {

  test('1. JudgeDemoCentre component exists and provides multi-track scenario inspection', () => {
    const filePath = path.join(srcDir, 'pages', 'demo', 'JudgeDemoCentre.tsx');
    assert.ok(fs.existsSync(filePath), 'JudgeDemoCentre.tsx must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('export const JudgeDemoCentre'), 'Exports JudgeDemoCentre component');
    assert.ok(content.includes('api.getDemoScenarios'), 'Loads synthetic scenarios from API');
    assert.ok(content.includes('api.getDemoRoutes'), 'Loads canonical workflow routes from API');
    assert.ok(content.includes('api.getDemoExplainability'), 'Loads deep explainability facts from API');
    assert.ok(content.includes('api.resetDemoScenario'), 'Provides safe scenario reset capability');
    assert.ok(content.includes('api.getDemoTelemetry'), 'Displays distributed system background telemetry');
  });

  test('2. Guided Regulatory Lifecycle Stepper derives authoritative states and explains non-applicable stages', () => {
    const filePath = path.join(srcDir, 'pages', 'demo', 'JudgeDemoCentre.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('CANONICAL_MILESTONES'), 'Defines canonical regulatory milestones');
    assert.ok(content.includes('NOT_APPLICABLE'), 'Handles statutory NOT APPLICABLE status');
    assert.ok(content.includes('aph_rule_reference'), 'Cites official Approval Process Handbook (APH) rules for non-applicable stages');
    assert.ok(content.includes('Deficiency Return Loop'), 'Explicitly models bidirectional deficiency cure loop');
  });

  test('3. Explainable Priority Panel enforces deterministic invariant (No ML hallucination)', () => {
    const filePath = path.join(srcDir, 'pages', 'demo', 'JudgeDemoCentre.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(
      content.includes('Deterministic mathematical attribution') || content.includes('Deterministic Point Attribution'),
      'Proclaims deterministic point attribution invariant'
    );
    assert.ok(content.includes('Never mutates statutory status'), 'Explicitly disclaims statutory decision mutation by priority score');
    assert.ok(content.includes('explainability.priority_breakdown.factors'), 'Visualizes itemized point contributions');
  });

  test('4. Frontend types export complete demonstration and workflow explorer contracts', () => {
    const filePath = path.join(srcDir, 'types', 'index.ts');
    assert.ok(fs.existsSync(filePath), 'types/index.ts must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('export interface DemoScenarioItem'), 'Exports DemoScenarioItem');
    assert.ok(content.includes('export interface WorkflowRouteDefinition'), 'Exports WorkflowRouteDefinition');
    assert.ok(content.includes('export interface WorkflowStageDefinition'), 'Exports WorkflowStageDefinition');
    assert.ok(content.includes('export interface NonApplicableStageDefinition'), 'Exports NonApplicableStageDefinition');
    assert.ok(content.includes('export interface ExplainabilityResponse'), 'Exports ExplainabilityResponse');
    assert.ok(content.includes('export interface DemoResetResponse'), 'Exports DemoResetResponse');
    assert.ok(content.includes('export interface DemoTelemetryResponse'), 'Exports DemoTelemetryResponse');
  });

  test('5. API client exposes full demo explorer endpoints', () => {
    const filePath = path.join(srcDir, 'api', 'client.ts');
    assert.ok(fs.existsSync(filePath), 'api/client.ts must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('getDemoScenarios:'), 'Exposes getDemoScenarios');
    assert.ok(content.includes('getDemoRoutes:'), 'Exposes getDemoRoutes');
    assert.ok(content.includes('getDemoExplainability:'), 'Exposes getDemoExplainability');
    assert.ok(content.includes('resetDemoScenario:'), 'Exposes resetDemoScenario');
    assert.ok(content.includes('getDemoTelemetry:'), 'Exposes getDemoTelemetry');
  });

  test('6. App layout, Header and Sidebar mount /demo/explorer navigation', () => {
    const appPath = path.join(srcDir, 'App.tsx');
    const appContent = fs.readFileSync(appPath, 'utf-8');
    assert.ok(appContent.includes('/demo/explorer'), 'App.tsx registers /demo/explorer route');
    assert.ok(appContent.includes('JudgeDemoCentre'), 'App.tsx mounts JudgeDemoCentre component');

    const headerPath = path.join(srcDir, 'components', 'layout', 'Header.tsx');
    const headerContent = fs.readFileSync(headerPath, 'utf-8');
    assert.ok(headerContent.includes('/demo/explorer'), 'Header.tsx provides quick link to Demo Centre');

    const sidebarPath = path.join(srcDir, 'components', 'layout', 'Sidebar.tsx');
    const sidebarContent = fs.readFileSync(sidebarPath, 'utf-8');
    assert.ok(sidebarContent.includes('/demo/explorer'), 'Sidebar.tsx provides Judge Demo Centre link');
  });
});
