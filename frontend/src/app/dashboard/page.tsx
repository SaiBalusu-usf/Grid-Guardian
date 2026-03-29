'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  Activity,
  ListTodo,
  Bell,
  Building2,
  Shield,
  Map,
  ChevronRight,
  Users,
  Clock,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { useIncident, useTrace, useTasks, useAlerts, useDashboard, useStreaming } from '@/lib/hooks';
import { cn, severityColor, formatConfidence, statusBadgeClasses, severityBg } from '@/lib/utils';
import IncidentBanner from '@/components/IncidentBanner';
import AgentStatusCard from '@/components/AgentStatusCard';
import TraceTimeline from '@/components/TraceTimeline';
import type { AgentStatus } from '@/lib/types';

function Skeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton', className)} />;
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  sub?: string;
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
          {sub && <p className="text-[10px] text-slate-500">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const incidentId = searchParams.get('incident');
  const { incident, loading: incidentLoading } = useIncident(incidentId);
  const { traces } = useTrace(incidentId);
  const { tasks } = useTasks(incidentId);
  const { alerts } = useAlerts(incidentId);
  const { data: dashboard, loading: dashLoading } = useDashboard();
  const { agents, setActiveIncidentId } = useStreaming();

  useEffect(() => {
    if (incidentId) {
      setActiveIncidentId(incidentId);
    }
  }, [incidentId, setActiveIncidentId]);

  const pendingTasks = tasks.filter((t) => t.status === 'pending').length;
  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const activeAlerts = alerts.filter((a) => a.status !== 'acknowledged' && a.status !== 'dismissed').length;

  const defaultAgents: AgentStatus[] = useMemo(() => {
    const names: Array<{ name: string; display_name: string }> = [
      { name: 'hazard_watcher', display_name: 'Hazard Watcher' },
      { name: 'vulnerability_mapper', display_name: 'Vulnerability Mapper' },
      { name: 'route_planner', display_name: 'Route Planner' },
      { name: 'resource_coordinator', display_name: 'Resource Coordinator' },
      { name: 'public_alert', display_name: 'Public Alert' },
      { name: 'planner', display_name: 'Planner' },
      { name: 'audit', display_name: 'Audit Agent' },
    ];
    return names.map((a) => {
      const existing = agents.find((ag) => ag.name === a.name);
      return (
        existing || {
          name: a.name as any,
          display_name: a.display_name,
          status: 'waiting' as const,
        }
      );
    });
  }, [agents]);

  const shelterOccupancy = dashboard
    ? dashboard.shelter_capacity > 0
      ? Math.round((dashboard.shelter_occupancy / dashboard.shelter_capacity) * 100)
      : 0
    : 0;

  if (incidentLoading && incidentId) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 lg:col-span-2" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Incident Banner */}
      {incident && <IncidentBanner incident={incident} />}

      {!incident && !incidentId && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-8 text-center">
          <Shield className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-white mb-1">No Active Incident</h2>
          <p className="text-sm text-slate-400 mb-4">
            Launch a simulation from the{' '}
            <Link href="/" className="text-emerald-400 hover:underline">
              home page
            </Link>{' '}
            or the{' '}
            <Link href="/settings" className="text-emerald-400 hover:underline">
              settings
            </Link>{' '}
            panel.
          </p>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          icon={AlertTriangle}
          label="Severity"
          value={incident?.severity?.toUpperCase() || dashboard?.active_incidents?.toString() || '--'}
          sub={incident ? `Confidence: ${formatConfidence(incident.confidence)}` : 'active incidents'}
          color="red"
        />
        <StatCard
          icon={TrendingUp}
          label="Confidence"
          value={incident ? formatConfidence(incident.confidence) : '--'}
          sub="AI assessment"
          color="blue"
        />
        <StatCard
          icon={ListTodo}
          label="Tasks"
          value={tasks.length || dashboard?.total_tasks || 0}
          sub={`${pendingTasks} pending, ${completedTasks} done`}
          color="purple"
        />
        <StatCard
          icon={Bell}
          label="Alerts"
          value={alerts.length || dashboard?.active_alerts || 0}
          sub={`${activeAlerts} active`}
          color="amber"
        />
        <StatCard
          icon={Building2}
          label="Shelters"
          value={`${shelterOccupancy}%`}
          sub={dashboard ? `${dashboard.shelter_occupancy}/${dashboard.shelter_capacity}` : 'occupancy'}
          color="emerald"
        />
        <StatCard
          icon={Activity}
          label="Trace Events"
          value={traces.length}
          sub="agent events"
          color="blue"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="h-4 w-4 text-slate-400" />
              Agent Status
            </h3>
            {incident && (
              <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-medium', statusBadgeClasses(incident.status))}>
                {incident.status.replace('_', ' ')}
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
            {defaultAgents.map((agent) => (
              <AgentStatusCard key={agent.name} agent={agent} />
            ))}
          </div>
        </div>

        {/* Trace Feed */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-400" />
              Live Trace
            </h3>
            {incidentId && (
              <Link
                href={`/trace?incident=${incidentId}`}
                className="flex items-center gap-1 text-[10px] text-emerald-400 hover:underline"
              >
                Full trace <ChevronRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
            <TraceTimeline events={traces.slice(-15)} maxHeight="380px" />
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { href: incidentId ? `/map?incident=${incidentId}` : '/map', icon: Map, label: 'Operations Map', iconColor: 'text-emerald-400' },
          { href: incidentId ? `/trace?incident=${incidentId}` : '/trace', icon: Activity, label: 'Full Trace', iconColor: 'text-blue-400' },
          { href: incidentId ? `/alerts?incident=${incidentId}` : '/alerts', icon: Bell, label: 'Alert Center', iconColor: 'text-amber-400' },
          { href: incidentId ? `/tasks?incident=${incidentId}` : '/tasks', icon: ListTodo, label: 'Task Board', iconColor: 'text-purple-400' },
        ].map(({ href, icon: Icon, label, iconColor }) => (
          <Link
            key={label}
            href={href}
            className={cn(
              'flex items-center gap-3 p-3.5 rounded-xl border border-slate-700/50 bg-slate-800/40 transition-all duration-200 hover:bg-slate-800/70 hover:border-slate-600/50 group'
            )}
          >
            <Icon className={cn('h-5 w-5', iconColor)} />
            <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
              {label}
            </span>
            <ChevronRight className="h-4 w-4 text-slate-600 ml-auto group-hover:text-slate-400 transition-colors" />
          </Link>
        ))}
      </div>

      {/* Recent Incidents */}
      {dashboard && dashboard.recent_incidents.length > 0 && !incidentId && (
        <div>
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-400" />
            Recent Incidents
          </h3>
          <div className="space-y-2">
            {dashboard.recent_incidents.map((inc) => (
              <Link
                key={inc.id}
                href={`/dashboard?incident=${inc.id}`}
                className="flex items-center gap-4 p-3 rounded-xl border border-slate-700/50 bg-slate-800/40 hover:bg-slate-800/70 transition-all duration-200 group"
              >
                <div className={cn('h-2 w-2 rounded-full', inc.severity === 'critical' ? 'bg-red-400' : inc.severity === 'high' ? 'bg-orange-400' : 'bg-amber-400')} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{inc.scenario}</p>
                  <p className="text-[10px] text-slate-500">{inc.status} -- {inc.id.slice(0, 8)}</p>
                </div>
                <span className={cn('text-[10px] font-bold uppercase', severityColor(inc.severity))}>
                  {inc.severity}
                </span>
                <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-slate-400" />
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  );
}
