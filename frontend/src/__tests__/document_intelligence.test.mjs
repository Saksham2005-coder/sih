import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — Document Intelligence & Evidence Verification UI', () => {

  it('1. DocumentIntelligenceModal component exists and provides full regulatory telemetry', () => {
    const modalPath = path.join(srcDir, 'components', 'common', 'DocumentIntelligenceModal.tsx');
    assert.ok(fs.existsSync(modalPath), 'DocumentIntelligenceModal.tsx must exist');

    const modalContent = fs.readFileSync(modalPath, 'utf-8');
    assert.match(modalContent, /export const DocumentIntelligenceModal/, 'Must export DocumentIntelligenceModal');
    assert.match(modalContent, /extraction_engine/, 'Must render extraction engine telemetry');
    assert.match(modalContent, /ocr_provider/, 'Must render local OCR provider status');
    assert.match(modalContent, /overall_confidence/, 'Must render extraction reliability score');
    assert.match(modalContent, /has_text_layer/, 'Must render text layer vs scanned detection');
  });

  it('2. Cross-check finding status classifications adhere to canonical regulatory labels', () => {
    const modalContent = fs.readFileSync(path.join(srcDir, 'components', 'common', 'DocumentIntelligenceModal.tsx'), 'utf-8');
    assert.match(modalContent, /MATCH/, 'Must handle MATCH status');
    assert.match(modalContent, /POSSIBLE_MISMATCH/, 'Must handle POSSIBLE_MISMATCH status');
    assert.match(modalContent, /MISSING_EVIDENCE/, 'Must handle MISSING_EVIDENCE status');
    assert.match(modalContent, /EXTRACTION_UNAVAILABLE/, 'Must handle EXTRACTION_UNAVAILABLE status');
    assert.match(modalContent, /source_excerpt/, 'Must display supporting source excerpt');
    assert.match(modalContent, /source_page/, 'Must display source page index');
  });

  it('3. Officer Statutory Decision Desk exposes authorized decisioning and non-automation controls', () => {
    const modalContent = fs.readFileSync(path.join(srcDir, 'components', 'common', 'DocumentIntelligenceModal.tsx'), 'utf-8');
    assert.match(modalContent, /CONFIRMED/, 'Must support CONFIRMED decision');
    assert.match(modalContent, /CORRECTED/, 'Must support CORRECTED decision');
    assert.match(modalContent, /REJECTED/, 'Must support REJECTED decision');
    assert.match(modalContent, /applyToRecord|apply_to_record/, 'Must require explicit apply to record toggle');
    assert.match(modalContent, /reviewer_remarks|remarks/, 'Must mandate reviewer remarks');
    assert.match(modalContent, /Under AICTE PS 26262/i, 'Must feature non-automation statutory notice');
  });

  it('4. DocumentsRenewals integrates Document Intelligence scan and version inspection', () => {
    const renewalsPath = path.join(srcDir, 'pages', 'institution', 'DocumentsRenewals.tsx');
    const content = fs.readFileSync(renewalsPath, 'utf-8');
    assert.match(content, /DocumentIntelligenceModal/, 'DocumentsRenewals must import DocumentIntelligenceModal');
    assert.match(content, /Intelligence Scan/, 'Must expose Intelligence Scan action');
    assert.match(content, /Inspect Intelligence/, 'Must expose version inspection action');
  });

  it('5. RegionalOfficerWorkspace integrates Document Intelligence & Cross-Check Desk', () => {
    const roPath = path.join(srcDir, 'pages', 'officer', 'RegionalOfficerWorkspace.tsx');
    const content = fs.readFileSync(roPath, 'utf-8');
    assert.match(content, /DocumentIntelligenceModal/, 'RegionalOfficerWorkspace must import DocumentIntelligenceModal');
    assert.match(content, /Document Intelligence & Regulatory Cross-Check Desk/, 'Must feature dedicated verification desk');
    assert.match(content, /Intelligence Review/, 'Must provide Intelligence Review button for regional officers');
  });

  it('6. API client exposes full document intelligence contract', () => {
    const clientPath = path.join(srcDir, 'api', 'client.ts');
    const content = fs.readFileSync(clientPath, 'utf-8');
    assert.match(content, /getDocumentAnalyses/, 'Must export getDocumentAnalyses');
    assert.match(content, /getDocumentAnalysisByVersion/, 'Must export getDocumentAnalysisByVersion');
    assert.match(content, /triggerDocumentAnalysis/, 'Must export triggerDocumentAnalysis');
    assert.match(content, /reviewDocumentAnalysis/, 'Must export reviewDocumentAnalysis');
  });

});
