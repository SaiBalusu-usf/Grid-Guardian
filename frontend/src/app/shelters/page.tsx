'use client';

import { useState, useEffect } from 'react';
import { Building2, Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import ShelterPanel from '@/components/ShelterPanel';
import type { Shelter } from '@/lib/types';

const MOCK_SHELTERS: Shelter[] = [
  {
    shelter_id: 'shelter-001',
    name: 'Tampa Convention Center',
    capacity: 500,
    occupancy: 127,
    accessibility: 'full_ada',
    supplies: { water_gallons: 800, cots: 350, first_aid_kits: 75, blankets: 400 },
  },
  {
    shelter_id: 'shelter-002',
    name: 'Hillsborough High School Gymnasium',
    capacity: 300,
    occupancy: 289,
    accessibility: 'wheelchair',
    supplies: { water_gallons: 500, cots: 150, first_aid_kits: 20, blankets: 180 },
  },
  {
    shelter_id: 'shelter-003',
    name: 'Idlewild Baptist Church',
    capacity: 200,
    occupancy: 45,
    accessibility: 'standard',
    supplies: { water_gallons: 400, cots: 180, first_aid_kits: 40, blankets: 200 },
  },
  {
    shelter_id: 'shelter-004',
    name: 'Florida State Fairgrounds',
    capacity: 1000,
    occupancy: 312,
    accessibility: 'full_ada',
    supplies: { water_gallons: 1500, cots: 800, first_aid_kits: 100, blankets: 900 },
  },
];

export default function SheltersPage() {
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const BASE = process.env.NEXT_PUBLIC_API_URL || '';
    fetch(`${BASE}/api/shelters`)
      .then((r) => r.ok ? r.json() : Promise.reject('API error'))
      .then((data) => { setShelters(data); setLoading(false); })
      .catch(() => { setShelters(MOCK_SHELTERS); setLoading(false); });
  }, []);

  const totalCapacity = shelters.reduce((sum, s) => sum + s.capacity, 0);
  const totalOccupancy = shelters.reduce((sum, s) => sum + s.occupancy, 0);
  const overCapacityCount = shelters.filter(
    (s) => s.capacity > 0 && s.occupancy / s.capacity > 0.8
  ).length;

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-blue-400" />
          <h1 className="text-lg font-bold text-white">Shelter Operations</h1>
          <span className="text-xs text-slate-500">{shelters.length} shelters</span>
        </div>

        <div className="flex items-center gap-4">
          {overCapacityCount > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/15 border border-red-500/30">
              <AlertTriangle className="h-3 w-3 text-red-400" />
              <span className="text-xs font-medium text-red-400">
                {overCapacityCount} shelter{overCapacityCount > 1 ? 's' : ''} &gt;80% capacity
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Total Capacity</p>
          <p className="text-xl font-bold text-white">{totalCapacity.toLocaleString()}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Total Occupancy</p>
          <p className="text-xl font-bold text-white">{totalOccupancy.toLocaleString()}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Available Spots</p>
          <p className="text-xl font-bold text-emerald-400">{(totalCapacity - totalOccupancy).toLocaleString()}</p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-3">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Utilization</p>
          <p className="text-xl font-bold text-white">
            {totalCapacity > 0 ? Math.round((totalOccupancy / totalCapacity) * 100) : 0}%
          </p>
        </div>
      </div>

      {/* A2A Recommendation */}
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/15 border border-emerald-500/30 shrink-0">
            <span className="text-sm">\uD83E\uDD16</span>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-emerald-400 mb-1">A2A Resource Specialist Recommendation</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Based on current occupancy rates, recommend redirecting new evacuees to{' '}
              <span className="font-semibold text-white">Millennium Youth Complex</span> (13% occupancy) and{' '}
              <span className="font-semibold text-white">Florida State Fairgrounds</span> (20% occupancy).
              Palmer Events Center and Dove Springs are approaching critical capacity -- consider activating overflow protocols.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-blue-400 mb-3" />
          <p className="text-sm text-slate-400">Loading shelter data...</p>
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shelters.map((shelter) => (
            <ShelterPanel key={shelter.shelter_id} shelter={shelter} />
          ))}
        </div>
      )}
    </div>
  );
}
