import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import useStore from '../store';

const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical': return '#FF3333';
    case 'warning': return '#FFB000';
    case 'info': return '#00FF66';
    default: return '#00FF66';
  }
};

const getSeverityWeight = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'critical': return 3;
    case 'warning': return 2;
    case 'info': return 1;
    default: return 0;
  }
};

export default function IncidentCorePanel() {
  const incidents = useStore((state) => state.incidents);

  // Sort by severity (critical first) then by timestamp (newest first)
  const sortedIncidents = [...incidents].sort((a, b) => {
    const weightDiff = getSeverityWeight(b.severity) - getSeverityWeight(a.severity);
    if (weightDiff !== 0) return weightDiff;
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

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
        <AlertTriangle size={14} color="#FF3333" />
        <span className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0' }}>CRITICAL INCIDENT CORE</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sortedIncidents.length === 0 ? (
          <div className="palantir-mono" style={{ padding: '12px', color: '#5c7080', fontSize: '11px', fontStyle: 'italic', textAlign: 'center' }}>
            [ NO ACTIVE ANOMALIES ]
          </div>
        ) : (
          sortedIncidents.map((inc) => {
            const color = getSeverityColor(inc.severity);
            return (
              <div key={inc.id} style={{
                backgroundColor: '#161F30',
                border: '1px solid #26354A',
                borderLeft: `3px solid ${color}`,
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="palantir-mono" style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    color: color,
                    backgroundColor: `${color}1A`,
                    padding: '2px 6px',
                    border: `1px solid ${color}`
                  }}>
                    {inc.severity?.toUpperCase() || 'UNKNOWN'}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={10} color="#5c7080" />
                    <span className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080' }}>
                      {inc.timestamp ? new Date(inc.timestamp).toLocaleTimeString() : '--:--:--'}
                    </span>
                  </div>
                </div>

                <h4 className="palantir-mono" style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0', margin: 0 }}>
                  {inc.title}
                </h4>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                  <span className="palantir-mono" style={{ fontSize: '10px', color: '#8a9ba8' }}>
                    TRN: {inc.train_number}
                  </span>
                  <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>
                    ID: {inc.id.substring(0, 8)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
