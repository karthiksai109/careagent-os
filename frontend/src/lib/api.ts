const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error: ${res.status} - ${error}`);
  }
  return res.json();
}

export const api = {
  // System
  getStatus: () => fetchAPI('/status'),
  getAgents: () => fetchAPI('/agents'),
  getActivityFeed: (limit = 50) => fetchAPI(`/activity-feed?limit=${limit}`),

  // Voice Intake
  startIntake: (data: any) => fetchAPI('/intake/start', { method: 'POST', body: JSON.stringify(data) }),
  continueIntake: (data: any) => fetchAPI('/intake/continue', { method: 'POST', body: JSON.stringify(data) }),
  completeIntake: (data: any) => fetchAPI('/intake/complete', { method: 'POST', body: JSON.stringify(data) }),

  // Triage
  triagePatient: (data: any) => fetchAPI('/triage', { method: 'POST', body: JSON.stringify(data) }),
  quickTriage: (data: any) => fetchAPI('/triage/quick', { method: 'POST', body: JSON.stringify(data) }),

  // Prior Auth
  submitPriorAuth: (data: any) => fetchAPI('/prior-auth', { method: 'POST', body: JSON.stringify(data) }),
  checkAuthRequired: (data: any) => fetchAPI('/prior-auth/check', { method: 'POST', body: JSON.stringify(data) }),
  callInsurance: (data: any) => fetchAPI('/prior-auth/call-insurance', { method: 'POST', body: JSON.stringify(data) }),

  // Clinical Doc
  generateSOAP: (data: any) => fetchAPI('/documentation/soap', { method: 'POST', body: JSON.stringify(data) }),
  codeEncounter: (data: any) => fetchAPI('/documentation/code', { method: 'POST', body: JSON.stringify(data) }),

  // Patient Advocate
  patientFollowup: (data: any) => fetchAPI('/patient/followup', { method: 'POST', body: JSON.stringify(data) }),
  processResponse: (data: any) => fetchAPI('/patient/response', { method: 'POST', body: JSON.stringify(data) }),
  explainDiagnosis: (data: any) => fetchAPI('/patient/explain', { method: 'POST', body: JSON.stringify(data) }),

  // Operations
  getDashboard: () => fetchAPI('/operations/dashboard'),
  getPredictions: (days = 7) => fetchAPI(`/operations/predictions?days=${days}`),
  getSchedule: () => fetchAPI('/operations/schedule'),
  getRevenue: (months = 3) => fetchAPI(`/operations/revenue?months=${months}`),
  getCapacity: () => fetchAPI('/operations/capacity'),

  // Full Journey
  runJourney: (data: any) => fetchAPI('/journey', { method: 'POST', body: JSON.stringify(data) }),
  runDemo: () => fetchAPI('/demo', { method: 'POST' }),
};
