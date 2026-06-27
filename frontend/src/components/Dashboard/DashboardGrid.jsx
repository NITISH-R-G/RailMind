import React from 'react';
import LogStream from './LogStream';
import IncidentCore from './IncidentCore';
import TaskKanban from './TaskKanban';
import TelemetryOverview from './TelemetryOverview';
import LiveMap from '../LiveMap';

export default function DashboardGrid() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr 350px',
      gridTemplateRows: '60% 40%',
      gridTemplateAreas: `
        "incidents map telemetry"
        "incidents tasks logs"
      `,
      gap: '8px',
      padding: '8px',
      height: '100%',
      backgroundColor: 'var(--bg-main)',
      overflow: 'hidden'
    }}>
      <IncidentCore />

      <div className="bento-panel" style={{ gridArea: 'map', position: 'relative' }}>
        <div className="bento-header" style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 1000, backgroundColor: 'rgba(22, 31, 48, 0.9)' }}>
          <span className="bento-title">Tactical Map Orchestration</span>
          <div className="pulse-dot-green"></div>
        </div>
        <div style={{ flex: 1, height: '100%' }}>
          <LiveMap />
        </div>
      </div>

      <TelemetryOverview />
      <TaskKanban />
      <LogStream />
    </div>
  );
}
