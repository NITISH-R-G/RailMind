import React from 'react';
import { Activity } from 'lucide-react';
import useStore from '../store';

const MetricCard = ({ label, value, color }) => (
  <div style={{
    backgroundColor: '#161F30',
    border: '1px solid #26354A',
    padding: '8px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  }}>
    <span className="palantir-mono" style={{ fontSize: '9px', fontWeight: 600, color: '#5c7080' }}>
      {label}
    </span>
    <span className="palantir-mono" style={{ fontSize: '14px', fontWeight: 700, color: color, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
      {value}
    </span>
  </div>
);

export default function TelemetryOverviewPanel() {
  const telemetry = useStore((state) => state.telemetry) || {};

  const metrics = [
    { label: 'AGENT STATE', value: telemetry.agent_loop_status?.toUpperCase() || 'NOMINAL', color: '#00FF66' },
    { label: 'RAIL API PING', value: `${telemetry.railways_latency_ms || 0}ms`, color: '#00FF66' },
    { label: 'AI COG LATENCY', value: `${telemetry.ai_latency_ms || 0}ms`, color: '#FFB000' },
    { label: 'WS CLIENTS', value: telemetry.websocket_clients || 0, color: '#00FF66' },
    { label: 'ACTIVE INCIDENTS', value: telemetry.mongodb_incidents || 0, color: '#FF3333' },
    { label: 'PENDING TASKS', value: telemetry.mongodb_tasks || 0, color: '#FFB000' }
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#0A0E17',
      border: '1px solid #26354A',
    }}>
      <div style={{
        padding: '8px 12px',
        borderBottom: '1px solid #26354A',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        backgroundColor: '#161F30'
      }}>
        <Activity size={14} color="#00FF66" />
        <span className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0' }}>TELEMETRY OVERVIEW</span>
      </div>

      <div style={{ flex: 1, padding: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '8px', overflowY: 'auto', alignContent: 'start' }}>
        {metrics.map((m, idx) => (
          <MetricCard key={idx} label={m.label} value={m.value} color={m.color} />
        ))}
      </div>
    </div>
  );
}
