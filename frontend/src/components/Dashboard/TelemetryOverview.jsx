import React from 'react';
import { useStore } from '../../store';

export default function TelemetryOverview() {
  const telemetry = useStore((state) => state.telemetry);

  const MetricCard = ({ label, value, unit, color }) => (
    <div style={{
      backgroundColor: 'var(--bg-main)',
      border: '1px solid var(--border-color)',
      padding: '12px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center'
    }}>
      <span className="tactical-mono" style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '4px' }}>
        <span className="tactical-mono" style={{ fontSize: '18px', fontWeight: 700, color: color }}>{value}</span>
        <span className="tactical-mono" style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{unit}</span>
      </div>
    </div>
  );

  return (
    <div className="bento-panel" style={{ height: '100%', gridArea: 'telemetry' }}>
      <div className="bento-header">
        <span className="bento-title">Panel D // Telemetry Overview</span>
      </div>
      <div style={{ flex: 1, padding: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <MetricCard label="Worker CPU" value={telemetry.workerMetrics.cpu} unit="%" color="var(--color-green)" />
        <MetricCard label="Memory" value={telemetry.workerMetrics.memory} unit="%" color="var(--color-green)" />
        <MetricCard label="API Latency" value={telemetry.workerMetrics.latency} unit="ms" color={telemetry.workerMetrics.latency > 200 ? 'var(--color-amber)' : 'var(--color-green)'} />
        <MetricCard label="Queue Depth" value={telemetry.workerMetrics.queueDepth} unit="req" color={telemetry.workerMetrics.queueDepth > 50 ? 'var(--color-crimson)' : 'var(--color-green)'} />
      </div>
    </div>
  );
}
