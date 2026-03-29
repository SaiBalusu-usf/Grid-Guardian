'use client';

import { useState } from 'react';
import {
  MapPin,
  ChevronDown,
  ChevronUp,
  User,
  Bot,
  Truck,
  Radio,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { cn, priorityColor, statusBadgeClasses } from '@/lib/utils';
import { updateTaskStatus } from '@/lib/api';
import type { Task } from '@/lib/types';

interface TaskCardProps {
  task: Task;
  onStatusUpdate?: (task: Task) => void;
}

const ASSIGNEE_ICONS: Record<string, typeof User> = {
  human: User,
  ai: Bot,
  drone: Radio,
  vehicle: Truck,
};

const STATUS_FLOW: Record<string, string> = {
  pending: 'in_progress',
  in_progress: 'completed',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Start',
  in_progress: 'Complete',
};

export default function TaskCard({ task, onStatusUpdate }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);
  const AssigneeIcon = ASSIGNEE_ICONS[task.assignee_type] || User;

  const nextStatus = STATUS_FLOW[task.status];
  const canAdvance = !!nextStatus;

  const handleAdvance = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!nextStatus || updating) return;
    setUpdating(true);
    try {
      const updated = await updateTaskStatus(task.id, nextStatus);
      if (onStatusUpdate) {
        onStatusUpdate(updated);
      }
    } catch (err) {
      console.error('Failed to update task status:', err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div
      className={cn(
        'rounded-xl border border-slate-700/50 bg-slate-800/60 p-3.5 transition-all duration-200 hover:bg-slate-800/80 cursor-pointer',
        task.status === 'completed' && 'opacity-70'
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span
              className={cn(
                'inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border',
                priorityColor(task.priority)
              )}
            >
              {task.priority}
            </span>
            <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-medium', statusBadgeClasses(task.status))}>
              {task.status.replace('_', ' ')}
            </span>
          </div>

          <h3 className="text-sm font-medium text-white leading-snug">{task.title}</h3>

          <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {task.location}
            </span>
            <span className="flex items-center gap-1">
              <AssigneeIcon className="h-3 w-3" />
              {task.assignee_type}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {canAdvance && (
            <button
              onClick={handleAdvance}
              disabled={updating}
              className={cn(
                'flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-colors',
                task.status === 'pending'
                  ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30 hover:bg-blue-500/25'
                  : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25',
                updating && 'opacity-50 cursor-not-allowed'
              )}
            >
              {updating ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <>
                  {STATUS_LABELS[task.status]}
                  <ArrowRight className="h-3 w-3" />
                </>
              )}
            </button>
          )}
          <button className="p-1 text-slate-500 hover:text-slate-300 transition-colors">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-slate-700/40 animate-fade-in">
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-slate-500 text-[10px] uppercase tracking-wider">ID</dt>
              <dd className="text-slate-300 font-mono text-[11px] truncate">{task.id}</dd>
            </div>
            <div>
              <dt className="text-slate-500 text-[10px] uppercase tracking-wider">Incident</dt>
              <dd className="text-slate-300 font-mono text-[11px] truncate">{task.incident_id}</dd>
            </div>
            <div>
              <dt className="text-slate-500 text-[10px] uppercase tracking-wider">Location</dt>
              <dd className="text-slate-300">{task.location}</dd>
            </div>
            <div>
              <dt className="text-slate-500 text-[10px] uppercase tracking-wider">Assignee</dt>
              <dd className="text-slate-300 capitalize">{task.assignee_type}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
