'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Play, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { simulateIncident } from '@/lib/api';

interface SimulationButtonProps {
  scenario: string;
  triggerSource: string;
  children: React.ReactNode;
  className?: string;
}

export default function SimulationButton({
  scenario,
  triggerSource,
  children,
  className,
}: SimulationButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleLaunch() {
    if (loading) return;
    setLoading(true);
    setError(null);

    try {
      const result = await simulateIncident(scenario, triggerSource);
      const id = (result as any).incident_id || result.id;
      router.push(`/dashboard?incident=${id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start simulation');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleLaunch}
        disabled={loading}
        className={cn(
          'flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200',
          'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
          'hover:bg-emerald-500/25 hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10',
          'active:scale-[0.98]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          className
        )}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        {children}
      </button>
      {error && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-red-400">
          <AlertCircle className="h-3 w-3" />
          {error}
        </div>
      )}
    </div>
  );
}
