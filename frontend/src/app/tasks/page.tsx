'use client';

import { Suspense, useState, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { ListTodo, Loader2, ArrowUpDown } from 'lucide-react';
import { useTasks, useIncident } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import TaskCard from '@/components/TaskCard';
import IncidentBanner from '@/components/IncidentBanner';
import type { Task } from '@/lib/types';

const PRIORITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const COLUMNS: { key: string; label: string; color: string }[] = [
  { key: 'pending', label: 'Pending', color: 'amber' },
  { key: 'in_progress', label: 'In Progress', color: 'blue' },
  { key: 'completed', label: 'Completed', color: 'emerald' },
];

function sortByPriority(tasks: Task[]): Task[] {
  return [...tasks].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99)
  );
}

function TaskColumn({ title, tasks, color }: { title: string; tasks: Task[]; color: string }) {
  const colorMap: Record<string, string> = {
    amber: 'border-amber-500/30 text-amber-400',
    blue: 'border-blue-500/30 text-blue-400',
    emerald: 'border-emerald-500/30 text-emerald-400',
  };
  const cc = colorMap[color] || colorMap.blue;

  return (
    <div className="flex flex-col min-h-0">
      <div className={cn('flex items-center gap-2 pb-3 mb-3 border-b', cc.split(' ')[0])}>
        <div className={cn('h-2 w-2 rounded-full', `bg-${color}-400`)} />
        <h3 className={cn('text-sm font-semibold', cc.split(' ')[1] || 'text-white')}>
          {title}
        </h3>
        <span className="ml-auto text-[10px] font-medium text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded-full">
          {tasks.length}
        </span>
      </div>
      <div className="space-y-2 overflow-y-auto flex-1 custom-scrollbar pr-1" style={{ maxHeight: 'calc(100vh - 340px)' }}>
        {tasks.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-xs text-slate-600">No tasks</p>
          </div>
        ) : (
          tasks.map((task) => <TaskCard key={task.id} task={task} />)
        )}
      </div>
    </div>
  );
}

function TasksContent() {
  const searchParams = useSearchParams();
  const incidentId = searchParams.get('incident');
  const { incident } = useIncident(incidentId);
  const { tasks, loading, error } = useTasks(incidentId);
  const [sortByPriorityEnabled, setSortByPriorityEnabled] = useState(true);

  const columns = useMemo(() => {
    return COLUMNS.map((col) => {
      const colTasks = tasks.filter((t) => t.status === col.key);
      return {
        ...col,
        tasks: sortByPriorityEnabled ? sortByPriority(colTasks) : colTasks,
      };
    });
  }, [tasks, sortByPriorityEnabled]);

  // Capture tasks with unknown status
  const otherTasks = useMemo(() => {
    const knownStatuses = new Set(COLUMNS.map((c) => c.key));
    return tasks.filter((t) => !knownStatuses.has(t.status));
  }, [tasks]);

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {incident && <IncidentBanner incident={incident} />}

      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <ListTodo className="h-5 w-5 text-purple-400" />
          <h1 className="text-lg font-bold text-white">Task Board</h1>
          <span className="text-xs text-slate-500">{tasks.length} total</span>
        </div>

        <button
          onClick={() => setSortByPriorityEnabled(!sortByPriorityEnabled)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
            sortByPriorityEnabled
              ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
              : 'bg-slate-800 text-slate-400 border border-slate-700/50 hover:text-white'
          )}
        >
          <ArrowUpDown className="h-3 w-3" />
          Sort by Priority
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-purple-400 mb-3" />
          <p className="text-sm text-slate-400">Loading tasks...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-12 text-center">
          <ListTodo className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-white mb-1">No Tasks</h2>
          <p className="text-sm text-slate-400">
            Tasks will appear here as agents create them during incident response.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {columns.map((col) => (
            <TaskColumn
              key={col.key}
              title={col.label}
              tasks={col.tasks}
              color={col.color}
            />
          ))}
        </div>
      )}

      {otherTasks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-400 mb-2">Other Tasks</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {otherTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function TasksPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <TasksContent />
    </Suspense>
  );
}
