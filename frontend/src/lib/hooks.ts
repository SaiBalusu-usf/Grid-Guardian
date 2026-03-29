'use client';

import { useState, useEffect, useCallback, useContext } from 'react';
import { getIncident, getTrace, getTasks, getAlerts, getDashboard } from './api';
import type { Incident, TraceEvent, Task, Alert, DashboardData } from './types';
import { StreamingContext } from '@/components/StreamingProvider';

export function useStreaming() {
  const ctx = useContext(StreamingContext);
  if (!ctx) {
    throw new Error('useStreaming must be used within a StreamingProvider');
  }
  return ctx;
}

export function useIncident(id: string | null) {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { incident: streamIncident } = useStreaming();

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    getIncident(id)
      .then(setIncident)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (streamIncident && streamIncident.id === id) {
      setIncident(streamIncident);
    }
  }, [streamIncident, id]);

  const refetch = useCallback(() => {
    if (!id) return;
    getIncident(id).then(setIncident).catch(() => {});
  }, [id]);

  return { incident, loading, error, refetch };
}

export function useTrace(incidentId: string | null) {
  const [traces, setTraces] = useState<TraceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { traces: streamTraces } = useStreaming();

  useEffect(() => {
    if (!incidentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    getTrace(incidentId)
      .then(setTraces)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [incidentId]);

  useEffect(() => {
    if (streamTraces.length > 0) {
      setTraces((prev) => {
        const ids = new Set(prev.map((t) => t.id));
        const newOnes = streamTraces.filter((t) => !ids.has(t.id));
        return newOnes.length > 0 ? [...prev, ...newOnes] : prev;
      });
    }
  }, [streamTraces]);

  return { traces, loading, error };
}

export function useTasks(incidentId?: string | null) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { tasks: streamTasks } = useStreaming();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getTasks(incidentId || undefined)
      .then(setTasks)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [incidentId]);

  useEffect(() => {
    if (streamTasks.length > 0) {
      setTasks((prev) => {
        const map = new Map(prev.map((t) => [t.id, t]));
        streamTasks.forEach((t) => map.set(t.id, t));
        return Array.from(map.values());
      });
    }
  }, [streamTasks]);

  return { tasks, loading, error };
}

export function useAlerts(incidentId?: string | null) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { alerts: streamAlerts } = useStreaming();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getAlerts(incidentId || undefined)
      .then(setAlerts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [incidentId]);

  useEffect(() => {
    if (streamAlerts.length > 0) {
      setAlerts((prev) => {
        const map = new Map(prev.map((a) => [a.id, a]));
        streamAlerts.forEach((a) => map.set(a.id, a));
        return Array.from(map.values());
      });
    }
  }, [streamAlerts]);

  const refetchAlerts = useCallback(() => {
    getAlerts(incidentId || undefined).then(setAlerts).catch(() => {});
  }, [incidentId]);

  return { alerts, loading, error, refetchAlerts };
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
