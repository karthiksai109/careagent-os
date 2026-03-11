'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Activity, FileText, Heart, Phone, Shield, TrendingUp,
  Users, AlertTriangle, CheckCircle2, Clock, ArrowRight,
  Stethoscope, BarChart3, Workflow, PhoneCall, ClipboardList,
  DollarSign, BedDouble, ChevronRight, Play, LayoutDashboard,
  CircleDot, Timer, X
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

type Tab = 'overview' | 'demo' | 'triage' | 'journey' | 'auth' | 'docs';

const NAV: { id: Tab; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'demo', label: 'Live Demo', icon: Play },
  { id: 'triage', label: 'Triage', icon: AlertTriangle },
  { id: 'journey', label: 'Patient Journey', icon: Workflow },
  { id: 'auth', label: 'Prior Auth', icon: Shield },
  { id: 'docs', label: 'Documentation', icon: FileText },
];

const AGENTS = [
  { key: 'voice_intake', name: 'Voice Intake', icon: Phone, desc: 'Patient calls & symptom collection', color: 'bg-sky-500' },
  { key: 'triage', name: 'Triage', icon: AlertTriangle, desc: 'Urgency classification & routing', color: 'bg-amber-500' },
  { key: 'prior_auth', name: 'Prior Auth', icon: Shield, desc: 'Insurance authorization', color: 'bg-violet-500' },
  { key: 'clinical_doc', name: 'Clinical Docs', icon: FileText, desc: 'SOAP notes & ICD-10 coding', color: 'bg-emerald-500' },
  { key: 'patient_advocate', name: 'Patient Advocate', icon: Heart, desc: 'Follow-ups & reminders', color: 'bg-rose-500' },
  { key: 'operations', name: 'Operations', icon: BarChart3, desc: 'Analytics & forecasting', color: 'bg-teal-500' },
];

const URGENCY_BADGE: Record<string, string> = {
  critical: 'badge-danger',
  emergency: 'badge-danger',
  urgent: 'badge-warning',
  semi_urgent: 'badge-info',
  non_urgent: 'badge-success',
};

