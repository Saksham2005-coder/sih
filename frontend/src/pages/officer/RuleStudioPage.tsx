import React, { useEffect, useState } from 'react';
import { Sliders, Edit3, ShieldAlert, CheckCircle2, History } from 'lucide-react';
import { api } from '../../api/client';
import { RuleDefinitionItem } from '../../types';
import { Modal } from '../../components/common/Modal';

export const RuleStudioPage: React.FC = () => {
  const [rules, setRules] = useState<RuleDefinitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRule, setSelectedRule] = useState<RuleDefinitionItem | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [configJson, setConfigJson] = useState('');
  const [version, setVersion] = useState('');
  const [submitting, setSubmitting] = useState(false);

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
    setVersion('1.1.0');
    setEditModalOpen(true);
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRule) return;
    setSubmitting(true);
    try {
      await api.updateRule(selectedRule.rule_code, {
        config_json: configJson,
        version: version || undefined,
      });
      setEditModalOpen(false);
      loadRules();
    } catch (err: any) {
      alert(err.message || 'Failed to update rule');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-brand-ink">Rule Studio & Policy Governance</h1>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-[#C5892B] border border-amber-300">
            Illustrative Demo Rules
          </span>
        </div>
        <p className="text-xs text-brand-muted mt-0.5">
          Configurable regulatory SLA thresholds, escalation intervals, and workflow routing parameters
        </p>
      </div>

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
                  <span className="px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-brand-ink border border-gray-200">
                    v{rule.version}
                  </span>
                </div>

                <div className="p-3 bg-brand-porcelain/60 rounded-lg border border-brand-border text-xs font-mono space-y-1">
                  {Object.entries(parsedConfig).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-brand-muted">{k}:</span>
                      <span className="font-semibold text-brand-ink">{JSON.stringify(v)}</span>
                    </div>
                  ))}
                </div>

                <p className="text-[10px] text-gray-400 mt-3">
                  Rule Code: <span className="font-mono text-brand-ink">{rule.rule_code}</span>
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end">
                <button
                  onClick={() => handleOpenEdit(rule)}
                  className="px-3 py-1.5 rounded-lg border border-brand-teal text-brand-teal hover:bg-teal-50 text-xs font-semibold shadow-sm inline-flex items-center gap-1.5 transition-colors"
                >
                  <Edit3 className="w-3.5 h-3.5" /> Modify Parameters
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Edit Rule Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title="Modify Regulatory Rule Parameters"
        subtitle={selectedRule?.name || ''}
      >
        <form onSubmit={handleSaveRule} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              New Rule Version Tag
            </label>
            <input
              type="text"
              required
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="w-full border border-brand-border rounded-lg p-2 text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div>
            <label className="block font-semibold text-brand-ink uppercase text-[10px] tracking-wider mb-1">
              Configuration JSON
            </label>
            <textarea
              rows={8}
              required
              value={configJson}
              onChange={(e) => setConfigJson(e.target.value)}
              className="w-full border border-brand-border rounded-lg p-2.5 font-mono text-xs focus:ring-1 focus:ring-brand-teal"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setEditModalOpen(false)}
              className="px-4 py-2 border border-brand-border rounded-lg font-semibold hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-brand-teal text-white rounded-lg font-semibold hover:bg-brand-teal-dark shadow-sm"
            >
              {submitting ? 'Updating...' : 'Publish Version'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
