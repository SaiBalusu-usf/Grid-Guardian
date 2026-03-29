'use client';

import { cn } from '@/lib/utils';

interface WorkflowProgressProps {
  currentStage: string;
}

const STAGES = [
  { key: 'initiated', label: 'Trigger' },
  { key: 'analyzing', label: 'Analyzing' },
  { key: 'planning', label: 'Planning' },
  { key: 'auditing', label: 'Auditing' },
  { key: 'executing', label: 'Executing' },
  { key: 'completed', label: 'Complete' },
];

export default function WorkflowProgress({ currentStage }: WorkflowProgressProps) {
  const stageIndex = STAGES.findIndex((s) => s.key === currentStage);
  // For failed/cancelled, treat as last active stage
  const effectiveIndex = currentStage === 'failed' || currentStage === 'cancelled'
    ? STAGES.length
    : stageIndex;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
      <div className="flex items-center gap-0.5">
        {STAGES.map((stage, i) => {
          const isDone = effectiveIndex > i;
          const isActive = effectiveIndex === i;
          const isFailed = (currentStage === 'failed' || currentStage === 'cancelled') && i === STAGES.length - 1;

          return (
            <div key={stage.key} className="flex-1 flex flex-col items-center">
              <div
                className={cn(
                  'h-2 w-full rounded-full transition-all duration-500',
                  isDone && 'bg-emerald-500',
                  isActive && 'bg-blue-500 animate-pulse',
                  !isDone && !isActive && 'bg-slate-700',
                  isFailed && 'bg-red-500',
                  i === 0 && 'rounded-l-full',
                  i === STAGES.length - 1 && 'rounded-r-full'
                )}
              />
              <span
                className={cn(
                  'mt-1.5 text-[10px] font-medium transition-colors',
                  isDone && 'text-emerald-400',
                  isActive && 'text-blue-400',
                  !isDone && !isActive && 'text-slate-600',
                  isFailed && 'text-red-400'
                )}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
