'use client';

import { useState, useEffect } from 'react';
import {
  Settings,
  Server,
  ToggleLeft,
  ToggleRight,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  Radio,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStreaming } from '@/lib/hooks';
import DemoScenarios from '@/components/DemoScenarios';

export default function SettingsPage() {
  const { connected } = useStreaming();
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [mockMode, setMockMode] = useState(false);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    checkHealth();
  }, []);

  async function checkHealth() {
    setHealthStatus('checking');
    try {
      const res = await fetch('/api/dashboard', { signal: AbortSignal.timeout(5000) });
      setHealthStatus(res.ok ? 'online' : 'offline');
    } catch {
      setHealthStatus('offline');
    }
  }

  async function handleClear() {
    if (!confirm('Clear all simulation data? This cannot be undone.')) return;
    setClearing(true);
    // Simulate clearing
    await new Promise((r) => setTimeout(r, 1000));
    setClearing(false);
  }

  return (
    <div className="p-6 space-y-8 animate-fade-in max-w-4xl">
      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5 text-slate-400" />
        <h1 className="text-lg font-bold text-white">Settings & Demo Mode</h1>
      </div>

      {/* System Status */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="h-4 w-4 text-slate-400" />
          System Status
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-700/30">
            <div
              className={cn(
                'h-3 w-3 rounded-full',
                healthStatus === 'online'
                  ? 'bg-emerald-400'
                  : healthStatus === 'offline'
                    ? 'bg-red-400'
                    : 'bg-amber-400 animate-pulse'
              )}
            />
            <div>
              <p className="text-xs font-medium text-white">Backend API</p>
              <p className="text-[10px] text-slate-500 capitalize">{healthStatus}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-700/30">
            <div className={cn('h-3 w-3 rounded-full', connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400')} />
            <div>
              <p className="text-xs font-medium text-white">SSE Stream</p>
              <p className="text-[10px] text-slate-500">{connected ? 'Connected' : 'Disconnected'}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-700/30">
            <div className="h-3 w-3 rounded-full bg-emerald-400" />
            <div>
              <p className="text-xs font-medium text-white">Frontend</p>
              <p className="text-[10px] text-slate-500">Online</p>
            </div>
          </div>
        </div>

        <button
          onClick={checkHealth}
          className="mt-3 flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <Radio className="h-3 w-3" />
          Re-check status
        </button>
      </div>

      {/* Backend Config */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <h2 className="text-sm font-semibold text-white mb-4">Backend Configuration</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">API Base URL</label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700/50 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 focus:border-emerald-500/50"
              placeholder="http://localhost:8000"
            />
            <p className="text-[10px] text-slate-600 mt-1">
              The Next.js rewrite proxy forwards /api/* to this URL automatically.
            </p>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/40 border border-slate-700/30">
            <div>
              <p className="text-xs font-medium text-white">Mock Mode</p>
              <p className="text-[10px] text-slate-500">
                Use simulated responses when the backend is unavailable
              </p>
            </div>
            <button
              onClick={() => setMockMode(!mockMode)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              {mockMode ? (
                <ToggleRight className="h-7 w-7 text-emerald-400" />
              ) : (
                <ToggleLeft className="h-7 w-7" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <h2 className="text-sm font-semibold text-white mb-4">Launch Demo Scenario</h2>
        <p className="text-xs text-slate-400 mb-5">
          Select a pre-configured disaster scenario to demonstrate the multi-agent response pipeline.
        </p>
        <DemoScenarios />
      </div>

      {/* Data Management */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <h2 className="text-sm font-semibold text-white mb-4">Data Management</h2>

        <button
          onClick={handleClear}
          disabled={clearing}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
            'bg-red-500/10 text-red-400 border border-red-500/30',
            'hover:bg-red-500/20 hover:border-red-500/50',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {clearing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          Clear All Simulation Data
        </button>
        <p className="text-[10px] text-slate-600 mt-2">
          Removes all incidents, traces, tasks, and alerts from the database.
        </p>
      </div>
    </div>
  );
}
