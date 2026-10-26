import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — Statutory Decision Orders & QR Integrity Verification UI', () => {

  it('1. StatutoryOrderModal component exists and provides full order dossier & integrity details', () => {
    const modalPath = path.join(srcDir, 'components', 'common', 'StatutoryOrderModal.tsx');
    assert.ok(fs.existsSync(modalPath), 'StatutoryOrderModal.tsx must exist');

    const modalContent = fs.readFileSync(modalPath, 'utf-8');
    assert.match(modalContent, /export const StatutoryOrderModal/, 'Must export StatutoryOrderModal');
    assert.match(modalContent, /order_number/, 'Must render order number');
    assert.match(modalContent, /checksum_sha256/, 'Must display SHA-256 checksum');
    assert.match(modalContent, /verification_token/, 'Must display verification token');
    assert.match(modalContent, /signature_status/, 'Must render signature status badge');
    assert.match(modalContent, /Download PDF Order/i, 'Must feature PDF download action');
    assert.match(modalContent, /Public Verification/i, 'Must feature public verification link');
  });

  it('2. Prototype Signature State and IT Act 2000 disclosure is explicitly enforced in UI', () => {
    const modalContent = fs.readFileSync(path.join(srcDir, 'components', 'common', 'StatutoryOrderModal.tsx'), 'utf-8');
    assert.match(modalContent, /UNSIGNED_PROTOTYPE/, 'Must enforce UNSIGNED_PROTOTYPE status state');
    assert.match(modalContent, /signature_disclaimer|Prototype Notice/i, 'Must feature prototype regulatory disclaimer');

    const publicVerifPath = path.join(srcDir, 'pages', 'PublicOrderVerification.tsx');
    const publicContent = fs.readFileSync(publicVerifPath, 'utf-8');
    assert.match(publicContent, /UNSIGNED_PROTOTYPE/, 'Public verification must disclose prototype signature state');
    assert.match(publicContent, /QR code establishes document reference provenance/i, 'Must explain QR is not legal cryptographic certificate');
  });

  it('3. PublicOrderVerification page exists with token verification and file checksum validation', () => {
    const pagePath = path.join(srcDir, 'pages', 'PublicOrderVerification.tsx');
    assert.ok(fs.existsSync(pagePath), 'PublicOrderVerification.tsx must exist');

    const content = fs.readFileSync(pagePath, 'utf-8');
    assert.match(content, /export const PublicOrderVerification/, 'Must export PublicOrderVerification');
    assert.match(content, /verifyOrderByToken/, 'Must call verifyOrderByToken');
    assert.match(content, /verifyOrderUpload/, 'Must call verifyOrderUpload for physical file checks');
    assert.match(content, /VERIFIED_AUTHENTIC/, 'Must handle VERIFIED_AUTHENTIC state');
    assert.match(content, /TAMPERED_HASH_MISMATCH/, 'Must handle TAMPERED_HASH_MISMATCH state');
    assert.match(content, /REVOKED/, 'Must handle REVOKED state');
    assert.match(content, /SUPERSEDED/, 'Must handle SUPERSEDED state');
  });

  it('4. App.tsx registers unauthenticated public verification routes', () => {
    const appPath = path.join(srcDir, 'App.tsx');
    const appContent = fs.readFileSync(appPath, 'utf-8');
    assert.match(appContent, /PublicOrderVerification/, 'App.tsx must import PublicOrderVerification');
    assert.match(appContent, /path="\/verify-order"/, 'Must register /verify-order route');
    assert.match(appContent, /path="\/verify-order\/:token"/, 'Must register /verify-order/:token route');
  });

  it('5. API client exposes full statutory orders API contract', () => {
    const clientPath = path.join(srcDir, 'api', 'client.ts');
    const content = fs.readFileSync(clientPath, 'utf-8');
    assert.match(content, /export const ordersApi/, 'Must export ordersApi');
    assert.match(content, /generateOrder:/, 'Must expose generateOrder');
    assert.match(content, /revokeOrder:/, 'Must expose revokeOrder');
    assert.match(content, /getOrdersByApplication:/, 'Must expose getOrdersByApplication');
    assert.match(content, /verifyOrderByToken:/, 'Must expose verifyOrderByToken');
    assert.match(content, /verifyOrderUpload:/, 'Must expose verifyOrderUpload');
    assert.match(content, /getOrderDownloadUrl:/, 'Must expose getOrderDownloadUrl');
  });

  it('6. Frontend types define StatutoryOrderData and PublicVerification schemas', () => {
    const typesPath = path.join(srcDir, 'types', 'index.ts');
    const content = fs.readFileSync(typesPath, 'utf-8');
    assert.match(content, /export interface StatutoryOrderData/, 'Must export StatutoryOrderData');
    assert.match(content, /export interface StatutoryOrderPublicVerificationData/, 'Must export StatutoryOrderPublicVerificationData');
    assert.match(content, /export interface OrderArtifactVerifyUploadData/, 'Must export OrderArtifactVerifyUploadData');
  });

  it('7. Role workspaces integrate StatutoryOrderModal for decision and order access', () => {
    const caPath = path.join(srcDir, 'pages', 'officer', 'CompetentAuthorityWorkspace.tsx');
    const caContent = fs.readFileSync(caPath, 'utf-8');
    assert.match(caContent, /StatutoryOrderModal/, 'CompetentAuthorityWorkspace must import StatutoryOrderModal');
    assert.match(caContent, /Order Artifact/, 'Must provide Order Artifact button');

    const officerPath = path.join(srcDir, 'pages', 'officer', 'OfficerApplicationDetail.tsx');
    const officerContent = fs.readFileSync(officerPath, 'utf-8');
    assert.match(officerContent, /StatutoryOrderModal/, 'OfficerApplicationDetail must import StatutoryOrderModal');

    const instPath = path.join(srcDir, 'pages', 'institution', 'ApplicationDetail.tsx');
    const instContent = fs.readFileSync(instPath, 'utf-8');
    assert.match(instContent, /StatutoryOrderModal/, 'Institution ApplicationDetail must import StatutoryOrderModal');
    assert.match(instContent, /View Official Statutory Order/i, 'Must expose statutory order viewing action for approved/rejected applications');
  });

});
