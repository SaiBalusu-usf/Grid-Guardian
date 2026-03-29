'use client';

import {
  Building2,
  Users,
  Accessibility,
  Package,
  Zap,
  Heart,
  PawPrint,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Shelter } from '@/lib/types';

interface ShelterPanelProps {
  shelter: Shelter;
}

export default function ShelterPanel({ shelter }: ShelterPanelProps) {
  const occupancyPercent =
    shelter.capacity > 0 ? (shelter.occupancy / shelter.capacity) * 100 : 0;

  let barColor = 'bg-emerald-500';
  let barBg = 'bg-emerald-500/10';
  if (occupancyPercent > 80) {
    barColor = 'bg-red-500';
    barBg = 'bg-red-500/10';
  } else if (occupancyPercent > 60) {
    barColor = 'bg-amber-500';
    barBg = 'bg-amber-500/10';
  }

  const supplies = Object.entries(shelter.supplies || {});

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/60 p-4 transition-all duration-200 hover:bg-slate-800/80">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/15 border border-blue-500/30">
            <Building2 className="h-4.5 w-4.5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{shelter.name}</h3>
            <span className="text-[10px] font-mono text-slate-500">{shelter.shelter_id}</span>
          </div>
        </div>

        <span
          className={cn(
            'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border',
            shelter.accessibility === 'full'
              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              : shelter.accessibility === 'partial'
                ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                : 'bg-slate-500/15 text-slate-400 border-slate-500/30'
          )}
        >
          <Accessibility className="h-2.5 w-2.5" />
          {shelter.accessibility}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="flex items-center gap-1 text-xs text-slate-400">
            <Users className="h-3 w-3" />
            Capacity
          </span>
          <span className="text-xs font-semibold text-white">
            {shelter.occupancy} / {shelter.capacity}
          </span>
        </div>
        <div className={cn('h-2.5 w-full rounded-full overflow-hidden', barBg)}>
          <div
            className={cn(
              'h-full rounded-full transition-all duration-500 ease-out',
              barColor
            )}
            style={{ width: `${Math.min(occupancyPercent, 100)}%` }}
          />
        </div>
        <span className="text-[10px] text-slate-500 mt-1 block text-right">
          {occupancyPercent.toFixed(0)}% occupied
        </span>
      </div>

      {supplies.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-700/40">
          <div className="flex items-center gap-1 mb-2">
            <Package className="h-3 w-3 text-slate-400" />
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium">
              Supplies
            </span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {supplies.map(([name, count]) => (
              <div
                key={name}
                className="flex items-center justify-between px-2 py-1 rounded-md bg-slate-900/40 border border-slate-700/30"
              >
                <span className="text-[10px] text-slate-400 capitalize">
                  {name.replace(/_/g, ' ')}
                </span>
                <span className="text-[10px] font-semibold text-slate-200">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-slate-700/40 flex items-center gap-3">
        <div className="flex items-center gap-1 text-[10px]">
          <Zap className="h-3 w-3 text-emerald-400" />
          <span className="text-slate-400">Power</span>
        </div>
        <div className="flex items-center gap-1 text-[10px]">
          <Heart className="h-3 w-3 text-red-400" />
          <span className="text-slate-400">Medical</span>
        </div>
        <div className="flex items-center gap-1 text-[10px]">
          <PawPrint className="h-3 w-3 text-amber-400" />
          <span className="text-slate-400">Pet-Friendly</span>
        </div>
      </div>
    </div>
  );
}
