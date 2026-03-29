import type { Incident, TraceEvent, Task, Alert, DashboardData } from './types';

const BASE = '';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function simulateIncident(
  scenario: string,
  triggerSource: string = 'dashboard_demo'
): Promise<Incident> {
  return request<Incident>('/api/incidents/simulate', {
    method: 'POST',
    body: JSON.stringify({ scenario, trigger_source: triggerSource }),
  });
}

export async function getIncident(id: string): Promise<Incident> {
  return request<Incident>(`/api/incidents/${id}`);
}

export async function getTrace(incidentId: string): Promise<TraceEvent[]> {
  return request<TraceEvent[]>(`/api/incidents/${incidentId}/trace`);
}

export async function getTasks(incidentId?: string): Promise<Task[]> {
  const params = incidentId ? `?incident_id=${incidentId}` : '';
  return request<Task[]>(`/api/tasks${params}`);
}

export async function getAlerts(incidentId?: string): Promise<Alert[]> {
  const params = incidentId ? `?incident_id=${incidentId}` : '';
  return request<Alert[]>(`/api/alerts${params}`);
}

export async function acknowledgeAlert(id: string): Promise<Alert> {
  return request<Alert>(`/api/alerts/${id}/ack`, { method: 'POST' });
}

export async function getDashboard(): Promise<DashboardData> {
  return request<DashboardData>('/api/dashboard');
}
