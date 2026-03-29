'use client';

import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Clock,
  Activity,
  Shield,
  ChevronRight,
} from 'lucide-react';
import { cn, severityGradient, severityColor, formatConfidence, elapsedTime, statusBadgeClasses } from '@/lib/utils';
import type { Incident } from '@/lib/types';

interface IncidentBannerProps {
  incident: Incident;
}

export default function IncidentBanner({ incident }: IncidentBannerProps) {
  const [elapsed, setElapsed] = useState('');

  useEffect(() => {
    const update = () => setElapsed(elapsedTime(incident.started_at));
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [incident.started_at]);

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border bg-gradient-to-r p-4',
        severityGradient(incident.severity),
        incident.severity === 'critical'
          ? 'border-red-500/30'
          : incident.severity === 'high'
            ? 'border-orange-500/30'
            : 'border-amber-500/30'
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-white/[0.03] to-transparent" />

      <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={cn(
              'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
              incident.severity === 'critical'
                ? 'bg-red-500/20'
                : incident.severity === 'high'
                  ? 'bg-orange-500/20'
                  : 'bg-amber-500/20'
            )}
          >
            <AlertTriangle
              className={cn(
                'h-5 w-5',
                severityColor(incident.severity)
              )}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-sm font-semibold text-white truncate">
                {incident.scenario}
              </h2>
              <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest', statusBadgeClasses(incident.status))}>
                {incident.status.replace('_', ' ')}
              </span>
            </div>
            <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-300">
              <span className="flex items-center gap-1">
                <Shield className="h-3 w-3" />
                Severity: <span className={cn('font-semibold uppercase', severityColor(incident.severity))}>{incident.severity}</span>
              </span>
              <span className="flex items-center gap-1">
                <Activity className="h-3 w-3" />
                Confidence: <span className="font-semibold text-white">{formatConfidence(incident.confidence)}</span>
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Elapsed: <span className="font-semibold text-white">{elapsed}</span>
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {incident.impacted_zones.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              {incident.impacted_zones.slice(0, 3).map((zone) => (
                <span
                  key={zone}
                  className="px-2 py-0.5 rounded-md bg-slate-800/60 border border-slate-600/40 text-[10px] font-medium text-slate-300"
                >
                  {zone}
                </span>
              ))}
              {incident.impacted_zones.length > 3 && (
                <span className="text-[10px] text-slate-400">
                  +{incident.impacted_zones.length - 3} more
                </span>
              )}
            </div>
          )}
          <ChevronRight className="h-4 w-4 text-slate-500 hidden md:block" />
        </div>
      </div>
    </div>
  );
}
