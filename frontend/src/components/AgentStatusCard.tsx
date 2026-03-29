'use client';

import {
  Bot,
  CheckCircle,
  Loader2,
  Clock,
  AlertCircle,
  Wrench,
} from 'lucide-react';
import { cn, agentDisplayName, formatDuration } from '@/lib/utils';
import type { AgentStatus } from '@/lib/types';

interface AgentStatusCardProps {
  agent: AgentStatus;
}

const AGENT_ICONS: Record<string, string> = {
  triage_agent: '\uD83D\uDD0D',
  resource_agent: '\uD83D\uDCE6',
  alert_agent: '\uD83D\uDCE2',
  logistics_agent: '\uD83D\uDE9A',
  coordinator_agent: '\uD83C\uDFAF',
};

export default function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const statusConfig = {
    waiting: {
      icon: Clock,
      color: 'text-slate-400',
      bg: 'bg-slate-500/10',
      border: 'border-slate-500/20',
      label: 'Waiting',
    },
    running: {
      icon: Loader2,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      label: 'Running',
    },
    completed: {
      icon: CheckCircle,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      label: 'Completed',
    },
    error: {
      icon: AlertCircle,
      color: 'text-red-400',
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      label: 'Error',
    },
  };

  const config = statusConfig[agent.status] || statusConfig.waiting;
  const StatusIcon = config.icon;

  return (
    <div
      className={cn(
        'relative rounded-xl border p-4 transition-all duration-300',
        config.bg,
        config.border,
        agent.status === 'running' && 'ring-1 ring-blue-500/20'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{AGENT_ICONS[agent.name] || '\uD83E\uDD16'}</span>
          <div>
            <h3 className="text-sm font-semibold text-white">
              {agent.display_name || agentDisplayName(agent.name)}
            </h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <StatusIcon
                className={cn(
                  'h-3 w-3',
                  config.color,
                  agent.status === 'running' && 'animate-spin'
                )}
              />
              <span className={cn('text-xs font-medium', config.color)}>
                {config.label}
              </span>
            </div>
          </div>
        </div>

        {agent.duration_ms !== undefined && (
          <span className="text-[10px] font-mono text-slate-500">
            {formatDuration(agent.duration_ms)}
          </span>
        )}
      </div>

      {agent.summary && (
        <p className="mt-2.5 text-xs text-slate-400 line-clamp-2 leading-relaxed">
          {agent.summary}
        </p>
      )}

      {agent.tool_calls !== undefined && agent.tool_calls > 0 && (
        <div className="mt-2 flex items-center gap-1 text-[10px] text-slate-500">
          <Wrench className="h-3 w-3" />
          {agent.tool_calls} tool call{agent.tool_calls !== 1 ? 's' : ''}
        </div>
      )}

      {agent.status === 'running' && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 overflow-hidden rounded-b-xl">
          <div className="h-full w-1/3 bg-blue-400/60 animate-shimmer rounded-full" style={{ backgroundSize: '200% 100%' }} />
        </div>
      )}
    </div>
  );
}
