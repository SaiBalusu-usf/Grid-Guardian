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
  { id: 'hospital-1', position: [27.9559, -82.4593] as [number, number], type: 'hospital' as const, label: 'Tampa General Hospital', details: 'Level I Trauma Center - 1,041 beds' },
  { id: 'hospital-2', position: [27.9850, -82.4570] as [number, number], type: 'hospital' as const, label: 'St. Joseph\'s Hospital', details: 'General Hospital - 492 beds' },
  { id: 'hospital-3', position: [27.9110, -82.5150] as [number, number], type: 'hospital' as const, label: 'AdventHealth Carrollwood', details: 'Community Hospital - 120 beds' },
  { id: 'shelter-1', position: [27.9425, -82.4515] as [number, number], type: 'shelter' as const, label: 'Tampa Convention Center', details: 'Primary shelter - Cap. 2,000' },
  { id: 'shelter-2', position: [27.9750, -82.4590] as [number, number], type: 'shelter' as const, label: 'Hillsborough High School', details: 'Secondary shelter - Cap. 300' },
  { id: 'shelter-3', position: [28.0750, -82.4850] as [number, number], type: 'shelter' as const, label: 'Idlewild Baptist Church', details: 'Community shelter - Cap. 200' },
  { id: 'shelter-4', position: [27.9650, -82.3980] as [number, number], type: 'shelter' as const, label: 'Florida State Fairgrounds', details: 'Overflow shelter - Cap. 1,000' },
  { id: 'zone-1', position: [27.9506, -82.4572] as [number, number], type: 'zone' as const, label: 'Downtown Tampa', details: 'Flood zone, storm surge risk' },
  { id: 'zone-2', position: [27.9200, -82.4800] as [number, number], type: 'zone' as const, label: 'South Tampa / Bayshore', details: 'Coastal flooding, evacuation zone A' },
  { id: 'zone-3', position: [27.9700, -82.4100] as [number, number], type: 'zone' as const, label: 'Ybor City / East Tampa', details: 'Low-lying area, power grid vulnerability' },
];

const DEFAULT_ZONES = [
  { id: 'impact-1', center: [27.9506, -82.4572] as [number, number], radius: 1500, color: '#EF4444', label: 'Downtown Tampa Impact Zone' },
  { id: 'impact-2', center: [27.9200, -82.4800] as [number, number], radius: 1200, color: '#F59E0B', label: 'South Tampa / Bayshore Zone' },
  { id: 'impact-3', center: [27.9700, -82.4100] as [number, number], radius: 800, color: '#F59E0B', label: 'Ybor City Zone' },
];

const DEFAULT_ROUTES = [
  {
    id: 'evac-1',
    positions: [
      [27.9506, -82.4572],
      [27.9450, -82.4550],
      [27.9425, -82.4515],
    ] as [number, number][],
    color: '#10B981',
    label: 'Downtown to Convention Center',
  },
  {
    id: 'evac-2',
    positions: [
      [27.9200, -82.4800],
      [27.9350, -82.4650],
      [27.9425, -82.4515],
    ] as [number, number][],
    color: '#10B981',
    label: 'South Tampa to Convention Center',
  },
  {
    id: 'evac-3',
    positions: [
      [27.9700, -82.4100],
      [27.9680, -82.4300],
      [27.9650, -82.3980],
    ] as [number, number][],
    color: '#3B82F6',
    label: 'Ybor City to Fairgrounds',
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
        position: [27.9506, -82.4572] as [number, number],
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
          <span>Tampa, FL</span>
          <span className="text-slate-700">|</span>
          <span>{markers.length} markers</span>
        </div>
      </div>

      <div className="h-[calc(100%-3rem)]">
        <MapView
          center={[27.9506, -82.4572]}
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
