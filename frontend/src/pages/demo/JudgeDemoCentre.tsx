import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Compass, ShieldCheck, CheckCircle2, Clock, AlertTriangle, FileText,
  RefreshCw, ArrowRight, Activity, Users, FileCheck, Layers, ExternalLink,
  ChevronRight, AlertOctagon, HelpCircle, Check, X, Shield, Gavel, Cpu,
  Flame, Radio, Send, Database, Info, RotateCcw
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  DemoScenarioItem,
  WorkflowRouteDefinition,
  ExplainabilityResponse,
  DemoTelemetryResponse
} from '../../types';
import { StatusBadge } from '../../components/common/StatusBadge';

export const JudgeDemoCentre: React.FC = () => {
  const { user, login } = useAuth();
  const navigate = useNavigate();

  const [scenarios, setScenarios] = useState<DemoScenarioItem[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario-3-deficiency-cure-loop');
  const [routes, setRoutes] = useState<Record<string, WorkflowRouteDefinition>>({});
  const [explainability, setExplainability] = useState<ExplainabilityResponse | null>(null);
  const [telemetry, setTelemetry] = useState<DemoTelemetryResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'stepper' | 'workflow_map' | 'explainability'>('stepper');
  const [selectedNodeCode, setSelectedNodeCode] = useState<string | null>(null);

  // Load initial demo scenarios, routes, and telemetry
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
        const [scenariosData, routesData, telemetryData] = await Promise.all([
          api.getDemoScenarios(),
          api.getDemoRoutes(),
          api.getDemoTelemetry()
        ]);
        setScenarios(scenariosData);
        setRoutes(routesData);
        setTelemetry(telemetryData);

        // Load explainability for first/default scenario
        const active = scenariosData.find((s: DemoScenarioItem) => s.scenario_id === selectedScenarioId) || scenariosData[0];
        if (active) {
          setSelectedScenarioId(active.scenario_id);
          const exp = await api.getDemoExplainability(active.application_id);
          setExplainability(exp);
        }
      } catch (err: any) {
        console.error('Failed to load demo explorer data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // When selected scenario changes, fetch explainability
  const handleSelectScenario = async (scenario: DemoScenarioItem) => {
    setSelectedScenarioId(scenario.scenario_id);
    setSelectedNodeCode(null);
    setResetMessage(null);
    try {
      const exp = await api.getDemoExplainability(scenario.application_id);
      setExplainability(exp);
    } catch (err) {
      console.error('Failed to load scenario explainability:', err);
    }
  };

  // Safe Scenario Reset
  const handleResetScenario = async (scenarioId: string) => {
    try {
      setIsResetting(true);
      const res = await api.resetDemoScenario(scenarioId);
      setResetMessage(res.message);

      // Refresh scenarios and explainability
      const scenariosData = await api.getDemoScenarios();
      setScenarios(scenariosData);
      const active = scenariosData.find((s: DemoScenarioItem) => s.scenario_id === scenarioId);
      if (active) {
        const exp = await api.getDemoExplainability(active.application_id);
        setExplainability(exp);
      }
      setTimeout(() => setResetMessage(null), 6000);
    } catch (err: any) {
      setResetMessage(`Reset failed: ${err.message || err}`);
    } finally {
      setIsResetting(false);
    }
  };

  const activeScenario = scenarios.find(s => s.scenario_id === selectedScenarioId) || scenarios[0];
  const activeRoute = activeScenario ? (routes[activeScenario.route_code] || routes['ONLY_SCRUTINY'] || routes['SCRUTINY_EVC']) : null;

  // Canonical full regulatory lifecycle milestones for the stepper
  const CANONICAL_MILESTONES = [
    {
      code: 'FILING',
      label: 'Filing & Submission',
      stage: 'SUBMITTED',
      description: 'Institutional DPR compilation, fee payment & formal docket lodging.',
      responsibleRole: 'INSTITUTION_ADMIN'
    },
    {
      code: 'SCRUTINY',
      label: 'Document Scrutiny',
      stage: 'UNDER_SCRUTINY',
      description: 'Regional Officer verification of land title, civil safety NOCs, and cadre ratios.',
      responsibleRole: 'REGIONAL_OFFICER'
    },
    {
      code: 'DEFICIENCY',
      label: 'Deficiency & Cure Loop',
      stage: 'DEFICIENCY_COMMUNICATED',
      description: 'Bidirectional cure window: Deficiency memo issuance & institutional resubmission.',
      responsibleRole: 'COMPLIANCE_OFFICER',
      isLoop: true
    },
    {
      code: 'SCRUTINY_SIGNOFF',
      label: 'Scrutiny Sign-Off',
      stage: 'SCRUTINY_COMPLETED',
      description: 'Documentary scrutiny completed with zero open deficiencies.',
      responsibleRole: 'REGIONAL_OFFICER'
    },
    {
      code: 'EVC_SCHEDULE',
      label: 'EVC Inspection & COI',
      stage: 'AWAITING_EVC_SCHEDULE',
      description: 'Unbiased expert panel selection, conflict-of-interest clearance, and scheduling.',
      responsibleRole: 'EVC_COORDINATOR'
    },
    {
      code: 'EVC_FIELD',
      label: 'Mobile Field Evidence',
      stage: 'EVC_COMPLETED',
      description: 'On-site geolocation check-in, laboratory verification, and field evidence capture.',
      responsibleRole: 'COMMITTEE_MEMBER'
    },
    {
      code: 'HEARING_REVIEW',
      label: 'Hearing Committee Review',
      stage: 'AWAITING_SAC_CAC_REVIEW',
      description: 'Standing Appellate / Hearing Committee review for contested or referred cases.',
      responsibleRole: 'COMMITTEE_MEMBER'
    },
    {
      code: 'DECISION_ORDER',
      label: 'Competent Authority Decision',
      stage: 'AWAITING_COMPETENT_AUTHORITY',
      description: 'Exclusive statutory order issuance with IT Act 2000 disclosure and tamper-evident QR.',
      responsibleRole: 'COMPETENT_AUTHORITY'
    },
    {
      code: 'COMPLIANCE_PASSPORT',
      label: 'Continuous Compliance Passport',
      stage: 'APPROVED',
      description: 'Automated deadline scans, 33-year lease renewals, and multi-tier SLA escalations.',
      responsibleRole: 'COMPLIANCE_OFFICER'
    }
  ];

  // Helper to determine stage status for stepper
  const getStageStatus = (stageCode: string, currentStage: string, route: WorkflowRouteDefinition | null) => {
    // Check if stage is explicitly NOT APPLICABLE in the current route
    if (route && route.non_applicable_stages) {
      const nonApp = route.non_applicable_stages.find(na => na.stage_code === stageCode);
      if (nonApp) {
        return {
          state: 'NOT_APPLICABLE' as const,
          reason: nonApp.statutory_reason,
          rule: nonApp.aph_rule_reference
        };
      }
    }

    // Sequence index comparison
    const stageOrder = [
      'DRAFT', 'SUBMITTED', 'UNDER_SCRUTINY', 'DEFICIENCY_COMMUNICATED', 'RESUBMITTED',
      'SCRUTINY_COMPLETED', 'AWAITING_EVC_SCHEDULE', 'EVC_SCHEDULED', 'EVC_COMPLETED',
      'AWAITING_SAC_CAC_REVIEW', 'AWAITING_COMPETENT_AUTHORITY', 'APPROVED', 'REJECTED'
    ];

    const currentIdx = stageOrder.indexOf(currentStage);
    const targetIdx = stageOrder.indexOf(stageCode);

    if (currentStage === stageCode || (stageCode === 'DEFICIENCY_COMMUNICATED' && currentStage === 'RESUBMITTED')) {
      return { state: 'CURRENT' as const, reason: 'Current active operational stage awaiting authorized officer action.' };
    }

    if (currentIdx > targetIdx && targetIdx !== -1) {
      return { state: 'COMPLETED' as const, reason: 'Stage completed and verified in audit history.' };
    }

    return { state: 'AWAITING_ACTION' as const, reason: 'Pending completion of preceding statutory milestones.' };
  };

  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-brand-text-muted">
        <RefreshCw className="w-8 h-8 animate-spin text-brand-teal mb-3" />
        <p className="text-sm font-semibold text-brand-text-primary">Loading Judge Demonstration Centre & Live Workflow Explorer...</p>
        <p className="text-xs text-brand-text-muted mt-1">Connecting to authoritative regulatory engine and database...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* 1. Header & Demonstration Badge */}
      <div className="bg-brand-surface rounded-xl border border-brand-border p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-lg bg-brand-teal/10 text-brand-teal border border-brand-teal/30">
                <Compass className="w-6 h-6" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-brand-text-primary tracking-tight">
                    Judge Regulatory Demonstration Centre & Live Workflow Explorer
                  </h1>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                    Synthetic Demo Layer
                  </span>
                </div>
                <p className="text-xs text-brand-text-muted mt-0.5">
                  Interactive architectural inspection layer over ReguFlow 360's genuine backend state machine, explainable priority engine, and multi-role workspaces.
                </p>
              </div>
            </div>
          </div>

          {/* Quick Persona Switcher for Evaluators */}
          {activeScenario && (
            <div className="flex items-center gap-2 bg-brand-surface-secondary px-3.5 py-2 rounded-lg border border-brand-border text-xs">
              <span className="text-brand-text-muted flex items-center gap-1 font-medium">
                <Users className="w-3.5 h-3.5 text-brand-teal" /> Recommended Persona:
              </span>
              <button
                onClick={() => login(activeScenario.recommended_persona.email)}
                className="font-bold text-brand-teal hover:underline flex items-center gap-1 cursor-pointer"
                title={`Switch session to ${activeScenario.recommended_persona.name} (${activeScenario.recommended_persona.role})`}
              >
                {activeScenario.recommended_persona.name} ({activeScenario.recommended_persona.role.replace(/_/g, ' ')})
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>

        {/* Distributed System Telemetry Bar */}
        {telemetry && (
          <div className="mt-4 pt-4 border-t border-brand-border grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="flex items-center gap-2 p-2 bg-brand-surface-secondary/50 rounded border border-brand-border/60">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div>
                <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Background Scheduler</span>
                <span className="font-bold text-brand-text-primary">{telemetry.scheduler_status} ({telemetry.scan_interval_seconds}s polling)</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-brand-surface-secondary/50 rounded border border-brand-border/60">
              <Clock className="w-3.5 h-3.5 text-brand-teal shrink-0" />
              <div className="truncate">
                <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Last Deadline Scan</span>
                <span className="font-bold text-brand-text-primary">
                  {telemetry.last_deadline_scan ? `${telemetry.last_deadline_scan.obligations_scanned} obligations scanned` : 'Autonomous Active'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-brand-surface-secondary/50 rounded border border-brand-border/60">
              <Send className="w-3.5 h-3.5 text-brand-teal shrink-0" />
              <div className="truncate">
                <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Notification Transport</span>
                <span className="font-bold text-brand-text-primary">{telemetry.notification_transport.transport_mode}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2 bg-brand-surface-secondary/50 rounded border border-brand-border/60">
              <Database className="w-3.5 h-3.5 text-brand-teal shrink-0" />
              <div className="truncate">
                <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Synthetic Records</span>
                <span className="font-bold text-emerald-600 dark:text-emerald-400">Grounded in Live DB</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Reset Feedback Notification */}
      {resetMessage && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs font-semibold text-emerald-700 dark:text-emerald-300 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{resetMessage}</span>
          </div>
          <button onClick={() => setResetMessage(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. Interactive Scenario Selector Strip */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-text-muted flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-brand-teal" /> Supported Regulatory Scenarios (Evaluator Tracks)
          </h2>
          <span className="text-[11px] text-brand-text-muted">Click any track to inspect live workflow & explainability</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {scenarios.map((sc) => {
            const isSelected = sc.scenario_id === selectedScenarioId;
            return (
              <div
                key={sc.scenario_id}
                onClick={() => handleSelectScenario(sc)}
                className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all duration-150 relative flex flex-col justify-between ${
                  isSelected
                    ? 'bg-brand-surface-secondary border-brand-teal ring-2 ring-brand-teal/20 shadow-sm'
                    : 'bg-brand-surface border-brand-border hover:border-brand-border/80 hover:bg-brand-surface-secondary/50'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      isSelected ? 'bg-brand-teal text-white' : 'bg-brand-surface-secondary text-brand-text-muted border border-brand-border'
                    }`}>
                      Track #{sc.scenario_number}
                    </span>
                    <span className="font-mono text-[10px] font-semibold text-brand-text-muted">
                      {sc.application_number}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-brand-text-primary line-clamp-2 leading-snug">
                    {sc.title}
                  </h3>

                  <p className="text-[11px] text-brand-text-secondary mt-1.5 line-clamp-2">
                    {sc.subtitle}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-brand-border/60 flex items-center justify-between text-[11px]">
                  <StatusBadge status={sc.current_stage} />
                  <span className="text-[10px] font-bold text-brand-text-muted">
                    Priority: {sc.priority_score}/100
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Selected Scenario Action Bar & Deep Link */}
      {activeScenario && (
        <div className="bg-brand-surface rounded-xl border border-brand-border p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start md:items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-surface-secondary border border-brand-border">
              <FileCheck className="w-5 h-5 text-brand-teal" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-brand-text-primary">
                  {activeScenario.title}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-surface-secondary text-brand-teal border border-brand-border">
                  {activeScenario.application_number}
                </span>
                <StatusBadge status={activeScenario.current_stage} />
              </div>
              <p className="text-xs text-brand-text-muted mt-0.5">
                Route: <span className="font-semibold text-brand-text-primary">{activeScenario.route_code}</span> • Recommended Actor: <span className="font-semibold text-brand-text-primary">{activeScenario.recommended_persona.name}</span> ({activeScenario.recommended_persona.role})
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            {/* Safe Scenario Reset Button */}
            <button
              onClick={() => handleResetScenario(activeScenario.scenario_id)}
              disabled={isResetting}
              className="px-3 py-1.5 rounded-lg border border-brand-border text-brand-text-primary hover:bg-brand-surface-secondary text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
              title="Safely resets target application to initial scenario state without deleting audit logs"
            >
              <RotateCcw className={`w-3.5 h-3.5 text-brand-text-muted ${isResetting ? 'animate-spin' : ''}`} />
              {isResetting ? 'Resetting...' : 'Safe Reset Scenario'}
            </button>

            {/* Direct Deep Link to Operational Workspace */}
            <button
              onClick={() => navigate(activeScenario.target_url)}
              className="px-3.5 py-1.5 rounded-lg bg-brand-teal text-white hover:bg-brand-teal/90 text-xs font-bold flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
            >
              Open in Operational Workspace <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* 4. Tab Navigation: Guided Lifecycle Stepper vs Visual Workflow Map vs Deep Explainability */}
      <div className="flex border-b border-brand-border gap-2">
        <button
          onClick={() => setActiveTab('stepper')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'stepper'
              ? 'border-brand-teal text-brand-teal'
              : 'border-transparent text-brand-text-muted hover:text-brand-text-primary'
          }`}
        >
          <Compass className="w-4 h-4" /> 1. Guided Regulatory Lifecycle Stepper
        </button>

        <button
          onClick={() => setActiveTab('workflow_map')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'workflow_map'
              ? 'border-brand-teal text-brand-teal'
              : 'border-transparent text-brand-text-muted hover:text-brand-text-primary'
          }`}
        >
          <Activity className="w-4 h-4" /> 2. Live Interactive Workflow Map
        </button>

        <button
          onClick={() => setActiveTab('explainability')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === 'explainability'
              ? 'border-brand-teal text-brand-teal'
              : 'border-transparent text-brand-text-muted hover:text-brand-text-primary'
          }`}
        >
          <ShieldCheck className="w-4 h-4" /> 3. Explainability Panel & Fact Citations
        </button>
      </div>

      {/* 5. TAB 1: GUIDED REGULATORY LIFECYCLE STEPPER */}
      {activeTab === 'stepper' && (
        <div className="bg-brand-surface rounded-xl border border-brand-border p-6 shadow-xs space-y-6">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-brand-text-primary">
                Authoritative Lifecycle Progression ({activeScenario?.route_code})
              </h2>
              <span className="text-xs text-brand-text-muted font-medium">
                Derived directly from backend state machine
              </span>
            </div>
            <p className="text-xs text-brand-text-muted mt-1">
              Shows every statutory stage from DPR filing to continuous compliance monitoring. Notice non-applicable stages explicitly marked with statutory rule citations.
            </p>
          </div>

          <div className="space-y-4">
            {CANONICAL_MILESTONES.map((m, idx) => {
              const stageStatus = getStageStatus(m.stage, activeScenario?.current_stage || 'SUBMITTED', activeRoute);
              const isNotApp = stageStatus.state === 'NOT_APPLICABLE';
              const isCurrent = stageStatus.state === 'CURRENT';
              const isCompleted = stageStatus.state === 'COMPLETED';

              return (
                <div
                  key={m.code}
                  className={`p-4 rounded-xl border transition-all ${
                    isCurrent
                      ? 'bg-brand-surface-secondary border-brand-teal ring-2 ring-brand-teal/20 shadow-xs'
                      : isNotApp
                      ? 'bg-brand-surface-secondary/40 border-brand-border/60 opacity-70'
                      : isCompleted
                      ? 'bg-emerald-500/5 border-emerald-500/30'
                      : 'bg-brand-surface border-brand-border'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        isCompleted
                          ? 'bg-emerald-500 text-white'
                          : isCurrent
                          ? 'bg-brand-teal text-white ring-4 ring-brand-teal/20'
                          : isNotApp
                          ? 'bg-slate-300 dark:bg-slate-700 text-brand-text-muted'
                          : 'bg-brand-surface-secondary text-brand-text-muted border border-brand-border'
                      }`}>
                        {isCompleted ? <Check className="w-4 h-4" /> : isNotApp ? <X className="w-3.5 h-3.5" /> : idx + 1}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-brand-text-primary">
                            {m.label}
                          </h4>
                          {m.isLoop && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                              Return Loop
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-brand-text-muted mt-0.5">{m.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      {isNotApp ? (
                        <div className="text-right">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700">
                            NOT APPLICABLE
                          </span>
                        </div>
                      ) : isCurrent ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-teal/15 text-brand-teal border border-brand-teal/30 flex items-center gap-1 animate-pulse">
                          <span className="w-1.5 h-1.5 rounded-full bg-brand-teal" /> ACTIVE STAGE
                        </span>
                      ) : isCompleted ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                          <Check className="w-3 h-3" /> COMPLETED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold text-brand-text-muted bg-brand-surface-secondary border border-brand-border">
                          Awaiting Action
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Statutory Reason for Non-Applicable or Active Status Details */}
                  {isNotApp && stageStatus.reason && (
                    <div className="mt-2.5 pt-2 border-t border-brand-border/60 text-[11px] text-brand-text-muted flex items-start gap-1.5">
                      <Info className="w-3.5 h-3.5 text-brand-teal shrink-0 mt-0.5" />
                      <div>
                        <span>{stageStatus.reason}</span>
                        {stageStatus.rule && (
                          <span className="ml-1.5 font-mono text-[10px] font-semibold text-brand-teal underline">
                            [{stageStatus.rule}]
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 6. TAB 2: LIVE INTERACTIVE WORKFLOW MAP */}
      {activeTab === 'workflow_map' && (
        <div className="bg-brand-surface rounded-xl border border-brand-border p-6 shadow-xs space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-brand-text-primary">
                Canonical Workflow Map: {activeRoute?.route_name || activeScenario?.route_code}
              </h2>
              <p className="text-xs text-brand-text-muted mt-0.5">
                Exposes authoritative state graph directly from backend rules. Click any node to inspect SLA limits and permitted actor roles.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1 text-[11px] text-brand-text-muted">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Completed
              </span>
              <span className="flex items-center gap-1 text-[11px] text-brand-text-muted ml-2">
                <span className="w-2.5 h-2.5 rounded-full bg-brand-teal ring-2 ring-brand-teal/30 animate-pulse" /> Active Stage
              </span>
              <span className="flex items-center gap-1 text-[11px] text-brand-text-muted ml-2">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" /> Pending
              </span>
            </div>
          </div>

          {/* Interactive Visual Graph representation */}
          <div className="p-4 bg-brand-surface-secondary/40 rounded-xl border border-brand-border overflow-x-auto">
            <div className="min-w-[800px] flex items-center justify-between py-6 relative">
              {activeRoute?.stages.map((stg, i) => {
                const isCurrent = activeScenario?.current_stage === stg.stage_code;
                const isSelectedNode = selectedNodeCode === stg.stage_code;

                return (
                  <div key={stg.stage_code} className="flex items-center relative z-10">
                    <div
                      onClick={() => setSelectedNodeCode(stg.stage_code)}
                      className={`p-3 rounded-xl border text-center cursor-pointer transition-all w-32 ${
                        isCurrent
                          ? 'bg-brand-surface border-brand-teal ring-4 ring-brand-teal/20 shadow-md scale-105'
                          : isSelectedNode
                          ? 'bg-brand-surface border-brand-teal ring-2 ring-brand-teal/30'
                          : 'bg-brand-surface border-brand-border hover:border-brand-teal/60'
                      }`}
                    >
                      <div className="flex justify-center mb-1.5">
                        {isCurrent ? (
                          <span className="w-3 h-3 rounded-full bg-brand-teal animate-ping" />
                        ) : (
                          <span className="w-2.5 h-2.5 rounded-full bg-brand-text-muted/40" />
                        )}
                      </div>
                      <p className="text-[11px] font-bold text-brand-text-primary leading-tight line-clamp-2">
                        {stg.label}
                      </p>
                      <span className="text-[9px] font-mono text-brand-text-muted mt-1 block">
                        SLA: {stg.sla_days}d
                      </span>
                    </div>

                    {/* Transition Connector Arrow */}
                    {i < activeRoute.stages.length - 1 && (
                      <div className="w-8 flex items-center justify-center text-brand-text-muted/60">
                        <ArrowRight className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Deficiency Return Loop Highlight Banner */}
            <div className="mt-4 p-3 bg-brand-surface rounded-lg border border-dashed border-amber-500/50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                <span className="text-brand-text-primary font-medium">
                  <span className="font-bold text-amber-600 dark:text-amber-400">Deficiency Return Loop: </span>
                  Scrutiny Committee issues Deficiency Memo → Institution Cures & Resubmits → Case returns to Scrutiny without restarting lifecycle.
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400">
                APH Ch. II Sec. 2.7
              </span>
            </div>
          </div>

          {/* Selected Node Inspector Drawer */}
          {selectedNodeCode && (
            <div className="p-4 bg-brand-surface-secondary rounded-xl border border-brand-teal/40 animate-fadeIn">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-brand-text-primary">Stage Inspector:</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-brand-teal text-white">
                    {selectedNodeCode}
                  </span>
                </div>
                <button onClick={() => setSelectedNodeCode(null)} className="text-brand-text-muted hover:text-brand-text-primary">
                  <X className="w-4 h-4" />
                </button>
              </div>

              {(() => {
                const nodeDef = activeRoute?.stages.find(s => s.stage_code === selectedNodeCode);
                if (!nodeDef) return null;
                return (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs mt-3">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Stage Title</span>
                      <p className="font-bold text-brand-text-primary mt-0.5">{nodeDef.label}</p>
                      <p className="text-brand-text-secondary mt-1">{nodeDef.description}</p>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Permitted Roles</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {nodeDef.permitted_roles.map(r => (
                          <span key={r} className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand-surface text-brand-text-primary border border-brand-border">
                            {r}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-semibold text-brand-text-muted block">Configured SLA Norm</span>
                      <p className="font-bold text-brand-teal mt-0.5">{nodeDef.sla_days} Days Max</p>
                      <p className="text-[11px] text-brand-text-muted mt-1">Autonomous SLA tracking triggers multi-tier escalations on breach.</p>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}

      {/* 7. TAB 3: EXPLAINABILITY PANEL & FACT CITATIONS */}
      {activeTab === 'explainability' && explainability && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Card 1: Stage SLA Telemetry */}
            <div className="bg-brand-surface rounded-xl border border-brand-border p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-brand-text-primary flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-brand-teal" /> SLA Telemetry
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  explainability.sla_tracking.is_breached
                    ? 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30'
                    : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                }`}>
                  {explainability.sla_tracking.sla_status}
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-brand-text-muted">Days in Stage:</span>
                  <span className="font-bold text-brand-text-primary">{explainability.sla_tracking.days_elapsed} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-brand-text-muted">Configured Norm:</span>
                  <span className="font-bold text-brand-text-primary">{explainability.sla_tracking.configured_sla_days} days</span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-brand-surface-secondary h-2 rounded-full overflow-hidden mt-2">
                  <div
                    className={`h-full rounded-full ${explainability.sla_tracking.is_breached ? 'bg-rose-500' : 'bg-brand-teal'}`}
                    style={{ width: `${Math.min(100, (explainability.sla_tracking.days_elapsed / explainability.sla_tracking.configured_sla_days) * 100)}%` }}
                  />
                </div>

                <p className="text-[10px] text-brand-text-muted font-mono pt-1">
                  Citation: {explainability.sla_tracking.rule_citation}
                </p>
              </div>
            </div>

            {/* Card 2: Deterministic Priority Score Breakdown */}
            <div className="bg-brand-surface rounded-xl border border-brand-border p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-brand-text-primary flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-amber-500" /> Explainable Priority
                </span>
                <span className="font-bold text-sm text-brand-text-primary">
                  {explainability.priority_breakdown.total_score} / 100
                </span>
              </div>

              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 text-xs">
                {explainability.priority_breakdown.factors.map((f, i) => (
                  <div key={i} className="flex items-center justify-between py-1 border-b border-brand-border/40 text-[11px]">
                    <span className="text-brand-text-secondary truncate mr-2">{f.factor.split(' (+')[0]}</span>
                    <span className="font-mono font-bold text-brand-teal shrink-0">+{f.points} pts</span>
                  </div>
                ))}
              </div>

              <p className="text-[10px] text-brand-text-muted mt-2 pt-2 border-t border-brand-border">
                Strict Invariant: Deterministic mathematical attribution. Never mutates statutory status.
              </p>
            </div>

            {/* Card 3: Deficiencies & EVC Readiness */}
            <div className="bg-brand-surface rounded-xl border border-brand-border p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-brand-text-primary flex items-center gap-1.5">
                  <AlertOctagon className="w-4 h-4 text-brand-teal" /> Deficiencies & EVC
                </span>
                <span className="text-[11px] font-bold text-brand-text-muted">
                  {explainability.deficiency_summary.open_count} Open Deficiencies
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-brand-text-muted">EVC Inspection Required:</span>
                  <span className="font-bold text-brand-text-primary">
                    {explainability.evc_prerequisites.evc_required ? 'YES (Statutory Mandate)' : 'NO (Exempted)'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-brand-text-muted">Inspection Status:</span>
                  <span className="font-bold text-brand-teal">{explainability.evc_prerequisites.inspection_status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-brand-text-muted">Assigned Experts:</span>
                  <span className="font-bold text-brand-text-primary">{explainability.evc_prerequisites.panel_members_count} Panel Members</span>
                </div>
              </div>
            </div>
          </div>

          {/* Deficiencies Table */}
          {explainability.deficiency_summary.items.length > 0 && (
            <div className="bg-brand-surface rounded-xl border border-brand-border p-5 shadow-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-brand-text-muted mb-3 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Active Deficiencies & Documentary Evidence
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-brand-surface-secondary text-brand-text-muted border-b border-brand-border">
                    <tr>
                      <th className="p-2.5 font-semibold">Category</th>
                      <th className="p-2.5 font-semibold">Description</th>
                      <th className="p-2.5 font-semibold">Required Document</th>
                      <th className="p-2.5 font-semibold">Status</th>
                      <th className="p-2.5 font-semibold">Institutional Cure</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {explainability.deficiency_summary.items.map(d => (
                      <tr key={d.id} className="hover:bg-brand-surface-secondary/40">
                        <td className="p-2.5 font-bold text-brand-text-primary">{d.category}</td>
                        <td className="p-2.5 text-brand-text-secondary max-w-xs">{d.description}</td>
                        <td className="p-2.5 font-mono text-[11px] text-brand-teal">{d.required_document || 'N/A'}</td>
                        <td className="p-2.5"><StatusBadge status={d.status} /></td>
                        <td className="p-2.5 text-brand-text-muted">{d.cure_remarks || 'Pending submission'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Immutable Audit Trail Ledger */}
          <div className="bg-brand-surface rounded-xl border border-brand-border p-5 shadow-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-text-muted mb-3 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-brand-teal" /> Immutable Regulatory Audit Ledger
            </h3>

            <div className="space-y-2">
              {explainability.audit_events.map(a => (
                <div key={a.id} className="p-3 bg-brand-surface-secondary/50 rounded-lg border border-brand-border flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-brand-text-primary">{a.action}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-brand-surface text-brand-text-muted border border-brand-border">
                        {a.actor_role}
                      </span>
                    </div>
                    <p className="text-[11px] text-brand-text-muted mt-0.5">
                      Actor: {a.actor_name} • {a.details?.remarks || a.details?.reason || JSON.stringify(a.details)}
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-brand-text-muted shrink-0">
                    {a.timestamp ? new Date(a.timestamp).toLocaleDateString() : 'Recorded'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JudgeDemoCentre;
