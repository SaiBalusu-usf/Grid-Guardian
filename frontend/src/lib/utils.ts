import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatTimestamp(iso: string): string {
  try {
    const date = new Date(iso);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return iso;
  }
}

export function timeAgo(iso: string): string {
  try {
    const now = Date.now();
    const then = new Date(iso).getTime();
    const seconds = Math.floor((now - then) / 1000);

    if (seconds < 5) return 'just now';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return iso;
  }
}

export function elapsedTime(startIso: string): string {
  try {
    const now = Date.now();
    const then = new Date(startIso).getTime();
    const seconds = Math.floor((now - then) / 1000);
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  } catch {
    return '...';
  }
}

export function severityColor(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'text-red-400';
    case 'high':
      return 'text-orange-400';
    case 'medium':
    case 'warning':
      return 'text-amber-400';
    case 'low':
      return 'text-emerald-400';
    case 'info':
      return 'text-blue-400';
    default:
      return 'text-slate-400';
  }
}

export function severityBg(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'bg-red-500/10 border-red-500/30';
    case 'high':
      return 'bg-orange-500/10 border-orange-500/30';
    case 'medium':
    case 'warning':
      return 'bg-amber-500/10 border-amber-500/30';
    case 'low':
      return 'bg-emerald-500/10 border-emerald-500/30';
    case 'info':
      return 'bg-blue-500/10 border-blue-500/30';
    default:
      return 'bg-slate-500/10 border-slate-500/30';
  }
}

export function severityBorder(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'border-l-red-500';
    case 'high':
      return 'border-l-orange-500';
    case 'medium':
    case 'warning':
      return 'border-l-amber-500';
    case 'low':
      return 'border-l-emerald-500';
    case 'info':
      return 'border-l-blue-500';
    default:
      return 'border-l-slate-500';
  }
}

export function severityGradient(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'from-red-600/20 to-red-900/10';
    case 'high':
      return 'from-orange-600/20 to-orange-900/10';
    case 'medium':
    case 'warning':
      return 'from-amber-600/20 to-amber-900/10';
    case 'low':
      return 'from-emerald-600/20 to-emerald-900/10';
    default:
      return 'from-blue-600/20 to-blue-900/10';
  }
}

export function priorityColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case 'critical':
      return 'text-red-400 bg-red-500/15 border-red-500/30';
    case 'high':
      return 'text-orange-400 bg-orange-500/15 border-orange-500/30';
    case 'medium':
      return 'text-amber-400 bg-amber-500/15 border-amber-500/30';
    case 'low':
      return 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
    default:
      return 'text-slate-400 bg-slate-500/15 border-slate-500/30';
  }
}

export function statusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'resolved':
    case 'acknowledged':
    case 'sent':
      return 'text-emerald-400';
    case 'in_progress':
    case 'running':
    case 'executing':
    case 'analyzing':
    case 'planning':
      return 'text-blue-400';
    case 'pending':
    case 'waiting':
    case 'monitoring':
      return 'text-amber-400';
    case 'cancelled':
    case 'error':
    case 'dismissed':
      return 'text-red-400';
    default:
      return 'text-slate-400';
  }
}

export function statusBadgeClasses(status: string): string {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'resolved':
    case 'acknowledged':
    case 'sent':
      return 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
    case 'in_progress':
    case 'running':
    case 'executing':
    case 'analyzing':
    case 'planning':
      return 'bg-blue-500/15 text-blue-400 border border-blue-500/30';
    case 'pending':
    case 'waiting':
    case 'monitoring':
      return 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
    case 'cancelled':
    case 'error':
    case 'dismissed':
      return 'bg-red-500/15 text-red-400 border border-red-500/30';
    default:
      return 'bg-slate-500/15 text-slate-400 border border-slate-500/30';
  }
}

export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs}s`;
}

export function agentDisplayName(name: string): string {
  const map: Record<string, string> = {
    hazard_watcher: 'Hazard Watcher',
    vulnerability_mapper: 'Vulnerability Mapper',
    route_planner: 'Route Planner',
    resource_coordinator: 'Resource Coordinator',
    public_alert: 'Public Alert',
    planner: 'Planner',
    audit: 'Audit Agent',
  };
  return map[name] || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function eventTypeIcon(eventType: string): string {
  const map: Record<string, string> = {
    trigger: '\u26A1',
    agent_start: '\uD83D\uDE80',
    agent_end: '\u2705',
    tool_call: '\uD83D\uDD27',
    audit: '\uD83D\uDD0D',
    a2a_request: '\uD83D\uDCE1',
    a2a_response: '\uD83D\uDCE5',
    plan_draft: '\uD83D\uDCCB',
    plan_final: '\u2705',
    action: '\u26A1',
  };
  return map[eventType] || '\u2022';
}

export function eventTypeColor(eventType: string): string {
  switch (eventType) {
    case 'trigger':
      return 'border-amber-400 bg-amber-400';
    case 'agent_start':
      return 'border-blue-400 bg-blue-400';
    case 'agent_end':
      return 'border-emerald-400 bg-emerald-400';
    case 'tool_call':
      return 'border-purple-400 bg-purple-400';
    case 'audit':
      return 'border-cyan-400 bg-cyan-400';
    case 'a2a_request':
      return 'border-orange-400 bg-orange-400';
    case 'a2a_response':
      return 'border-teal-400 bg-teal-400';
    case 'plan_draft':
      return 'border-indigo-400 bg-indigo-400';
    case 'plan_final':
      return 'border-emerald-400 bg-emerald-400';
    case 'action':
      return 'border-yellow-400 bg-yellow-400';
    default:
      return 'border-slate-400 bg-slate-400';
  }
}