export default function Dashboard() {
  const [tab, setTab] = useState<Tab>('overview');
  const [metrics, setMetrics] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [demoResult, setDemoResult] = useState<any>(null);
  const [triageResult, setTriageResult] = useState<any>(null);
  const [journeyResult, setJourneyResult] = useState<any>(null);
  const [authResult, setAuthResult] = useState<any>(null);
  const [soapResult, setSoapResult] = useState<any>(null);
  const [callResult, setCallResult] = useState<any>(null);

  const get = useCallback(async (path: string) => {
    try { const r = await fetch(`${API}${path}`); return r.ok ? r.json() : null; }
    catch { return null; }
  }, []);

  const post = useCallback(async (path: string, body: any) => {
    try {
      const r = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!r.ok) throw new Error(`${r.status}`);
      return r.json();
    } catch (e: any) { setError(e.message); return null; }
  }, []);

  useEffect(() => {
    const load = async () => {
      const [m, a] = await Promise.all([get('/operations/dashboard'), get('/activity-feed?limit=20')]);
      if (m) setMetrics(m.metrics || m);
      if (a) setActivities(a.activities || []);
    };
    load();
    const id = setInterval(load, 12000);
    return () => clearInterval(id);
  }, [get]);

  const refresh = async () => {
    const [m, a] = await Promise.all([get('/operations/dashboard'), get('/activity-feed?limit=20')]);
    if (m) setMetrics(m.metrics || m);
    if (a) setActivities(a.activities || []);
  };

  const exec = async (key: string, fn: () => Promise<any>) => {
    setLoading(p => ({ ...p, [key]: true }));
    setError(null);
    const res = await fn();
    setLoading(p => ({ ...p, [key]: false }));
    await refresh();
    return res;
  };

  const ov = metrics?.overview;

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-slate-200 flex flex-col fixed h-screen">
        <div className="px-5 py-5 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 leading-none">CareAgent OS</h1>
              <p className="text-[10px] text-slate-400 mt-0.5">Healthcare Operations</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-3 space-y-0.5">
          {NAV.map(n => (
            <button key={n.id} onClick={() => setTab(n.id)}
              className={n.id === tab ? 'sidebar-item-active w-full' : 'sidebar-item-inactive w-full'}>
              <n.icon className="w-4 h-4" />
              <span>{n.label}</span>
            </button>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
            <span className="text-xs text-slate-500">6 agents online</span>
          </div>
          <p className="text-[10px] text-slate-400">Multi-LLM Routing Active</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-56 overflow-x-hidden">
        {/* Top bar */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-30">
          <h2 className="text-sm font-semibold text-slate-800 shrink-0">
            {NAV.find(n => n.id === tab)?.label}
          </h2>
          <div className="flex items-center gap-3 shrink-0">
            {error && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 max-w-xs">
                <AlertTriangle className="w-3 h-3 shrink-0" />
                <span className="truncate">{error}</span>
                <button onClick={() => setError(null)} className="shrink-0"><X className="w-3 h-3" /></button>
              </div>
            )}
            <span className="badge-success shrink-0"><CheckCircle2 className="w-3 h-3 mr-1" /> System Healthy</span>
          </div>
        </header>

        <div className="p-6 max-w-[1400px]">
          {/* OVERVIEW */}
          {tab === 'overview' && (
            <div className="space-y-6 animate-in">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Stat icon={Users} label="Patients Today" value={ov?.patients_today ?? '--'} />
                <Stat icon={Clock} label="Avg Wait" value={ov?.average_wait_minutes ? `${ov.average_wait_minutes}m` : '--'} />
                <Stat icon={BedDouble} label="Bed Occupancy" value={ov?.bed_occupancy_rate ? `${(ov.bed_occupancy_rate * 100).toFixed(0)}%` : '--'} />
                <Stat icon={Activity} label="Tasks Today" value={ov?.tasks_completed_today ?? '--'} />
                <Stat icon={DollarSign} label="Revenue" value={metrics?.revenue?.today ? `$${(metrics.revenue.today / 1000).toFixed(0)}K` : '--'} />
                <Stat icon={Heart} label="Satisfaction" value={metrics?.patient_satisfaction?.score ? `${metrics.patient_satisfaction.score}/5` : '--'} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 card p-5">
                  <h3 className="section-heading mb-4">Agent Status</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {AGENTS.map(a => {
                      const m = metrics?.agent_performance?.[a.key];
                      return (
                        <div key={a.key} className="card-hover p-4">
                          <div className="flex items-center gap-2.5 mb-2">
                            <div className={`w-7 h-7 ${a.color} rounded-md flex items-center justify-center`}>
                              <a.icon className="w-3.5 h-3.5 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-800 truncate">{a.name}</p>
                              <p className="text-[11px] text-slate-400 truncate">{a.desc}</p>
                            </div>
                            <div className="w-2 h-2 rounded-full bg-emerald-500 pulse-dot" />
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-500 mt-2 pt-2 border-t border-slate-100">
                            <span>{m?.tasks ?? m?.reports_generated ?? '--'} tasks</span>
                            {m?.success_rate && <span className="text-emerald-600">{(m.success_rate * 100).toFixed(0)}%</span>}
                            {m?.approval_rate && <span className="text-emerald-600">{(m.approval_rate * 100).toFixed(0)}% approved</span>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="card p-5">
                  <h3 className="section-heading mb-4">Activity Log</h3>
                  <div className="space-y-1.5 max-h-[420px] overflow-y-auto">
                    {activities.length > 0 ? activities.map((a, i) => (
                      <div key={a.id || i} className="flex items-start gap-2.5 py-2 px-2 rounded-md hover:bg-slate-50 transition-colors">
                        <div className={`w-1.5 h-1.5 mt-1.5 rounded-full flex-shrink-0 ${a.status === 'completed' ? 'bg-emerald-500' : a.status === 'failed' ? 'bg-red-500' : 'bg-amber-500 pulse-dot'}`} />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-slate-700 truncate">{a.agent_name}</p>
                          <p className="text-[11px] text-slate-400">{a.task_type} &middot; {a.duration_ms || 0}ms</p>
                        </div>
                      </div>
                    )) : (
                      <p className="text-xs text-slate-400 text-center py-10">Run a demo to see activity</p>
                    )}
                  </div>
                </div>
              </div>

              {metrics?.efficiency && (
                <div className="card p-5">
                  <h3 className="section-heading mb-4">Efficiency Gains</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center py-3">
                      <p className="stat-value">{metrics.efficiency.admin_time_saved_hours}h</p>
                      <p className="stat-label mt-1">Admin Hours Saved</p>
                    </div>
                    <div className="text-center py-3">
                      <p className="stat-value">{metrics.efficiency.calls_automated}</p>
                      <p className="stat-label mt-1">Calls Automated</p>
                    </div>
                    <div className="text-center py-3">
                      <p className="stat-value">{metrics.efficiency.documents_generated}</p>
                      <p className="stat-label mt-1">Docs Generated</p>
                    </div>
                    <div className="text-center py-3">
                      <p className="stat-value">{metrics.efficiency.prior_auths_processed}</p>
                      <p className="stat-label mt-1">Auths Processed</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* LIVE DEMO */}
          {tab === 'demo' && (
            <div className="space-y-6 animate-in">
              <div className="card p-6">
                <div className="flex items-start justify-between gap-4 mb-5 flex-wrap sm:flex-nowrap">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">Full System Demo</h3>
                    <p className="text-sm text-slate-500 mt-1">
                      Processes 3 patients end-to-end through all 6 agents.
                    </p>
                  </div>
                  <button onClick={() => exec('demo', async () => { const r = await post('/demo', {}); if (r) setDemoResult(r); })} disabled={loading.demo} className="btn-primary">
                    {loading.demo ? <><span className="spinner" /> Running...</> : <><Play className="w-4 h-4" /> Run Demo</>}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { name: 'Maria Santos', age: 62, note: 'Chest pain, SOB, diaphoresis' },
                    { name: 'James Wilson', age: 8, note: 'High fever, sore throat, white patches' },
                    { name: 'Aisha Patel', age: 34, note: 'Back pain radiating to leg, numbness' },
                  ].map((p, i) => (
                    <div key={i} className="card p-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-slate-800">{p.name}</span>
                        <span className="text-xs text-slate-400">Age {p.age}</span>
                      </div>
                      <p className="text-xs text-slate-500">{p.note}</p>
                      {demoResult?.patient_results?.[i] && (
                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2">
                          <span className={URGENCY_BADGE[demoResult.patient_results[i].urgency] || 'badge-neutral'}>
                            {demoResult.patient_results[i].urgency?.toUpperCase()}
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {demoResult.patient_results[i].workflow_steps} steps &middot; {demoResult.patient_results[i].total_duration_ms}ms
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {demoResult && (
                  <div className="mt-5 p-4 bg-emerald-50 border border-emerald-200 rounded-md">
                    <p className="text-sm font-medium text-emerald-800 flex items-center gap-2 mb-2">
                      <CheckCircle2 className="w-4 h-4" /> {demoResult.patients_processed} patients processed
                    </p>
                    <pre className="code-block max-h-60">{JSON.stringify(demoResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TRIAGE */}
          {tab === 'triage' && (
            <div className="space-y-6 animate-in">
              <div className="card p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-1">AI Triage Assessment</h3>
                <p className="text-sm text-slate-500 mb-5">
                  Manchester Triage System + Emergency Severity Index with rule-based safety overrides.
                </p>
                <button onClick={() => exec('triage', async () => {
                  const r = await post('/triage', {
                    symptoms: 'Severe chest pain radiating to left arm, shortness of breath, diaphoresis for 30 minutes',
                    vital_signs: { heart_rate: 110, systolic_bp: 88, diastolic_bp: 55, oxygen_saturation: 91, temperature: 98.6, respiratory_rate: 24 },
                    patient_age: 62, patient_gender: 'female', pain_level: 9,
                    medical_history: ['hypertension', 'type 2 diabetes', 'hyperlipidemia'],
                  }); if (r) setTriageResult(r);
                })} disabled={loading.triage} className="btn-primary">
                  {loading.triage ? <><span className="spinner" /> Triaging...</> : <><Stethoscope className="w-4 h-4" /> Triage: Chest Pain Patient</>}
                </button>

                {triageResult && (
                  <div className="mt-5 space-y-4">
                    <div className="flex items-center gap-3">
                      <span className={`text-sm px-3 py-1 rounded-md font-medium ${URGENCY_BADGE[triageResult.triage?.urgency_level] || 'badge-neutral'}`}>
                        {triageResult.triage?.urgency_level?.toUpperCase()} &mdash; Score: {triageResult.triage?.urgency_score?.toFixed(2)}
                      </span>
                      {triageResult.is_critical_flag && <span className="badge-danger text-[11px]">RULE OVERRIDE</span>}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="card p-4">
                        <p className="stat-label mb-2">Assessment</p>
                        <p className="text-sm text-slate-700">{triageResult.triage?.assessment}</p>
                      </div>
                      <div className="card p-4">
                        <p className="stat-label mb-2">Department</p>
                        <p className="text-sm text-slate-700 capitalize">{triageResult.triage?.recommended_department?.replace(/_/g, ' ')}</p>
                        <p className="stat-label mt-3 mb-2">Suggested Tests</p>
                        <div className="flex flex-wrap gap-1.5">
                          {triageResult.triage?.suggested_tests?.map((t: string, i: number) => (
                            <span key={i} className="badge-neutral">{t}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <pre className="code-block max-h-60">{JSON.stringify(triageResult.triage, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PATIENT JOURNEY */}
          {tab === 'journey' && (
            <div className="space-y-6 animate-in">
              <div className="card p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-1">Full Patient Journey</h3>
                <p className="text-sm text-slate-500 mb-5">
                  Intake &rarr; Triage &rarr; Clinical Documentation &rarr; Prior Auth &rarr; Patient Follow-up
                </p>
                <button onClick={() => exec('journey', async () => {
                  const r = await post('/journey', {
                    patient_name: 'Sarah Johnson', patient_age: 45, patient_gender: 'female',
                    symptoms: 'Progressive lower back pain for 2 weeks, radiating down right leg, numbness in right foot',
                    vital_signs: { heart_rate: 88, systolic_bp: 135, diastolic_bp: 85, oxygen_saturation: 98, temperature: 98.4, respiratory_rate: 16 },
                    pain_level: 8, medical_history: ['none significant'], medications: ['ibuprofen 400mg PRN'],
                    allergies: [], insurance_provider: 'UnitedHealthcare', procedure: 'MRI lumbar spine',
                  }); if (r) setJourneyResult(r);
                })} disabled={loading.journey} className="btn-primary">
                  {loading.journey ? <><span className="spinner" /> Processing...</> : <><ArrowRight className="w-4 h-4" /> Run Patient Journey</>}
                </button>

                {journeyResult && (
                  <div className="mt-5 space-y-4">
                    <div className="flex items-center gap-2 flex-wrap">
                      {journeyResult.workflow?.steps?.map((s: any, i: number) => (
                        <div key={i} className="flex items-center gap-2">
                          <div className={`px-3 py-1.5 rounded-md text-xs font-medium border ${
                            s.status?.includes('complete') ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-50 text-slate-500 border-slate-200'}`}>
                            {s.agent} <span className="text-slate-400 ml-1">{s.duration_ms}ms</span>
                          </div>
                          {i < (journeyResult.workflow?.steps?.length || 0) - 1 && <ChevronRight className="w-4 h-4 text-slate-300" />}
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-6 text-sm text-slate-600">
                      <span>Total: <strong className="text-slate-900">{journeyResult.workflow?.total_duration_ms}ms</strong></span>
                      <span>Steps: <strong className="text-slate-900">{journeyResult.workflow?.steps?.length}</strong></span>
                    </div>
                    <pre className="code-block max-h-60">{JSON.stringify(journeyResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PRIOR AUTH */}
          {tab === 'auth' && (
            <div className="space-y-6 animate-in">
              <div className="card p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-1">Prior Authorization</h3>
                <p className="text-sm text-slate-500 mb-5">
                  Detects requirements, generates clinical justification, and calls insurance companies.
                </p>
                <div className="flex gap-3 flex-wrap">
                  <button onClick={() => exec('auth', async () => {
                    const r = await post('/prior-auth', {
                      procedure: 'MRI lumbar spine with and without contrast', insurance_provider: 'UnitedHealthcare',
                      diagnosis: 'Lumbar radiculopathy with progressive neurological deficit',
                      clinical_notes: 'Failed 4 weeks of conservative treatment including NSAIDs and physical therapy.',
                    }); if (r) setAuthResult(r);
                  })} disabled={loading.auth} className="btn-primary">
                    {loading.auth ? <><span className="spinner" /> Submitting...</> : <><ClipboardList className="w-4 h-4" /> Submit Auth</>}
                  </button>
                  <button onClick={() => exec('call', async () => {
                    const r = await post('/prior-auth/call-insurance', {
                      insurance_provider: 'UnitedHealthcare', call_reason: 'Prior authorization status check for MRI lumbar spine',
                    }); if (r) setCallResult(r);
                  })} disabled={loading.call} className="btn-outline">
                    {loading.call ? <><span className="spinner" /> Calling...</> : <><PhoneCall className="w-4 h-4" /> Call Insurance</>}
                  </button>
                </div>

                {authResult && (
                  <div className="mt-5">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="badge-warning">{authResult.status?.toUpperCase()}</span>
                      {authResult.estimated_turnaround && <span className="text-xs text-slate-500">Est. {authResult.estimated_turnaround}h turnaround</span>}
                    </div>
                    <pre className="code-block max-h-60">{JSON.stringify(authResult.authorization || authResult, null, 2)}</pre>
                  </div>
                )}

                {callResult && (
                  <div className="mt-5 p-4 bg-violet-50 border border-violet-200 rounded-md">
                    <p className="text-sm font-medium text-violet-800 flex items-center gap-2 mb-2">
                      <PhoneCall className="w-4 h-4" /> Insurance Call Transcript
                    </p>
                    <pre className="text-xs text-slate-700 whitespace-pre-wrap font-mono">{callResult.call_transcript}</pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* DOCUMENTATION */}
          {tab === 'docs' && (
            <div className="space-y-6 animate-in">
              <div className="card p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-1">Clinical Documentation</h3>
                <p className="text-sm text-slate-500 mb-5">
                  Generates SOAP notes, ICD-10/CPT codes, discharge instructions, and referral letters.
                </p>
                <button onClick={() => exec('soap', async () => {
                  const r = await post('/documentation/soap', {
                    symptoms: 'Productive cough for 5 days, low-grade fever, mild dyspnea on exertion',
                    vital_signs: { heart_rate: 92, systolic_bp: 128, diastolic_bp: 82, oxygen_saturation: 95, temperature: 100.4, respiratory_rate: 20 },
                    patient_age: 55, patient_gender: 'male',
                    exam_findings: 'Right basilar crackles on auscultation, mild respiratory distress',
                    medical_history: ['COPD', 'former smoker'], medications: ['albuterol inhaler PRN', 'tiotropium daily'],
                    allergies: ['sulfa drugs'],
                  }); if (r) setSoapResult(r);
                })} disabled={loading.soap} className="btn-primary">
                  {loading.soap ? <><span className="spinner" /> Generating...</> : <><FileText className="w-4 h-4" /> Generate SOAP Notes</>}
                </button>

                {soapResult?.documentation && (
                  <div className="mt-5 space-y-3">
                    {soapResult.documentation.soap && Object.entries(soapResult.documentation.soap).map(([k, v]: [string, any]) => (
                      <div key={k} className="card p-4">
                        <p className="stat-label mb-1.5">{k}</p>
                        <p className="text-sm text-slate-700">{typeof v === 'string' ? v : JSON.stringify(v)}</p>
                      </div>
                    ))}
                    {soapResult.documentation.icd10_codes?.length > 0 && (
                      <div className="card p-4">
                        <p className="stat-label mb-2">ICD-10 Codes</p>
                        <div className="flex flex-wrap gap-1.5">
                          {soapResult.documentation.icd10_codes.map((c: any, i: number) => (
                            <span key={i} className="badge-info">{c.code || c}{c.description ? ` — ${c.description}` : ''}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <footer className="px-6 py-4 border-t border-slate-200 text-center text-xs text-slate-400">
          CareAgent OS &middot; AI Agents Hackathon 2026 &middot; Built by Karthik Ramadugu
        </footer>
      </main>
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-slate-400" />
        <span className="stat-label">{label}</span>
      </div>
      <p className="stat-value">{value}</p>
    </div>
  );
}
