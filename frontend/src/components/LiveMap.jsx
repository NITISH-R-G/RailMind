/* eslint-disable */
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, Polyline, CircleMarker, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useStore } from '../store';

// ─── CSS Animations injected once ────────────────────────────────────────────
const ANIMATION_CSS = `
  @keyframes dashFlow {
    from { stroke-dashoffset: 24; }
    to   { stroke-dashoffset: 0; }
  }
  /* Smooth marker glide — Leaflet sets position via CSS transform */
  .train-position-marker {
    transition: transform 4.8s linear !important;
  }
  .shockwave-ring {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: 3px solid #FF3333;
    background: transparent;
    position: absolute;
    left: -16px;
    top: -16px;
    pointer-events: none;
    /* Uses transform scaling instead of layout properties */
    animation: shockwavePulse 1.8s ease-out infinite;
  }
  @keyframes shockwavePulse {
    0%   { transform: scale(0.1); opacity: 0.9; }
    100% { transform: scale(3.5); opacity: 0; }
  }
  .shockwave-ring.warning {
    border-color: #FFB000;
  }
  .leaflet-popup-content-wrapper {
    background: #161F30 !important;
    border: 1px solid #26354A !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
  }
  .leaflet-popup-tip { background: #161F30 !important; }
  .tactical-path {
    animation: dashFlow 1.5s linear infinite;
  }
`;

const INITIAL_VIEW = {
  center: [23.0, 80.0],
  zoom: 5
};

const STATION_COORDS = {
  "NDLS": [28.6419, 77.2194],
  "CNB": [26.4499, 80.3319],
  "ALD": [25.4358, 81.8463],
  "BSB": [25.3176, 82.9739],
  "BPL": [23.2599, 77.4126],
  "NGP": [21.1458, 79.0882],
  "BZA": [16.5193, 80.6305],
  "MAS": [13.0827, 80.2707],
  "HWH": [22.5958, 88.2636],
  "SDAH": [22.5697, 88.3697],
  "BWN": [23.2324, 87.8615],
  "GKP": [26.7606, 83.3732],
  "LDH": [30.9010, 75.8573],
  "LKO": [26.8467, 80.9462],
  "VSKP": [17.7231, 83.2985],
  "MDU": [9.9252, 78.1198]
};

const createTrainIcon = (status, bearing, isAnomaly) => {
  const isDelayed = status === 'delayed' || status === 'delayed_severe';
  const color = isAnomaly ? '#FF3333' : (isDelayed ? '#FFB000' : '#00FF66');

  const svgHtml = `
    <div style="position: relative; width: 0; height: 0;">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"
           style="position: absolute; left: -12px; top: -12px; transform: rotate(${bearing}deg); filter: drop-shadow(0 0 4px ${color});">
        <path d="M12 2L2 22L12 18L22 22L12 2Z" fill="${color}" stroke="#0A0E17" stroke-width="2" stroke-linejoin="round"/>
      </svg>
      ${isAnomaly ? `<div class="shockwave-ring ${status === 'warning' ? 'warning' : ''}"></div>` : ''}
    </div>
  `;

  return L.divIcon({
    html: svgHtml,
    className: 'train-position-marker',
    iconSize: [0, 0],
    iconAnchor: [0, 0]
  });
};

function MapViewSynchronizer({ trains }) {
  const map = useMap();
  useEffect(() => {
    // Optional: auto-fit bounds could go here
  }, [map, trains]);
  return null;
}

