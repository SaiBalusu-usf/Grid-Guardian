import type { Incident, TraceEvent, Task, Alert, DashboardData, MetricsData } from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL || '';

function getApiKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('gridguardian_api_key');
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const apiKey = getApiKey();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  const res = await fetch(`${BASE}${url}`, {
    headers,
    ...options,
  });
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('gridguardian_api_key');
      window.dispatchEvent(new Event('auth_required'));
    }
    throw new Error('Authentication required');
  }
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

export async function getShelters(): Promise<any[]> {
  return request<any[]>('/api/shelters');
}

export async function clearData(): Promise<void> {
  await request('/api/clear', { method: 'POST' });
}

export async function getIncidents(): Promise<any[]> {
  return request<any[]>('/api/incidents');
}

export async function getMetrics(): Promise<MetricsData> {
  return request<MetricsData>('/api/metrics');
}

export async function exportIncident(id: string): Promise<any> {
  return request<any>(`/api/incidents/${id}/export`);
}

export async function startAutoDemo(): Promise<any> {
  return request<any>('/api/demo/auto', { method: 'POST' });
}

export async function shelterCheckin(id: string, count: number): Promise<any> {
  return request<any>(`/api/shelters/${id}/checkin?count=${count}`, { method: 'POST' });
}

export async function getLearnings(): Promise<any[]> {
  return request<any[]>('/api/learnings');
}

export async function createApiKey(label: string, role: string): Promise<any> {
  return request<any>('/api/keys', {
    method: 'POST',
    body: JSON.stringify({ label, role }),
  });
}

export async function updateTaskStatus(id: string, status: string): Promise<Task> {
  return request<Task>(`/api/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}
