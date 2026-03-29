'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Bot,
  Wrench,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getMetrics } from '@/lib/api';
import type { MetricsData } from '@/lib/types';

function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton', className)} />;
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    red: 'bg-red-500/10 border-red-500/30 text-red-400',
    amber: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    blue: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    emerald: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    purple: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
  };
  const cc = colorClasses[color] || colorClasses.blue;
  const iconColor = cc.split(' ').pop() || 'text-blue-400';

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4 transition-all duration-200 hover:bg-slate-800/60">
      <div className="flex items-center gap-3">
        <div className={cn('flex h-9 w-9 items-center justify-center rounded-lg border', cc)}>
          <Icon className={cn('h-4 w-4', iconColor)} />
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">{label}</p>
          <p className="text-xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

function BarChart({
  items,
  maxValue,
  color,
  unit,
}: {
  items: { name: string; value: number }[];
  maxValue: number;
  color: string;
  unit: string;
}) {
  return (
    <div className="space-y-2.5">
      {items.map((item) => {
        const pct = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
        return (
          <div key={item.name} className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-40 truncate text-right shrink-0" title={item.name}>
              {item.name.replace(/_/g, ' ')}
            </span>
            <div className="flex-1 h-5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={cn('h-full rounded-full transition-all duration-700 ease-out', color)}
                style={{ width: `${Math.max(pct, 2)}%` }}
              />
            </div>
            <span className="text-xs text-slate-300 font-mono w-20 shrink-0">
              {item.value.toFixed(0)}{unit}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(() => {
    getMetrics()
      .then((data) => {
        setMetrics(data);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
          <span className="text-sm text-slate-400">Loading metrics...</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="p-6">
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={fetchMetrics}
            className="mt-3 px-4 py-1.5 rounded-lg bg-red-500/15 text-red-400 text-xs font-medium hover:bg-red-500/25 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const agentItems = Object.entries(metrics.agents).map(([name, data]) => ({
    name,
    value: data.avg_duration_ms,
    runs: data.total_runs,
    tokens: data.avg_tokens,
    errors: data.errors,
  }));
  const maxAgentDuration = Math.max(...agentItems.map((a) => a.value), 1);

  const toolItems = Object.entries(metrics.tools).map(([name, data]) => ({
    name,
    value: data.calls,
    avg_ms: data.avg_ms,
  }));
  const maxToolCalls = Math.max(...toolItems.map((t) => t.value), 1);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-emerald-400" />
          <h1 className="text-lg font-bold text-white">System Metrics</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Clock className="h-3 w-3" />
            Uptime: <span className="text-white font-medium">{formatUptime(metrics.uptime_seconds)}</span>
          </div>
          <button
            onClick={fetchMetrics}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/50 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="h-3 w-3" />
            Refresh
          </button>
        </div>
      </div>

      {/* Incident Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={Activity} label="Total Incidents" value={metrics.incidents.total} color="blue" />
        <StatCard icon={CheckCircle2} label="Completed" value={metrics.incidents.completed} color="emerald" />
        <StatCard icon={XCircle} label="Failed" value={metrics.incidents.failed} color="red" />
        <StatCard icon={AlertTriangle} label="Active" value={metrics.incidents.active} color="amber" />
      </div>

      {/* Agent Performance */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-white">Agent Performance</h2>
          <span className="text-[10px] text-slate-500 ml-auto">avg duration (ms)</span>
        </div>
        {agentItems.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">No agent data yet</p>
        ) : (
          <BarChart items={agentItems} maxValue={maxAgentDuration} color="bg-blue-500" unit="ms" />
        )}
        {agentItems.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-700/40">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {agentItems.map((agent) => (
                <div key={agent.name} className="text-center">
                  <p className="text-[10px] text-slate-500 truncate">{agent.name.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-white font-semibold">{agent.runs} runs</p>
                  <p className="text-[10px] text-slate-400">{agent.tokens} avg tokens</p>
                  {agent.errors > 0 && (
                    <p className="text-[10px] text-red-400">{agent.errors} errors</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tool Call Frequency */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Wrench className="h-4 w-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-white">Tool Call Frequency</h2>
          <span className="text-[10px] text-slate-500 ml-auto">total calls</span>
        </div>
        {toolItems.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-4">No tool data yet</p>
        ) : (
          <BarChart items={toolItems} maxValue={maxToolCalls} color="bg-purple-500" unit="" />
        )}
      </div>
    </div>
  );
}
