import { test, describe } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — EVC Expert Integrity, COI Engine & Mobile Field Evidence UI', () => {

  test('1. MobileFieldInspectionPage component exists and provides mobile-first inspection features', () => {
    const filePath = path.join(srcDir, 'pages', 'officer', 'MobileFieldInspectionPage.tsx');
    assert.ok(fs.existsSync(filePath), 'MobileFieldInspectionPage.tsx must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('export const MobileFieldInspectionPage'), 'Exports MobileFieldInspectionPage');
    assert.ok(content.includes('navigator.geolocation'), 'Integrates browser geolocation for visit check-in');
    assert.ok(content.includes('MANUAL_OFFICER_OVERRIDE'), 'Provides manual fallback when geolocation is denied');
    assert.ok(content.includes('DEFAULT_CHECKLIST_ITEMS'), 'Includes canonical APH checklist items');
    assert.ok(content.includes('SHA-256'), 'Displays SHA-256 integrity hash for evidence artifacts');
    assert.ok(content.includes('Statutory Decision Exclusivity Invariant'), 'Enforces Competent Authority approval exclusivity disclaimer');
    assert.ok(content.includes('api.finalizeEVCReport'), 'Calls finalize report API endpoint');
  });

  test('2. EVCCoordinatorWorkspace integrates structured expert selection and explainable COI engine', () => {
    const filePath = path.join(srcDir, 'pages', 'officer', 'EVCCoordinatorWorkspace.tsx');
    assert.ok(fs.existsSync(filePath), 'EVCCoordinatorWorkspace.tsx must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('api.getEVCExperts'), 'Loads expert registry from API');
    assert.ok(content.includes('api.checkEVCCOI'), 'Calls explainable COI check endpoint');
    assert.ok(content.includes('Explainable Conflict-of-Interest (COI) Assessment'), 'Exposes explainable COI assessment modal');
    assert.ok(content.includes('/officer/evc/field/'), 'Provides direct link to Mobile Field Workspace');
    assert.ok(content.includes('REASSIGNMENT_REQUIRED'), 'Highlights inspections requiring member reassignment');
  });

  test('3. EVCQueue integrates Mobile Field Workspace navigation', () => {
    const filePath = path.join(srcDir, 'pages', 'officer', 'EVCQueue.tsx');
    assert.ok(fs.existsSync(filePath), 'EVCQueue.tsx must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('/officer/evc/field/'), 'Links to mobile field inspection workspace');
    assert.ok(content.includes('Camera'), 'Features camera icon for field inspection');
  });

  test('4. Frontend types export EVCExpert, COICheckResult, EVCPanelAssignment, EVCFieldEvidence', () => {
    const filePath = path.join(srcDir, 'types', 'index.ts');
    assert.ok(fs.existsSync(filePath), 'types/index.ts must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes('export interface EVCExpert'), 'Exports EVCExpert interface');
    assert.ok(content.includes('export interface COICheckResult'), 'Exports COICheckResult interface');
    assert.ok(content.includes('export interface COIRuleResult'), 'Exports COIRuleResult interface');
    assert.ok(content.includes('export interface EVCPanelAssignment'), 'Exports EVCPanelAssignment interface');
    assert.ok(content.includes('export interface EVCFieldEvidence'), 'Exports EVCFieldEvidence interface');
    assert.ok(content.includes('panel_status?:'), 'EVCInspection includes panel_status');
    assert.ok(content.includes('check_in_lat?:'), 'EVCInspection includes check_in_lat');
    assert.ok(content.includes('virtual_meeting_url?:'), 'EVCInspection includes virtual_meeting_url');
  });

  test('5. API client exposes full extended EVC API contract', () => {
    const filePath = path.join(srcDir, 'api', 'client.ts');
    assert.ok(fs.existsSync(filePath), 'api/client.ts must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    const expectedMethods = [
      'getEVCExperts',
      'getEVCExpert',
      'checkEVCCOI',
      'proposeEVCAssignment',
      'inviteEVCAssignment',
      'acceptEVCAssignment',
      'declineEVCAssignment',
      'reassignEVCAssignment',
      'checkInEVC',
      'recordEVCFieldEvidence',
      'getEVCFieldEvidence',
      'finalizeEVCReport',
      'getEVCDossier'
    ];

    for (const method of expectedMethods) {
      assert.ok(content.includes(`${method}:`), `API client must expose '${method}' method`);
    }
  });

  test('6. App.tsx mounts MobileFieldInspectionPage routes', () => {
    const filePath = path.join(srcDir, 'App.tsx');
    assert.ok(fs.existsSync(filePath), 'App.tsx must exist');
    const content = fs.readFileSync(filePath, 'utf-8');

    assert.ok(content.includes("import { MobileFieldInspectionPage } from './pages/officer/MobileFieldInspectionPage'"), 'Imports MobileFieldInspectionPage');
    assert.ok(content.includes('path="/officer/evc/field/:id"'), 'Routes /officer/evc/field/:id');
    assert.ok(content.includes('path="/officer/evc/inspections/:id"'), 'Routes /officer/evc/inspections/:id');
  });
});
