'use client';

import { Suspense, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { Loader2, Map as MapIcon } from 'lucide-react';
import { useIncident } from '@/lib/hooks';

const MapView = dynamic(() => import('@/components/MapView'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-slate-900 rounded-xl">
      <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
    </div>
  ),
});

const DEFAULT_MARKERS = [
  { id: 'hospital-1', position: [30.2849, -97.7341] as [number, number], type: 'hospital' as const, label: 'Dell Seton Medical Center', details: 'Level I Trauma Center - 211 beds' },
  { id: 'hospital-2', position: [30.3119, -97.7384] as [number, number], type: 'hospital' as const, label: "St. David's North Austin", details: 'General Hospital - 380 beds' },
  { id: 'hospital-3', position: [30.2286, -97.7564] as [number, number], type: 'hospital' as const, label: "St. David's South Austin", details: 'General Hospital - 250 beds' },
  { id: 'shelter-1', position: [30.2747, -97.7404] as [number, number], type: 'shelter' as const, label: 'Austin Convention Center', details: 'Primary shelter - Cap. 2,000' },
  { id: 'shelter-2', position: [30.2983, -97.7165] as [number, number], type: 'shelter' as const, label: 'Palmer Events Center', details: 'Secondary shelter - Cap. 1,500' },
  { id: 'shelter-3', position: [30.2530, -97.7633] as [number, number], type: 'shelter' as const, label: 'Burger Activity Center', details: 'Neighborhood shelter - Cap. 500' },
  { id: 'shelter-4', position: [30.3190, -97.7048] as [number, number], type: 'shelter' as const, label: 'North Austin Community Center', details: 'Overflow shelter - Cap. 800' },
  { id: 'zone-1', position: [30.2862, -97.7394] as [number, number], type: 'zone' as const, label: 'UT Campus Zone', details: 'High density, flooding risk' },
  { id: 'zone-2', position: [30.2650, -97.7530] as [number, number], type: 'zone' as const, label: 'Downtown Core', details: 'Power grid vulnerability' },
  { id: 'zone-3', position: [30.2450, -97.7650] as [number, number], type: 'zone' as const, label: 'South Lamar Corridor', details: 'Evacuation congestion point' },
];

const DEFAULT_ZONES = [
  { id: 'impact-1', center: [30.2862, -97.7394] as [number, number], radius: 1200, color: '#EF4444', label: 'Campus Impact Zone' },
  { id: 'impact-2', center: [30.2650, -97.7530] as [number, number], radius: 800, color: '#F59E0B', label: 'Downtown Impact Zone' },
  { id: 'impact-3', center: [30.2450, -97.7650] as [number, number], radius: 600, color: '#F59E0B', label: 'South Corridor Zone' },
];

const DEFAULT_ROUTES = [
  {
    id: 'evac-1',
    positions: [
      [30.2862, -97.7394],
      [30.2800, -97.7420],
      [30.2747, -97.7404],
    ] as [number, number][],
    color: '#10B981',
    label: 'Campus to Convention Center',
  },
  {
    id: 'evac-2',
    positions: [
      [30.2650, -97.7530],
      [30.2700, -97.7300],
      [30.2747, -97.7404],
    ] as [number, number][],
    color: '#10B981',
    label: 'Downtown to Convention Center',
  },
  {
    id: 'evac-3',
    positions: [
      [30.2862, -97.7394],
      [30.2950, -97.7250],
      [30.2983, -97.7165],
    ] as [number, number][],
    color: '#3B82F6',
    label: 'Campus to Palmer Events',
  },
];

function MapContent() {
  const searchParams = useSearchParams();
  const incidentId = searchParams.get('incident');
  const { incident } = useIncident(incidentId);

  const markers = useMemo(() => {
    if (incident) {
      const incidentMarker = {
        id: 'incident-main',
        position: [30.2750, -97.7450] as [number, number],
        type: 'incident' as const,
        label: incident.scenario.slice(0, 50),
        details: `Severity: ${incident.severity} | Status: ${incident.status}`,
      };
      return [incidentMarker, ...DEFAULT_MARKERS];
    }
    return DEFAULT_MARKERS;
  }, [incident]);

  return (
    <div className="p-6 space-y-4 animate-fade-in h-[calc(100vh-3.5rem)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapIcon className="h-5 w-5 text-emerald-400" />
          <h1 className="text-lg font-bold text-white">Operations Map</h1>
          {incident && (
            <span className="text-xs text-slate-400">
              -- {incident.scenario.slice(0, 40)}...
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Austin, TX</span>
          <span className="text-slate-700">|</span>
          <span>{markers.length} markers</span>
        </div>
      </div>

      <div className="h-[calc(100%-3rem)]">
        <MapView
          center={[30.2672, -97.7431]}
          zoom={13}
          markers={markers}
          zones={DEFAULT_ZONES}
          routes={DEFAULT_ROUTES}
        />
      </div>
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      }
    >
      <MapContent />
    </Suspense>
  );
}