export default function LiveMap({ fullScreen = false }) {
  const storeTrains = useStore(state => state.trains);
  const storeIncidents = useStore(state => state.incidents);

  // Filter out any anomalies from incidents
  const criticalTrainNumbers = storeIncidents.filter(i => i.severity === 'critical').map(i => String(i.train_number));
  const warningTrainNumbers = storeIncidents.filter(i => i.severity === 'warning').map(i => String(i.train_number));

  useEffect(() => {
    if (!document.getElementById('leaflet-custom-animations')) {
      const style = document.createElement('style');
      style.id = 'leaflet-custom-animations';
      style.textContent = ANIMATION_CSS;
      document.head.appendChild(style);
    }
  }, []);

  // Compute tactical paths by parsing station codes from reroute_plan texts
  const tacticalPaths = useMemo(() => {
    const paths = [];
    storeIncidents.filter(i => i.reroute_plan).forEach(inc => {
      const planText = inc.reroute_plan.toUpperCase();
      const detectedStations = [];
      Object.keys(STATION_COORDS).forEach(code => {
        if (planText.includes(code)) {
          detectedStations.push(STATION_COORDS[code]);
        }
      });

      // If we find 2 or more stations, we assume they form a path segment
      if (detectedStations.length >= 2) {
        paths.push({
          id: inc.id,
          positions: detectedStations
        });
      }
    });
    return paths;
  }, [storeIncidents]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', backgroundColor: '#0A0E17' }}>

      {/* HUD Overlays */}
      <div style={{
        position: 'absolute', top: '16px', left: '16px', zIndex: 1000,
        backgroundColor: '#161F30', border: '1px solid #26354A', padding: '8px 12px'
      }}>
        <h3 className="palantir-mono" style={{ fontSize: '11px', color: '#00FF66', fontWeight: 600, letterSpacing: '0.5px' }}>TELEMETRY MAP // ORCHESTRATION</h3>
        <p className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080', marginTop: '4px' }}>TRACKING {storeTrains.length} ASSETS</p>
      </div>

      <MapContainer
        center={INITIAL_VIEW.center}
        zoom={INITIAL_VIEW.zoom}
        zoomControl={false}
        style={{ width: '100%', height: '100%', background: '#0A0E17' }}
      >
        <ZoomControl position="bottomright" />
        <MapViewSynchronizer trains={storeTrains} />

        {/* Tactical Dark Matter Map Layer */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; <a href='https://carto.com/attributions'>CARTO</a>"
        />

        {/* Draw Stations and Paths */}
        {Object.entries(STATION_COORDS).map(([code, coords]) => (
          <CircleMarker
            key={`station-${code}`}
            center={coords}
            radius={4}
            pathOptions={{ color: '#5c7080', fillColor: '#0A0E17', fillOpacity: 1, weight: 2 }}
          >
            <Popup closeButton={false}>
              <div className="palantir-mono" style={{ padding: '8px', color: '#e2e8f0', fontSize: '11px', textAlign: 'center' }}>
                <span style={{ color: '#00FF66', fontWeight: 700 }}>NODE: {code}</span>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {storeTrains.map(train => {
          if (!train.location_geo || !train.location_geo.coordinates) return null;
          // GeoJSON is [lng, lat], Leaflet expects [lat, lng]
          const coords = [train.location_geo.coordinates[1], train.location_geo.coordinates[0]];

          let bearing = 0;
          let isAnomaly = false;
          let severityStatus = 'nominal';

          const trainStr = String(train.train_number);
          if (criticalTrainNumbers.includes(trainStr)) {
            isAnomaly = true;
            severityStatus = 'critical';
          } else if (warningTrainNumbers.includes(trainStr)) {
             isAnomaly = true;
             severityStatus = 'warning';
          } else if (train.status === 'delayed' || train.delay_minutes > 15) {
             severityStatus = 'delayed';
          }

          return (
            <Marker
              key={train.train_number}
              position={coords}
              icon={createTrainIcon(severityStatus, bearing, isAnomaly)}
            >
              <Popup closeButton={false}>
                <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '200px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #26354A', paddingBottom: '4px' }}>
                     <span className="palantir-mono" style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0' }}>{train.train_number}</span>
                     <span className="palantir-mono" style={{ fontSize: '10px', color: isAnomaly ? '#FF3333' : '#00FF66' }}>[{severityStatus.toUpperCase()}]</span>
                  </div>
                  <div className="palantir-mono" style={{ fontSize: '10px', color: '#8a9ba8', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                     <p>NAME: {train.train_name}</p>
                     <p>SPEED: {train.speed || 0} km/h</p>
                     <p>DELAY: {train.delay_minutes || 0} min</p>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {tacticalPaths.map(path => (
          <Polyline
            key={`route-${path.id}`}
            positions={path.positions}
            pathOptions={{
              color: '#FFB000',
              weight: 2,
              dashArray: '4, 8',
              className: 'tactical-path'
            }}
          />
        ))}

      </MapContainer>
    </div>
  );
}
