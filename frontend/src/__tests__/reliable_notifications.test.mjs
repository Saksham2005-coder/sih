import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const srcDir = path.resolve(__dirname, '..');

describe('ReguFlow 360 — Reliable Notification Delivery & Event Outbox UI', () => {

  it('1. NotificationOutboxPage component exists and renders channel health, metrics, and outbox ledger', () => {
    const pagePath = path.join(srcDir, 'pages', 'officer', 'NotificationOutboxPage.tsx');
    assert.ok(fs.existsSync(pagePath), 'NotificationOutboxPage.tsx must exist');

    const content = fs.readFileSync(pagePath, 'utf-8');
    assert.match(content, /export const NotificationOutboxPage/, 'Must export NotificationOutboxPage');
    assert.match(content, /getNotificationOutbox/, 'Must call getNotificationOutbox');
    assert.match(content, /getOutboxSummary/, 'Must call getOutboxSummary');
    assert.match(content, /getNotificationChannelsStatus/, 'Must call getNotificationChannelsStatus');
    assert.match(content, /retryOutboxItem/, 'Must provide retry action');
    assert.match(content, /triggerOutboxDispatch/, 'Must provide batch dispatch trigger');
    assert.match(content, /ACCEPTED_BY_PROVIDER/, 'Must display ACCEPTED_BY_PROVIDER status badge');
    assert.match(content, /SIMULATED/, 'Must display SIMULATED status badge');
    assert.match(content, /NOT_CONFIGURED/, 'Must display NOT_CONFIGURED status badge');
    assert.match(content, /DEAD_LETTER/, 'Must display DEAD_LETTER status badge');
    assert.match(content, /RETRY_SCHEDULED/, 'Must display RETRY_SCHEDULED status badge');
  });

  it('2. Header component connects to real-time Server-Sent Events (SSE) with fallback polling', () => {
    const headerPath = path.join(srcDir, 'components', 'layout', 'Header.tsx');
    assert.ok(fs.existsSync(headerPath), 'Header.tsx must exist');

    const content = fs.readFileSync(headerPath, 'utf-8');
    assert.match(content, /EventSource/, 'Header must establish EventSource connection');
    assert.match(content, /\/api\/notifications\/stream/, 'Must connect to /api/notifications/stream SSE endpoint');
    assert.match(content, /getNotificationUnreadCount/, 'Must use getNotificationUnreadCount for polling fallback');
    assert.match(content, /isSseActive/, 'Must track SSE active connection state');
    assert.match(content, /liveToast/, 'Must maintain live toast state for real-time events');
    assert.match(content, /\/officer\/notifications\/outbox/, 'Must link to Notification Outbox in notification drawer');
  });

  it('3. Types export complete NotificationOutbox and channel contracts', () => {
    const typesPath = path.join(srcDir, 'types', 'index.ts');
    const content = fs.readFileSync(typesPath, 'utf-8');

    assert.match(content, /export interface NotificationOutboxItem/, 'Must export NotificationOutboxItem');
    assert.match(content, /idempotency_key/, 'Must include idempotency_key');
    assert.match(content, /correlation_id/, 'Must include correlation_id');
    assert.match(content, /export interface NotificationOutboxSummary/, 'Must export NotificationOutboxSummary');
    assert.match(content, /export interface NotificationChannelStatus/, 'Must export NotificationChannelStatus');
    assert.match(content, /export interface ChannelHealthStatus/, 'Must export ChannelHealthStatus');
    assert.match(content, /export interface LiveSSEEventSummary/, 'Must export LiveSSEEventSummary');
  });

  it('4. API client exposes full outbox and live channel methods', () => {
    const clientPath = path.join(srcDir, 'api', 'client.ts');
    const content = fs.readFileSync(clientPath, 'utf-8');

    assert.match(content, /getNotificationOutbox:/, 'Must expose getNotificationOutbox');
    assert.match(content, /getOutboxSummary:/, 'Must expose getOutboxSummary');
    assert.match(content, /retryOutboxItem:/, 'Must expose retryOutboxItem');
    assert.match(content, /triggerOutboxDispatch:/, 'Must expose triggerOutboxDispatch');
    assert.match(content, /getNotificationChannelsStatus:/, 'Must expose getNotificationChannelsStatus');
    assert.match(content, /getNotificationUnreadCount:/, 'Must expose getNotificationUnreadCount');
  });

  it('5. App.tsx and Sidebar.tsx wire up /officer/notifications/outbox navigation', () => {
    const appPath = path.join(srcDir, 'App.tsx');
    const appContent = fs.readFileSync(appPath, 'utf-8');
    assert.match(appContent, /NotificationOutboxPage/, 'App.tsx must import NotificationOutboxPage');
    assert.match(appContent, /path="\/officer\/notifications\/outbox"/, 'App.tsx must register /officer/notifications/outbox route');

    const sidebarPath = path.join(srcDir, 'components', 'layout', 'Sidebar.tsx');
    const sidebarContent = fs.readFileSync(sidebarPath, 'utf-8');
    assert.match(sidebarContent, /\/officer\/notifications\/outbox/, 'Sidebar must link to /officer/notifications/outbox');
  });
});
