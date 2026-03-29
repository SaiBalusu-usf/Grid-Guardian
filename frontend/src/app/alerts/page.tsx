'use client';

import { Suspense, useState, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { Bell, Filter, Loader2 } from 'lucide-react';
import { useAlerts, useIncident } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import AlertCard from '@/components/AlertCard';
import IncidentBanner from '@/components/IncidentBanner';
import type { Alert } from '@/lib/types';

function AlertsContent() {
  const searchParams = useSearchParams();
  const incidentId = searchParams.get('incident');
  const { incident } = useIncident(incidentId);
  const { alerts, loading, error, refetchAlerts } = useAlerts(incidentId);

  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filtered = useMemo(() => {
    return alerts.filter((a) => {
      if (severityFilter !== 'all' && a.severity !== severityFilter) return false;
      if (statusFilter !== 'all' && a.status !== statusFilter) return false;
      return true;
    });
  }, [alerts, severityFilter, statusFilter]);

  // Group by message for bilingual display
  const grouped = useMemo(() => {
    const groups: Map<string, Alert[]> = new Map();
    filtered.forEach((a) => {
      const key = `${a.incident_id}-${a.region}-${a.severity}`;
      const existing = groups.get(key) || [];
      existing.push(a);
      groups.set(key, existing);
    });
    return Array.from(groups.values());
  }, [filtered]);

  const severities = ['all', ...Array.from(new Set(alerts.map((a) => a.severity)))];
  const statuses = ['all', ...Array.from(new Set(alerts.map((a) => a.status)))];

  function handleAcknowledged() {
    refetchAlerts();
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {incident && <IncidentBanner incident={incident} />}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-amber-400" />
          <h1 className="text-lg font-bold text-white">Alert Center</h1>
          <span className="text-xs text-slate-500">{alerts.length} total</span>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-3.5 w-3.5 text-slate-500" />

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/50 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
          >
            {severities.map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? 'All Severities' : s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/50 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
          >
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s === 'all' ? 'All Statuses' : s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-amber-400 mb-3" />
          <p className="text-sm text-slate-400">Loading alerts...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-12 text-center">
          <Bell className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-white mb-1">No Alerts</h2>
          <p className="text-sm text-slate-400">
            {alerts.length > 0
              ? 'No alerts match your current filters.'
              : 'Alerts will appear here when the system generates them.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {grouped.map((group, i) => {
            if (group.length > 1) {
              // Bilingual pair
              return (
                <div key={i} className="space-y-2">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {group.map((alert) => (
                      <AlertCard
                        key={alert.id}
                        alert={alert}
                        onAcknowledged={handleAcknowledged}
                      />
                    ))}
                  </div>
                </div>
              );
            }
            return (
              <AlertCard
                key={group[0].id}
                alert={group[0]}
                onAcknowledged={handleAcknowledged}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function AlertsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <AlertsContent />
    </Suspense>
  );
}
