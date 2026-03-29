'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface MapMarker {
  id: string;
  position: [number, number];
  type: 'zone' | 'hospital' | 'shelter' | 'incident';
  label: string;
  details?: string;
}

interface MapRoute {
  id: string;
  positions: [number, number][];
  color?: string;
  label?: string;
}

interface MapZone {
  id: string;
  center: [number, number];
  radius: number;
  color?: string;
  label?: string;
}

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  routes?: MapRoute[];
  zones?: MapZone[];
}

function createDivIcon(type: string): L.DivIcon {
  const colors: Record<string, string> = {
    zone: '#EF4444',
    hospital: '#3B82F6',
    shelter: '#10B981',
    incident: '#F59E0B',
  };
  const icons: Record<string, string> = {
    zone: '\u26A0',
    hospital: '\u2795',
    shelter: '\uD83C\uDFE0',
    incident: '\u26A1',
  };

  const color = colors[type] || '#94A3B8';
  const icon = icons[type] || '\u2022';

  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: ${color}22;
      border: 2px solid ${color};
      color: ${color};
      font-size: 14px;
      box-shadow: 0 0 12px ${color}44;
    ">${icon}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
}

function FitBounds({ markers, zones }: { markers: MapMarker[]; zones: MapZone[] }) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] = [
      ...markers.map((m) => m.position),
      ...zones.map((z) => z.center),
    ];
    if (points.length > 1) {
      const bounds = L.latLngBounds(points.map(([lat, lng]) => [lat, lng]));
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [markers, zones, map]);

  return null;
}

export default function MapView({
  center = [27.9506, -82.4572],
  zoom = 12,
  markers = [],
  routes = [],
  zones = [],
}: MapViewProps) {
  return (
    <div className="relative h-full w-full rounded-xl overflow-hidden border border-slate-700/50">
      <MapContainer
        center={center}
        zoom={zoom}
        className="h-full w-full"
        style={{ background: '#0F172A' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {markers.length > 1 && <FitBounds markers={markers} zones={zones} />}

        {zones.map((zone) => (
          <Circle
            key={zone.id}
            center={zone.center}
            radius={zone.radius}
            pathOptions={{
              color: zone.color || '#EF4444',
              fillColor: zone.color || '#EF4444',
              fillOpacity: 0.1,
              weight: 2,
              dashArray: '6 4',
            }}
          >
            {zone.label && (
              <Popup>
                <div className="text-sm font-medium">{zone.label}</div>
              </Popup>
            )}
          </Circle>
        ))}

        {routes.map((route) => (
          <Polyline
            key={route.id}
            positions={route.positions}
            pathOptions={{
              color: route.color || '#10B981',
              weight: 3,
              dashArray: '8 4',
              opacity: 0.8,
              className: 'animated-route',
            }}
          >
            {route.label && (
              <Popup>
                <div className="text-sm font-medium">{route.label}</div>
              </Popup>
            )}
          </Polyline>
        ))}

        {markers.map((marker) => (
          <Marker
            key={marker.id}
            position={marker.position}
            icon={createDivIcon(marker.type)}
          >
            <Popup>
              <div className="min-w-[140px]">
                <p className="text-sm font-semibold text-slate-900">{marker.label}</p>
                {marker.details && (
                  <p className="text-xs text-slate-600 mt-1">{marker.details}</p>
                )}
                <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 capitalize">
                  {marker.type}
                </span>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] rounded-lg bg-slate-900/90 border border-slate-700/50 backdrop-blur-sm p-3">
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Legend</h4>
        <div className="space-y-1.5">
          {[
            { color: '#EF4444', label: 'Affected Zone' },
            { color: '#3B82F6', label: 'Hospital' },
            { color: '#10B981', label: 'Shelter' },
            { color: '#F59E0B', label: 'Incident' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-2">
              <div
                className="h-2.5 w-2.5 rounded-full border"
                style={{ backgroundColor: `${color}33`, borderColor: color }}
              />
              <span className="text-[10px] text-slate-300">{label}</span>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <div className="h-0.5 w-2.5 bg-emerald-500" style={{ borderTop: '2px dashed #10B981' }} />
            <span className="text-[10px] text-slate-300">Evacuation Route</span>
          </div>
        </div>
      </div>
    </div>
  );
}
