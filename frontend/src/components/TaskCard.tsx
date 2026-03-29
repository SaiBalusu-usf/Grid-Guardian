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
} from 'lucide-react';
import { cn, priorityColor, statusBadgeClasses } from '@/lib/utils';
import type { Task } from '@/lib/types';

interface TaskCardProps {
  task: Task;
}

const ASSIGNEE_ICONS: Record<string, typeof User> = {
  human: User,
  ai: Bot,
  drone: Radio,
  vehicle: Truck,
};

export default function TaskCard({ task }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const AssigneeIcon = ASSIGNEE_ICONS[task.assignee_type] || User;

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

        <button className="p-1 text-slate-500 hover:text-slate-300 transition-colors">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
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
