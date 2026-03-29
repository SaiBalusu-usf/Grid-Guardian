'use client';

import React, { createContext, useState, useEffect, useRef, useCallback } from 'react';
import type { Incident, TraceEvent, Task, Alert, AgentStatus } from '@/lib/types';

interface StreamingContextValue {
  connected: boolean;
  incident: Incident | null;
  traces: TraceEvent[];
  tasks: Task[];
  alerts: Alert[];
  agents: AgentStatus[];
  setActiveIncidentId: (id: string | null) => void;
  activeIncidentId: string | null;
}

export const StreamingContext = createContext<StreamingContextValue | null>(null);

export default function StreamingProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [traces, setTraces] = useState<TraceEvent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const es = new EventSource('/api/stream');
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnected(true);
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      es.addEventListener('incident_update', (e) => {
        try {
          const data = JSON.parse(e.data);
          setIncident(data);
        } catch {}
      });

      es.addEventListener('trace_event', (e) => {
        try {
          const data = JSON.parse(e.data);
          setTraces((prev) => [...prev, data]);
        } catch {}
      });

      es.addEventListener('task_update', (e) => {
        try {
          const data = JSON.parse(e.data);
          setTasks((prev) => {
            const idx = prev.findIndex((t) => t.id === data.id);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = data;
              return next;
            }
            return [...prev, data];
          });
        } catch {}
      });

      es.addEventListener('alert_update', (e) => {
        try {
          const data = JSON.parse(e.data);
          setAlerts((prev) => {
            const idx = prev.findIndex((a) => a.id === data.id);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = data;
              return next;
            }
            return [...prev, data];
          });
        } catch {}
      });

      es.addEventListener('agent_status', (e) => {
        try {
          const data = JSON.parse(e.data);
          setAgents((prev) => {
            const idx = prev.findIndex((a) => a.name === data.name);
            if (idx >= 0) {
              const next = [...prev];
              next[idx] = data;
              return next;
            }
            return [...prev, data];
          });
        } catch {}
      });

      es.addEventListener('plan_update', (e) => {
        try {
          const data = JSON.parse(e.data);
          setIncident((prev) =>
            prev ? { ...prev, final_plan: data.plan, status: data.status || prev.status } : prev
          );
        } catch {}
      });
    } catch {
      setConnected(false);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return (
    <StreamingContext.Provider
      value={{
        connected,
        incident,
        traces,
        tasks,
        alerts,
        agents,
        setActiveIncidentId,
        activeIncidentId,
      }}
    >
      {children}
    </StreamingContext.Provider>
  );
}
