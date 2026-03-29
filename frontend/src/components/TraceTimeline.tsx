'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn, timeAgo, formatTimestamp, eventTypeIcon, eventTypeColor } from '@/lib/utils';
import type { TraceEvent } from '@/lib/types';

interface TraceTimelineProps {
  events: TraceEvent[];
  maxHeight?: string;
  autoScroll?: boolean;
}

function TimeBetween({ prev, current }: { prev: string; current: string }) {
  const ms = new Date(current).getTime() - new Date(prev).getTime();
  if (ms < 0 || isNaN(ms)) return null;

  let display: string;
  if (ms < 1000) display = `${ms}ms`;
  else if (ms < 60000) display = `${(ms / 1000).toFixed(1)}s`;
  else display = `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;

  return (
    <div className="flex items-center gap-2 py-0.5 pl-4">
      <div className="w-3 border-l-2 border-dashed border-slate-700 h-4" />
      <span className="text-[10px] font-mono text-slate-600">{display}</span>
    </div>
  );
}

function TraceNode({ event, prevTimestamp }: { event: TraceEvent; prevTimestamp?: string }) {
  const [expanded, setExpanded] = useState(false);
  const dotColor = eventTypeColor(event.event_type);
  const icon = eventTypeIcon(event.event_type);
  const hasPayload = event.payload && Object.keys(event.payload).length > 0;

  return (
    <div className="animate-fade-in">
      {prevTimestamp && <TimeBetween prev={prevTimestamp} current={event.timestamp} />}
      <div
        className={cn(
          'group flex items-start gap-3 py-1.5 px-2 rounded-lg cursor-pointer transition-colors hover:bg-slate-800/40',
          expanded && 'bg-slate-800/30'
        )}
        onClick={() => hasPayload && setExpanded(!expanded)}
      >
        <div className="relative flex flex-col items-center pt-0.5">
          <div
            className={cn(
              'h-3 w-3 rounded-full border-2 shrink-0',
              dotColor
            )}
          />
          <div className="w-0.5 flex-1 bg-slate-700/50 mt-1" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm">{icon}</span>
            <span className="text-xs font-semibold text-white">
              {event.event_type.replace(/_/g, ' ')}
            </span>
            {hasPayload && (
              expanded ? (
                <ChevronDown className="h-3 w-3 text-slate-500" />
              ) : (
                <ChevronRight className="h-3 w-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              )
            )}
            <span className="ml-auto text-[10px] font-mono text-slate-500 shrink-0">
              {timeAgo(event.timestamp)}
            </span>
          </div>

          {event.payload?.agent && (
            <span className="text-[10px] text-slate-400 mt-0.5 block">
              Agent: {event.payload.agent}
            </span>
          )}
          {event.payload?.tool && (
            <span className="text-[10px] text-slate-400 mt-0.5 block">
              Tool: {event.payload.tool}
            </span>
          )}
          {event.payload?.message && !expanded && (
            <p className="text-[10px] text-slate-500 mt-0.5 truncate">
              {event.payload.message}
            </p>
          )}

          {expanded && hasPayload && (
            <div className="mt-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/40">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                  Payload
                </span>
                <span className="text-[10px] font-mono text-slate-500">
                  {formatTimestamp(event.timestamp)}
                </span>
              </div>
              <pre className="text-[11px] text-slate-300 font-mono whitespace-pre-wrap break-all leading-relaxed overflow-x-auto">
                {JSON.stringify(event.payload, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function TraceTimeline({ events, maxHeight = '600px', autoScroll = true }: TraceTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events.length, autoScroll]);

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-500">
        <div className="h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center mb-3">
          <div className="h-3 w-3 rounded-full bg-slate-600" />
        </div>
        <p className="text-sm">No trace events yet</p>
        <p className="text-xs mt-1">Events will appear here in real time</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="overflow-y-auto pr-1 custom-scrollbar"
      style={{ maxHeight }}
    >
      <div className="space-y-0">
        {events.map((event, i) => (
          <TraceNode
            key={event.id}
            event={event}
            prevTimestamp={i > 0 ? events[i - 1].timestamp : undefined}
          />
        ))}
      </div>
    </div>
  );
}
