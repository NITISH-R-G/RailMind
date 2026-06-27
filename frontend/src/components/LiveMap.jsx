import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { useStore } from '../store';

const MAP_CENTER = [22.9, 78.6]; // Center of India

// SVG Train Icon with Rotation
const createRotatedIcon = (status, rotation) => {
  let color = 'var(--color-green)';
  if (status === 'delayed') color = 'var(--color-amber)';
  if (status === 'cancelled') color = 'var(--color-crimson)';

  const svgIcon = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="transform: rotate(${rotation}deg); transform-origin: center;">
      <path d="M12 2L4 20L12 17L20 20L12 2Z" fill="${color}" stroke="var(--bg-main)" stroke-width="1.5"/>
    </svg>
  `;

  return L.divIcon({
    html: svgIcon,
    className: 'custom-svg-icon',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

const createShockwaveIcon = (severity) => {
  const color = severity === 'critical' ? 'crimson' : severity === 'high' ? 'amber' : 'green';
  return L.divIcon({
    className: 'leaflet-div-icon',
    html: `<div class="pulse-dot-${color}" style="width: 16px; height: 16px; margin: -8px 0 0 -8px;"></div>`,
    iconSize: [0, 0]
  });
};

const getDetourCoords = (planStr) => {
  if (!planStr) return null;
  const match = planStr.match(/coordinates:\s*\[(.*?)\]/);
  if (match && match[1]) {
    try {
      const parts = match[1].split('),').map(p => p.replace(/[()]/g, '').trim());
      const coords = parts.map(p => {
        const [lat, lng] = p.split(',').map(Number);
        return [lat, lng];
      });
      return coords.length > 0 ? coords : null;
    } catch (e) {
      return null;
    }
  }
  return null;
};

export default function LiveMap() {
  const trains = useStore(state => state.trains);
  const incidents = useStore(state => state.incidents);
  const [selectedTrainNo, setSelectedTrainNo] = useState(null);
  const [trainPositions, setTrainPositions] = useState({});

  useEffect(() => {
    // Calculate rotation vectors based on past positions
    setTrainPositions(prev => {
      const next = { ...prev };
      trains.forEach(t => {
        if (t.lat != null && t.lng != null) {
          const oldPos = next[t.train_number];
          let rotation = oldPos?.rotation || 0;
          if (oldPos && (oldPos.lat !== t.lat || oldPos.lng !== t.lng)) {
             rotation = Math.atan2(t.lng - oldPos.lng, t.lat - oldPos.lat) * 180 / Math.PI;
          }
          next[t.train_number] = { lat: Number(t.lat), lng: Number(t.lng), rotation };
        }
      });
      return next;
    });
  }, [trains]);

  const activeTrains = trains.length > 0 ? trains : [
    { train_number: "12301", train_name: "Howrah Rajdhani", current_station: "New Delhi", delay_minutes: 0, status: "On Time", lat: 28.6419, lng: 77.2194, speed: "120 km/h", next_station: "Kanpur Central", distance_next: "440 KM", route_stops: [{lat: 28.6419, lng: 77.2194}, {lat: 26.4499, lng: 80.3319}] },
  ];

  const selectedTrain = activeTrains.find(t => t.train_number === selectedTrainNo);
  const originalCoords = selectedTrain?.route_stops?.map(s => [s.lat, s.lng]) || [];

  const approvedIncident = selectedTrain && (incidents || []).find(
    inc => inc.train_number === selectedTrain.train_number && inc.approved && inc.reroute_plan
  );
  const detourCoords = approvedIncident ? getDetourCoords(approvedIncident.reroute_plan) : null;

  return (
    <div style={{ flex: 1, height: '100%', position: 'relative', backgroundColor: 'var(--bg-main)' }}>
      <MapContainer center={MAP_CENTER} zoom={5} zoomControl={false} style={{ width: '100%', height: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        <ZoomControl position="bottomright" />

        {/* Feature C: Animated Route Polylines */}
        {selectedTrain && (
          <>
            {detourCoords ? (
              <>
                {originalCoords.length > 1 && (
                  <Polyline positions={originalCoords} pathOptions={{ color: '#2a3a4a', weight: 2, dashArray: '4, 6', opacity: 0.5 }} />
                )}
                <Polyline positions={detourCoords} pathOptions={{ color: 'var(--color-crimson)', weight: 4, dashArray: '8, 8' }} className="animated-dash-flow" />
              </>
            ) : (
              originalCoords.length > 1 && (
                <Polyline positions={originalCoords} pathOptions={{ color: 'var(--color-green)', weight: 3 }} />
              )
            )}
          </>
        )}

        {/* Shockwaves for Incidents */}
        {incidents.map(inc => {
           const train = activeTrains.find(t => t.train_number === inc.train_number);
           if (!train || train.lat == null || train.lng == null) return null;
           return (
             <Marker key={`shock-${inc.id}`} position={[train.lat, train.lng]} icon={createShockwaveIcon(inc.severity)} />
           );
        })}

        {/* Train Markers */}
        {activeTrains.map((train, idx) => {
          const pos = trainPositions[train.train_number] || { lat: train.lat || 28.6, lng: train.lng || 77.2, rotation: 0 };
          const isSelected = selectedTrainNo === train.train_number;

          let status = 'ontime';
          if (train.delay_minutes > 60 || train.status?.toLowerCase() === 'cancelled') status = 'cancelled';
          else if (train.delay_minutes > 15) status = 'delayed';

          return (
            <Marker
              key={train.train_number || idx}
              position={[pos.lat, pos.lng]}
              icon={createRotatedIcon(status, pos.rotation)}
              eventHandlers={{ click: () => setSelectedTrainNo(prev => prev === train.train_number ? null : train.train_number) }}
              zIndexOffset={isSelected ? 1000 : 0}
            >
              <Popup closeButton={false}>
                <div style={{ padding: '8px', minWidth: '150px' }}>
                  <div className="tactical-mono" style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '4px' }}>#{train.train_number}</div>
                  <div className="tactical-sans" style={{ fontSize: '12px', color: 'var(--text-primary)', fontWeight: 'bold' }}>{train.train_name || 'Express Train'}</div>
                  <div className="tactical-mono" style={{ fontSize: '10px', color: status === 'ontime' ? 'var(--color-green)' : (status === 'delayed' ? 'var(--color-amber)' : 'var(--color-crimson)'), marginTop: '4px' }}>
                    {status.toUpperCase()} ({train.delay_minutes}m)
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
