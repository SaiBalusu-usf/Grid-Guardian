'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Activity, Loader2, RefreshCw } from 'lucide-react';
import { useTrace, useIncident } from '@/lib/hooks';
import TraceTimeline from '@/components/TraceTimeline';
import IncidentBanner from '@/components/IncidentBanner';

function TraceContent() {
  const searchParams = useSearchParams();
  const incidentId = searchParams.get('incident');
  const { incident } = useIncident(incidentId);
  const { traces, loading, error } = useTrace(incidentId);

  const eventTypeCounts: Record<string, number> = {};
  traces.forEach((t) => {
    eventTypeCounts[t.event_type] = (eventTypeCounts[t.event_type] || 0) + 1;
  });

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {incident && <IncidentBanner incident={incident} />}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-blue-400" />
          <h1 className="text-lg font-bold text-white">Agent Trace Timeline</h1>
          <span className="text-xs text-slate-500">{traces.length} events</span>
        </div>
      </div>

      {/* Event type breakdown */}
      {traces.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          {Object.entries(eventTypeCounts)
            .sort((a, b) => b[1] - a[1])
            .map(([type, count]) => (
              <span
                key={type}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[10px] font-medium text-slate-300"
              >
                <span className="text-xs">
                  {type === 'trigger' ? '\u26A1' : type === 'agent_start' ? '\uD83D\uDE80' : type === 'agent_end' ? '\u2705' : type === 'tool_call' ? '\uD83D\uDD27' : type === 'audit' ? '\uD83D\uDD0D' : type === 'a2a_request' ? '\uD83D\uDCE1' : type === 'a2a_response' ? '\uD83D\uDCE5' : type === 'plan_draft' ? '\uD83D\uDCCB' : type === 'plan_final' ? '\u2705' : '\u26A1'}
                </span>
                {type.replace(/_/g, ' ')}
                <span className="font-bold text-white">{count}</span>
              </span>
            ))}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-blue-400 mb-3" />
          <p className="text-sm text-slate-400">Loading trace events...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : !incidentId ? (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-12 text-center">
          <Activity className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-white mb-1">No Incident Selected</h2>
          <p className="text-sm text-slate-400">
            Start a simulation to see the agent trace timeline in real time.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
          <TraceTimeline events={traces} maxHeight="calc(100vh - 350px)" autoScroll={true} />
        </div>
      )}
    </div>
  );
}

export default function TracePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <TraceContent />
    </Suspense>
  );
}
