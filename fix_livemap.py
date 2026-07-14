with open("frontend/src/components/LiveMap.jsx", "r") as f:
    content = f.read()

# Strip out everything and build it correctly from scratch
new_content = """import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import useStore from '../store';

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

const parseReroutePlan = (planString) => {
  if (!planString) return [];
  // basic parsing to find station codes
  const words = planString.split(/[\\s,>➔-]/);
  const path = [];
  for (const word of words) {
    const code = word.trim().toUpperCase();
    if (STATION_COORDS[code]) {
      path.push(STATION_COORDS[code]);
    }
  }
  return path;
};

const MAP_CENTER = [23.0, 80.0];

// Inject tactical animation CSS
const tacticalStyles = `
  @keyframes pulseAnomaly {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
  }
  .leaflet-container {
    background: #0A0E17 !important;
  }
`;

const getTrainIcon = (color, rotation = 0) => L.divIcon({
  className: 'custom-train-marker',
  html: `<div style="
    width: 14px;
    height: 14px;
    background-color: ${color};
    border: 1px solid #0A0E17;
    transform: rotate(${rotation}deg);
    transition: transform 0.3s ease;
    clip-path: polygon(50% 0%, 100% 100%, 50% 80%, 0% 100%);
  "></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

const getAnomalyIcon = (color) => L.divIcon({
  className: 'custom-anomaly-marker',
  html: `<div style="
    width: 20px;
    height: 20px;
    border: 2px solid ${color};
    border-radius: 50%;
    animation: pulseAnomaly 1.5s infinite;
  "></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

export default function LiveMap() {
  const trains = useStore(state => state.trains);
  const incidents = useStore(state => state.incidents);
  const [styleInjected, setStyleInjected] = useState(false);

  useEffect(() => {
    if (!styleInjected) {
      const styleSheet = document.createElement("style");
      styleSheet.innerText = tacticalStyles;
      document.head.appendChild(styleSheet);
      setStyleInjected(true);
    }
  }, [styleInjected]);

  return (
    <div style={{ flex: 1, height: '100%', position: 'relative', backgroundColor: '#0A0E17', border: '1px solid #26354A' }}>
      <MapContainer center={MAP_CENTER} zoom={5} zoomControl={false} style={{ width: '100%', height: '100%' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />
        <ZoomControl position="bottomright" />

        {/* Tactical Reroute Lines */}
        {incidents.filter(inc => inc.approved && inc.reroute_plan).map(inc => {
          const coords = parseReroutePlan(inc.reroute_plan);
          if (coords.length < 2) return null;
          return (
            <Polyline
              key={`reroute-${inc.id}`}
              positions={coords}
              color="#00FF66"
              weight={2}
              dashArray="4, 4"
              opacity={0.8}
            />
          );
        })}

        {/* Train Markers */}
        {trains.map(train => {
          if (!train.lat || !train.lng) return null;

          let color = '#00FF66'; // Nominal
          if (train.delay_minutes > 15) color = '#FFB000'; // Warning
          if (train.delay_minutes > 60 || train.status === 'cancelled') color = '#FF3333'; // Critical

          // Dummy rotation logic for demo (should use actual bearing)
          const rotation = train.train_number.charCodeAt(0) * 10 % 360;

          return (
            <Marker
              key={`train-${train.train_number}`}
              position={[train.lat, train.lng]}
              icon={getTrainIcon(color, rotation)}
            />
          );
        })}

        {/* Anomaly Markers */}
        {incidents.map(inc => {
          const t = trains.find(tr => tr.train_number === inc.train_number);
          if (!t || !t.lat || !t.lng) return null;

          const color = inc.severity === 'critical' ? '#FF3333' : inc.severity === 'warning' ? '#FFB000' : '#00FF66';
          return (
            <Marker
              key={`anomaly-${inc.id}`}
              position={[t.lat, t.lng]}
              icon={getAnomalyIcon(color)}
            />
          );
        })}

      </MapContainer>
    </div>
  );
}
"""

with open("frontend/src/components/LiveMap.jsx", "w") as f:
    f.write(new_content)
