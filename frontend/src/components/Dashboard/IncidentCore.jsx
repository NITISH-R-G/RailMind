import React from 'react';
import { useStore } from '../../store';
import { AlertTriangle, ShieldAlert, Activity } from 'lucide-react';

export default function IncidentCore() {
  const incidents = useStore((state) => state.incidents);

  const getSeverityDetails = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return { color: '#FF3333', bg: 'rgba(255, 51, 51, 0.1)', icon: <ShieldAlert size={14} color="#FF3333" /> };
      case 'high': return { color: '#FFB000', bg: 'rgba(255, 176, 0, 0.1)', icon: <AlertTriangle size={14} color="#FFB000" /> };
      case 'medium': return { color: '#FFB000', bg: 'transparent', icon: <AlertTriangle size={14} color="#FFB000" /> };
      default: return { color: '#00FF66', bg: 'transparent', icon: <Activity size={14} color="#00FF66" /> };
    }
  };

  const sortedIncidents = [...incidents].sort((a, b) => {
    const sevOrder = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };
    return (sevOrder[b.severity?.toLowerCase()] || 0) - (sevOrder[a.severity?.toLowerCase()] || 0);
  });

  return (
    <div className="bento-panel" style={{ height: '100%', gridArea: 'incidents' }}>
      <div className="bento-header">
        <span className="bento-title">Panel B // Critical Incident Core</span>
        <span className="tactical-mono" style={{ fontSize: '10px', color: '#FF3333', fontWeight: 'bold' }}>{incidents.length} ACTIVE</span>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sortedIncidents.length === 0 ? (
          <div className="tactical-mono" style={{ color: '#5c7080', fontSize: '11px', textAlign: 'center', padding: '20px' }}>
            [ NO INCIDENTS DETECTED ]
          </div>
        ) : (
          sortedIncidents.map(inc => {
            const { color, bg, icon } = getSeverityDetails(inc.severity);
            return (
              <div key={inc.id} style={{
                backgroundColor: '#121820',
                border: `1px solid ${color}`,
                borderLeft: `3px solid ${color}`,
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {icon}
                    <span className="tactical-mono" style={{ fontSize: '11px', fontWeight: 700, color: color }}>
                      {inc.severity?.toUpperCase() || 'INFO'}
                    </span>
                  </div>
                  <span className="tactical-mono" style={{ fontSize: '10px', color: '#5c7080' }}>{inc.timestamp}</span>
                </div>

                <h4 className="tactical-sans" style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>{inc.title}</h4>
                <p className="tactical-mono" style={{ fontSize: '11px', color: '#8a9ba8', lineHeight: '1.4' }}>{inc.description}</p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', paddingTop: '6px', borderTop: '1px solid #1a2433' }}>
                   <span className="tactical-mono" style={{ fontSize: '10px', color: '#5c7080' }}>Train: <span style={{color: '#fff'}}>{inc.train_number}</span></span>
                   <span className="tactical-mono" style={{ fontSize: '10px', color: inc.approved ? '#00FF66' : '#FFB000' }}>
                     {inc.approved ? 'RESOLVED' : 'PENDING'}
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
