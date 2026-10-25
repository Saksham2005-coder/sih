import React, { useEffect, useState } from 'react';
import {
  Sliders, Edit3, ShieldAlert, CheckCircle2, History,
  Play, AlertCircle, Info, RefreshCw, Check
} from 'lucide-react';
import { api } from '../../api/client';
import {
  RuleDefinitionItem, RuleVersionHistoryItem,
  RuleValidateResponse, RuleSimulateResponse
} from '../../types';
import { Modal } from '../../components/common/Modal';

export const RuleStudioPage: React.FC = () => {
  const [rules, setRules] = useState<RuleDefinitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRule, setSelectedRule] = useState<RuleDefinitionItem | null>(null);

  // Edit / Publish Modal
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [configJson, setConfigJson] = useState('');
  const [version, setVersion] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Validation state
  const [validationResult, setValidationResult] = useState<RuleValidateResponse | null>(null);
  const [validating, setValidating] = useState(false);

  // Simulation state
  const [simModalOpen, setSimModalOpen] = useState(false);
  const [simResult, setSimResult] = useState<RuleSimulateResponse | null>(null);
  const [simulating, setSimulating] = useState(false);

  // History state
  const [historyModalOpen, setHistoryModalOpen] = useState(false);
  const [versionHistory, setVersionHistory] = useState<RuleVersionHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadRules = async () => {
    try {
      const data = await api.getRules();
      setRules(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleOpenEdit = (rule: RuleDefinitionItem) => {
    setSelectedRule(rule);
    try {
      const parsed = JSON.parse(rule.config_json);
      setConfigJson(JSON.stringify(parsed, null, 2));
    } catch {
      setConfigJson(rule.config_json);
    }
    // Increment minor version suggestion
    const parts = rule.version.split('.');
    if (parts.length === 3) {
      setVersion(`${parts[0]}.${parseInt(parts[1]) + 1}.0`);
    } else {
      setVersion('1.1.0');
    }
    setChangeReason('');
    setValidationResult(null);
    setEditModalOpen(true);
  };

  const handleValidateConfig = async () => {
    if (!selectedRule) return;
    setValidating(true);
    setValidationResult(null);
    try {
      const res = await api.validateRule(selectedRule.rule_code, configJson);
      setValidationResult(res);
    } catch (err: any) {
      alert(err.message || 'Validation request failed');
    } finally {
      setValidating(false);
    }
  };

  const handlePublishRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRule) return;
    setSubmitting(true);
    try {
      await api.publishRule(selectedRule.rule_code, {
        config_json: configJson,
        version: version || '1.1.0',
        change_reason: changeReason || 'Regulatory parameter revision'
      });
      setEditModalOpen(false);
      loadRules();
    } catch (err: any) {
      alert(err.message || 'Failed to publish rule version');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenSimulate = async (rule: RuleDefinitionItem) => {
    setSelectedRule(rule);
    setSimulating(true);
    setSimResult(null);
    setSimModalOpen(true);
    try {
      const res = await api.simulateRule(rule.rule_code, { config_json: rule.config_json });
      setSimResult(res);
    } catch (err: any) {
      alert(err.message || 'Simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  const handleOpenHistory = async (rule: RuleDefinitionItem) => {
    setSelectedRule(rule);
    setLoadingHistory(true);
    setHistoryModalOpen(true);
    try {
      const hist = await api.getRuleHistory(rule.rule_code);
      setVersionHistory(hist);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-brand-ink">Rule Studio & Policy Governance</h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-[#C5892B] border border-amber-300">
              Illustrative Demo Rules
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-brand-teal border border-teal-300">
              Versioned Ledger
            </span>
          </div>
          <p className="text-xs text-brand-muted mt-0.5">
            Deterministic regulatory SLA thresholds, reminder offsets, escalation tiers, and explainable priority policies
          </p>
        </div>

        <button
          onClick={loadRules}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-brand-border text-brand-ink hover:bg-gray-50 text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Rules
        </button>
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {rules.map((rule) => {
          let parsedConfig: any = {};
          try {
            parsedConfig = JSON.parse(rule.config_json);
          } catch {
            parsedConfig = {};
          }

          return (
            <div
              key={rule.id}
              className="bg-white rounded-xl border border-brand-border p-6 shadow-sm hover:border-brand-teal/50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 pb-3 border-b border-brand-border mb-3">
                  <div>
                    <span className="text-[10px] font-bold text-brand-muted uppercase tracking-wider">
                      [{rule.category}]
                    </span>
                    <h3 className="text-sm font-bold text-brand-ink mt-0.5">{rule.name}</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-brand-ink border border-gray-200">
                      v{rule.version}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${rule.status === 'PUBLISHED' ? 'bg-teal-50 text-brand-teal border border-teal-200' : 'bg-gray-100 text-brand-muted'}`}>
                      {rule.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-brand-muted mb-3">
                  {rule.description || 'Configurable regulatory rule defining timeline and operational threshold limits.'}
                </p>

                <div className="p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border text-xs font-mono space-y-1 max-h-48 overflow-y-auto">
                  {Object.entries(parsedConfig).map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2">
                      <span className="text-brand-muted shrink-0">{k}:</span>
                      <span className="font-semibold text-brand-ink truncate text-right">
                        {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between text-[10px] text-gray-400 mt-3">
                  <span>Rule Code: <strong className="font-mono text-brand-ink">{rule.rule_code}</strong></span>
                  {rule.change_reason && (
                    <span className="italic truncate max-w-[200px]" title={rule.change_reason}>
                      "{rule.change_reason}"
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleOpenHistory(rule)}
                    className="px-2.5 py-1.5 rounded-lg border border-brand-border text-brand-muted hover:text-brand-ink hover:bg-gray-50 text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                    title="View historical versions"
                  >
                    <History className="w-3.5 h-3.5" /> History
                  </button>
                  <button
                    onClick={() => handleOpenSimulate(rule)}
                    className="px-2.5 py-1.5 rounded-lg border border-brand-border text-brand-teal hover:bg-teal-50 text-xs font-semibold inline-flex items-center gap-1 transition-colors"
                    title="Dry-run simulation"
                  >
                    <Play className="w-3.5 h-3.5" /> Test Simulation
                  </button>
                </div>

                <button
                  onClick={() => handleOpenEdit(rule)}
                  className="px-3 py-1.5 rounded-lg bg-brand-teal text-white hover:bg-brand-teal-dark text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5" /> Modify & Publish
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Edit & Publish Version Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Modify & Publish Rule Version"
        subtitle={selectedRule?.name || ''}
      >
        <form onSubmit={handlePublishRule} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
                New Target Version
              </label>
              <input
                type="text"
                required
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.1.0"
                className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
              />
            </div>
            <div>
              <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
                Current Active Version
              </label>
              <input
                type="text"
                disabled
                value={`v${selectedRule?.version || '1.0.0'} (Active)`}
                className="w-full border border-gray-200 bg-gray-50 rounded-lg p-2 text-xs text-brand-muted"
              />
            </div>
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Audit Change Reason & Regulatory Reference
            </label>
            <input
              type="text"
              required
              value={changeReason}
              onChange={(e) => setChangeReason(e.target.value)}
              placeholder="e.g. APH 2026 Chapter 4 SLA revision approved by AICTE Committee"
              className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider">
                Configuration Payload (JSON)
              </label>
              <button
                type="button"
                onClick={handleValidateConfig}
                disabled={validating}
                className="text-[10px] font-bold text-brand-teal hover:underline flex items-center gap-1"
              >
                <Check className="w-3 h-3" /> {validating ? 'Validating...' : 'Validate Schema'}
              </button>
            </div>
            <textarea
              rows={8}
              required
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              className="w-full font-mono text-xs border border-brand-border rounded-lg p-3 bg-brand-porcelain/60 focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          {/* Validation Feedback Banner */}
          {validationResult && (
            <div className={`p-3 rounded-lg border text-xs ${validationResult.valid ? 'bg-teal-50 border-teal-200 text-teal-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
              <div className="flex items-center gap-1.5 font-bold">
                {validationResult.valid ? <CheckCircle2 className="w-4 h-4 text-teal-700" /> : <AlertCircle className="w-4 h-4 text-red-700" />}
                {validationResult.valid ? 'Configuration Syntax & Schema Valid' : 'Validation Errors Detected'}
              </div>
              {validationResult.errors.length > 0 && (
                <ul className="mt-1.5 list-disc list-inside space-y-0.5 text-[11px]">
                  {validationResult.errors.map((err, i) => <li key={i}>{err}</li>)}
                </ul>
              )}
              {validationResult.warnings.length > 0 && (
                <ul className="mt-1 list-disc list-inside space-y-0.5 text-[11px] text-amber-800">
                  {validationResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={() => setEditModalOpen(false)}
              className="px-3 py-1.5 rounded-lg border border-brand-border text-brand-muted hover:bg-gray-50 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 rounded-lg bg-brand-ink text-white font-semibold hover:bg-gray-800 transition-colors"
            >
              {submitting ? 'Publishing Version...' : 'Publish New Version'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Simulation Modal */}
      {simModalOpen && (
        <Modal
          isOpen={simModalOpen}
          onClose={() => setSimModalOpen(false)}
          title={`Dry-Run Rule Simulation — ${selectedRule?.name || ''}`}
          subtitle={`Rule Code: ${selectedRule?.rule_code} (v${selectedRule?.version})`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-xs">
              <span className="font-bold uppercase tracking-wider text-[10px] block">Dry-Run Disclaimer</span>
              SIMULATION ONLY: This evaluation was executed in sandbox memory. Zero database records were mutated, and no real notifications or alerts were dispatched.
            </div>

            {simulating ? (
              <div className="py-8 text-center text-brand-muted">
                Running rule simulation engine...
              </div>
            ) : simResult ? (
              <div className="space-y-3">
                <h4 className="font-bold text-brand-ink uppercase text-[10px] tracking-wider">
                  Simulation Outcome & Predictive Impact
                </h4>
                <div className="p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border font-mono text-[11px] space-y-2">
                  <pre className="whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(simResult.simulation_results, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <p className="text-brand-muted">No simulation results available.</p>
            )}

            <div className="flex justify-end pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setSimModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-brand-ink text-white font-semibold"
              >
                Close Simulation
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Version History Modal */}
      {historyModalOpen && (
        <Modal
          isOpen={historyModalOpen}
          onClose={() => setHistoryModalOpen(false)}
          title={`Version History & Governance Ledger`}
          subtitle={`Rule Code: ${selectedRule?.rule_code}`}
        >
          <div className="space-y-4 text-xs">
            {loadingHistory ? (
              <div className="py-8 text-center text-brand-muted">Loading version history...</div>
            ) : versionHistory.length === 0 ? (
              <div className="py-8 text-center text-brand-muted">
                No archived previous versions. Current version v{selectedRule?.version} is the initial baseline.
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {versionHistory.map((item) => (
                  <div key={item.id} className="p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-brand-ink text-xs">Version {item.version}</span>
                      <span className="text-[10px] text-brand-muted font-mono">
                        {new Date(item.created_at).toLocaleString('en-IN', {
                          timeZone: 'Asia/Kolkata',
                          dateStyle: 'medium',
                          timeStyle: 'short'
                        })}
                      </span>
                    </div>
                    <p className="text-[11px] text-brand-muted mt-1 italic">
                      Change reason: "{item.change_reason || 'Archived prior version'}"
                    </p>
                    <div className="mt-2 p-2 bg-white rounded border border-gray-200 font-mono text-[10px] text-gray-700 max-h-24 overflow-y-auto">
                      <pre>{item.config_json}</pre>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end pt-3 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setHistoryModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-brand-ink text-white font-semibold"
              >
                Close Ledger
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
