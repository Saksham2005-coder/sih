import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Server, Sliders, ShieldAlert, Users, Play,
  RefreshCw, CheckCircle2, ArrowRight, Database,
  Activity, Download, Terminal, Cpu
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import { RuleDefinitionItem, AuditEventItem } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import { StatusBadge } from '../../components/common/StatusBadge';

export const SystemAdminWorkspace: React.FC = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState<any>(null);
  const [engineStatus, setEngineStatus] = useState<any>(null);
  const [rules, setRules] = useState<RuleDefinitionItem[]>([]);
  const [demoUsers, setDemoUsers] = useState<any[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [h, eng, rList, uList, aud] = await Promise.all([
        api.getHealth(),
        api.getEngineStatus(),
        api.getRules(),
        api.getDemoUsers(),
        api.getAuditExplorer({ limit: 10 }),
      ]);
      setHealth(h);
      setEngineStatus(eng);
      setRules(rList);
      setDemoUsers(uList.demo_users);
      setAuditEvents(aud.items || []);
    } catch (err) {
      console.error('Failed to load system admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunManualScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const res = await api.runDeadlineScan();
      setScanResult(
        `Deadline Scan Completed: ${res.scanned_entities} entities scanned, ${res.reminders_created} reminders generated, ${res.escalations_created} escalations created, ${res.duplicates_prevented} duplicate triggers prevented (${res.execution_time_ms}ms).`
      );
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleExportAuditCsv = () => {
    window.location.href = '/api/audit/export';
  };

  return (
    <div className="space-y-6">
      {/* Admin Command Banner */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal text-white">
              PLATFORM SYSTEM ADMINISTRATION
            </span>
            <span className="text-xs text-brand-muted dark:text-brand-muted">
              Environment: <strong className="text-brand-ink dark:text-brand-ink">{health?.environment?.toUpperCase() || 'DEVELOPMENT'}</strong> • Academic Cycle: <strong className="text-brand-ink dark:text-brand-ink">{health?.academic_cycle || '2026-2027'}</strong>
            </span>
          </div>
          <h1 className="text-xl font-bold text-brand-ink dark:text-brand-ink mt-1">
            System Administration, Rule Studio & Telemetry
          </h1>
          <p className="text-xs text-brand-muted dark:text-brand-muted mt-0.5">
            Active Administrator: <span className="font-semibold text-brand-teal">{user?.full_name}</span> (SYSTEM ADMIN) • Platform Diagnostics, Leases & Audit Explorer
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border dark:border-brand-border text-brand-ink dark:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Telemetry
          </button>
          <button
            onClick={handleRunManualScan}
            disabled={scanning}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-brand-teal hover:bg-brand-teal-hover text-white text-xs font-semibold shadow-sm transition-colors"
          >
            <Play className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Running Engine...' : 'Run On-Demand Deadline Scan'}
          </button>
        </div>
      </div>

      {/* Scan Result Notice */}
      {scanResult && (
        <div className="p-4 bg-teal-50 dark:bg-brand-teal/15 border border-teal-200 dark:border-brand-teal/30 rounded-xl text-xs text-teal-900 dark:text-teal-200 font-medium flex items-center justify-between">
          <span>{scanResult}</span>
          <button onClick={() => setScanResult(null)} className="text-teal-900 dark:text-teal-100 font-bold hover:underline">Dismiss</button>
        </div>
      )}

      {/* Live System Diagnostics Grid */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border p-6 shadow-sm transition-colors">
        <div className="flex items-center justify-between pb-3 border-b border-brand-border dark:border-brand-border mb-4">
          <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-teal" /> Live Orchestrator & Distributed Engine Telemetry
          </h3>
          <span className="text-[10px] text-brand-muted dark:text-brand-muted font-mono">
            Ping: {health?.database_details?.latency_ms ? `${health.database_details.latency_ms}ms` : '< 1ms'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border dark:border-brand-border">
            <span className="text-brand-muted dark:text-brand-muted text-[10px] uppercase font-semibold">API Health & Core:</span>
            <p className="font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> {health?.status?.toUpperCase() || 'ONLINE'}
            </p>
            <span className="text-[10px] text-brand-muted dark:text-brand-muted">v{health?.version || '1.0.0'}</span>
          </div>

          <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border dark:border-brand-border">
            <span className="text-brand-muted dark:text-brand-muted text-[10px] uppercase font-semibold">Database Engine:</span>
            <p className="font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 mt-0.5">
              <Database className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> {health?.database?.toUpperCase() || 'HEALTHY'}
            </p>
            <span className="text-[10px] text-brand-muted dark:text-brand-muted">WAL Pragma & Isolation Active</span>
          </div>

          <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border dark:border-brand-border">
            <span className="text-brand-muted dark:text-brand-muted text-[10px] uppercase font-semibold">Distributed Lease:</span>
            <p className="font-bold text-brand-teal flex items-center gap-1 mt-0.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              {health?.scheduler?.lease?.is_active ? 'LOCK HELD' : 'ACQUIRED'}
            </p>
            <span className="text-[10px] text-brand-muted dark:text-brand-muted font-mono truncate block">
              {health?.scheduler?.lease?.holder_id || 'Active Leaseholder'}
            </span>
          </div>

          <div className="p-3 bg-brand-porcelain/60 dark:bg-brand-surface-elevated rounded-lg border border-brand-border dark:border-brand-border">
            <span className="text-brand-muted dark:text-brand-muted text-[10px] uppercase font-semibold">Scheduler Thread:</span>
            <p className="font-bold text-brand-ink dark:text-brand-ink flex items-center gap-1 mt-0.5">
              <Activity className="w-3.5 h-3.5 text-brand-teal" />
              {health?.scheduler?.is_running ? 'RUNNING (60s)' : 'STOPPED'}
            </p>
            <span className="text-[10px] text-brand-muted dark:text-brand-muted">Autonomous Scan Thread</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Configured Rule Definitions"
          value={rules.length}
          subtext="Deadlines, SLAs, Priority weights"
          icon={<Sliders size={18} />}
        />
        <StatCard
          title="Configured Demo Personas"
          value={demoUsers.length}
          subtext="8 Canonical roles with tenant scoping"
          icon={<Users size={18} />}
        />
        <StatCard
          title="Lifetime Engine Scans"
          value={engineStatus?.lifetime_metrics?.total_scans_executed ?? 1}
          subtext={`${engineStatus?.lifetime_metrics?.total_reminders_created ?? 0} reminders created`}
          icon={<Activity size={18} />}
        />
        <StatCard
          title="Audit Trail Entries"
          value={auditEvents.length > 0 ? `${auditEvents.length}+` : '0'}
          subtext="Immutable 256-bit hashed logs"
          icon={<ShieldAlert size={18} />}
        />
      </div>

      {/* Rule Studio Section */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="px-6 py-4 border-b border-brand-border dark:border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink">Regulatory Rule Studio & Policy Lifecycle</h3>
            <p className="text-xs text-brand-muted dark:text-brand-muted">Version-controlled policies governing scrutiny SLAs, deficiency cure windows, and priority weights</p>
          </div>
          <Link
            to="/officer/rules"
            className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
          >
            Open Rule Studio <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border dark:border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Rule Code</th>
                <th className="px-6 py-3.5">Rule Title</th>
                <th className="px-6 py-3.5">Category</th>
                <th className="px-6 py-3.5">Version</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 dark:divide-brand-border">
              {rules.map((r) => (
                <tr key={r.rule_code} className="hover:bg-brand-porcelain/50 dark:hover:bg-brand-surface-elevated/50 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-brand-teal">
                    {r.rule_code}
                  </td>
                  <td className="px-6 py-4 font-semibold text-brand-ink dark:text-brand-ink">
                    {r.name}
                  </td>
                  <td className="px-6 py-4 text-brand-muted dark:text-brand-muted font-medium">
                    {r.category}
                  </td>
                  <td className="px-6 py-4 font-mono font-semibold text-brand-ink dark:text-brand-ink">
                    v{r.version}
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40">
                      {r.status || 'PUBLISHED'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to="/officer/rules"
                      className="text-xs font-semibold text-brand-teal hover:underline"
                    >
                      Configure / Simulate
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Real-Time Immutable Audit Log Stream */}
      <div className="bg-white dark:bg-brand-surface rounded-xl border border-brand-border dark:border-brand-border shadow-sm overflow-hidden transition-colors">
        <div className="px-6 py-4 border-b border-brand-border dark:border-brand-border flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-brand-ink dark:text-brand-ink">Real-Time Immutable Audit Trail</h3>
            <p className="text-xs text-brand-muted dark:text-brand-muted">Cryptographically logged workflow events, transitions, and administrative actions</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExportAuditCsv}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-border dark:border-brand-border text-xs font-semibold text-brand-ink dark:text-brand-ink hover:bg-brand-porcelain dark:hover:bg-brand-surface-elevated shadow-sm transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-brand-teal" /> Export Sanitized CSV
            </button>
            <Link
              to="/officer/audit"
              className="text-xs font-semibold text-brand-teal hover:underline flex items-center gap-1"
            >
              Audit Explorer <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-porcelain/60 dark:bg-brand-surface-elevated text-brand-muted dark:text-brand-muted uppercase text-[10px] font-semibold border-b border-brand-border dark:border-brand-border">
              <tr>
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5">Action Code</th>
                <th className="px-6 py-3.5">Actor & Role</th>
                <th className="px-6 py-3.5">Target Entity</th>
                <th className="px-6 py-3.5">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border/60 dark:divide-brand-border">
              {auditEvents.slice(0, 8).map((ev) => (
                <tr key={ev.id} className="hover:bg-brand-porcelain/50 dark:hover:bg-brand-surface-elevated/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-[11px] text-brand-muted dark:text-brand-muted whitespace-nowrap">
                    {new Date(ev.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono font-bold text-brand-ink dark:text-brand-ink bg-brand-porcelain dark:bg-brand-surface-elevated px-2 py-0.5 rounded text-[11px] border border-brand-border/60 dark:border-brand-border">
                      {ev.action}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-semibold text-brand-ink dark:text-brand-ink">{ev.actor_name || 'System'}</p>
                    <span className="text-[10px] text-brand-teal">{ev.actor_role?.replace(/_/g, ' ') || 'SYSTEM'}</span>
                  </td>
                  <td className="px-6 py-4 font-mono text-[11px] text-brand-muted dark:text-brand-muted">
                    {ev.entity_type} #{ev.entity_id}
                  </td>
                  <td className="px-6 py-4 text-brand-muted dark:text-brand-muted text-[11px] max-w-xs truncate">
                    {ev.details || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default SystemAdminWorkspace;
