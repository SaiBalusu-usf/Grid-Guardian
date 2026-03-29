export interface Incident {
  id: string;
  scenario: string;
  trigger_source: string;
  started_at: string;
  severity: string;
  confidence: number;
  impacted_zones: string[];
  status: string;
  final_plan: Record<string, any> | null;
}

export interface TraceEvent {
  id: string;
  incident_id: string;
  event_type: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface Task {
  id: string;
  incident_id: string;
  title: string;
  priority: string;
  location: string;
  assignee_type: string;
  status: string;
}

export interface Alert {
  id: string;
  incident_id: string;
  message: string;
  language: string;
  severity: string;
  region: string;
  status: string;
  sent_at: string | null;
}

export interface Shelter {
  shelter_id: string;
  name: string;
  capacity: number;
  occupancy: number;
  accessibility: string;
  supplies: Record<string, number>;
}

export interface DashboardData {
  active_incidents: number;
  total_tasks: number;
  pending_tasks: number;
  active_alerts: number;
  shelter_capacity: number;
  shelter_occupancy: number;
  recent_incidents: Incident[];
}

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type IncidentStatus = 'analyzing' | 'planning' | 'executing' | 'monitoring' | 'resolved' | 'closed';
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';
export type AlertStatus = 'pending' | 'sent' | 'acknowledged' | 'dismissed';

export type AgentName =
  | 'hazard_watcher'
  | 'vulnerability_mapper'
  | 'route_planner'
  | 'resource_coordinator'
  | 'public_alert'
  | 'planner'
  | 'audit';

export type EventType =
  | 'trigger'
  | 'agent_start'
  | 'agent_end'
  | 'tool_call'
  | 'audit'
  | 'a2a_request'
  | 'a2a_response'
  | 'plan_draft'
  | 'plan_final'
  | 'action';

export interface AgentStatus {
  name: AgentName;
  display_name: string;
  status: 'waiting' | 'running' | 'completed' | 'error';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  tool_calls?: number;
  summary?: string;
}

export interface StreamEvent {
  type: string;
  data: any;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  scenario: string;
  trigger_source: string;
}
