/* eslint-disable */
import React, { useState, useRef, useEffect } from 'react';
import { CornerDownRight, Check, X } from 'lucide-react';
import { VariableSizeList as List } from 'react-window';
import { useStore } from '../store';

export default function IncidentFeed() {
  const [filter, setFilter] = useState('ALL');
  const [expandedIncident, setExpandedIncident] = useState(null);
  const listRef = useRef(null);

  const incidents = useStore(state => state.incidents);
  const handleApprove = useStore(state => state.handleApprove);
  const handleAcknowledge = useStore(state => state.handleAcknowledge);

  const filteredIncidents = incidents.filter(inc => {
    if (filter === 'ALL') return true;
    return inc.severity?.toUpperCase() === filter;
  });

  // Force re-calculation of heights when an incident expands or collapses
  useEffect(() => {
    if (listRef.current) {
      listRef.current.resetAfterIndex(0);
    }
  }, [expandedIncident, filteredIncidents.length]);

  const Row = ({ index, style }) => {
    const inc = filteredIncidents[index];
    const isCritical = inc.severity === 'critical';
    const isWarning = inc.severity === 'warning';
    const borderColor = isCritical ? '#FF3333' : isWarning ? '#FFB000' : '#00FF66';
    const isExpanded = expandedIncident === inc.id;

    return (
      <div style={{ ...style, paddingRight: '12px', paddingBottom: '12px', boxSizing: 'border-box' }}>
        <div style={{
          backgroundColor: '#161F30',
          border: '1px solid #26354A',
          borderLeft: `4px solid ${borderColor}`,
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          height: '100%',
          boxSizing: 'border-box',
          overflow: 'hidden'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="palantir-mono" style={{
              fontSize: '9px',
              fontWeight: 700,
              color: borderColor,
              backgroundColor: `${borderColor}1A`,
              padding: '3px 8px',
              border: `1px solid ${borderColor}`,
              textTransform: 'uppercase'
            }}>{inc.severity}</span>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="palantir-mono" style={{ fontSize: '11px', color: '#5c7080' }}>{inc.timestamp}</span>
              <button onClick={() => handleAcknowledge(inc.id)} style={{ background: 'transparent', border: 'none', color: '#5c7080', cursor: 'pointer', padding: 0 }} title="Dismiss Alert"><X size={14} /></button>
            </div>
          </div>

          <div>
            <h3 className="palantir-mono" style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{inc.title}</h3>
            <p className="palantir-mono" style={{ fontSize: '10px', color: '#8a9ba8', marginTop: '4px' }}>TRAIN: {inc.train_number}</p>
          </div>

          {inc.reroute_plan && (
            <div style={{
              backgroundColor: '#0A0E17',
              border: '1px dashed #26354A',
              padding: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <div className="palantir-mono" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '9px', color: '#00FF66', fontWeight: 700 }}>
                <CornerDownRight size={12} /> REROUTE PLAN COMMAND
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                <span className="palantir-mono" style={{ fontSize: '10px', color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{inc.reroute_plan}</span>
                {inc.approved ? (
                  <span className="palantir-mono" style={{ color: '#00FF66', fontSize: '10px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                    <Check size={12} /> APPROVED
                  </span>
                ) : (
                  <button
                    onClick={() => handleApprove(inc.id)}
                    className="palantir-mono"
                    style={{
                      backgroundColor: 'transparent',
                      color: '#00FF66',
                      border: '1px solid #00FF66',
                      padding: '4px 8px',
                      fontSize: '9px',
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    APPROVE
                  </button>
                )}
              </div>
            </div>
          )}

          <div style={{ borderTop: '1px solid #26354A', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>
              DISPATCH: {inc.departments?.join(' / ') || 'NONE'}
            </span>
            <button
              onClick={() => setExpandedIncident(isExpanded ? null : inc.id)}
              className="palantir-mono"
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: '#8a9ba8',
                fontSize: '9px',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              {isExpanded ? 'HIDE' : 'DETAILS'}
            </button>
          </div>

          {isExpanded && (
            <div className="palantir-mono" style={{
              backgroundColor: '#0A0E17',
              border: '1px solid #26354A',
              padding: '10px',
              fontSize: '10px',
              color: '#8a9ba8',
              whiteSpace: 'pre-wrap',
              marginTop: '4px',
              overflowY: 'auto',
              flex: 1
            }}>
              {inc.description}
            </div>
          )}
        </div>
      </div>
    );
  };

  const getItemSize = (index) => {
    const inc = filteredIncidents[index];
    const isExpanded = expandedIncident === inc.id;
    let baseHeight = 150;
    if (inc.reroute_plan) baseHeight += 70;
    if (isExpanded) baseHeight += 120;
    return baseHeight + 12; // padding bottom
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: '#0A0E17', border: '1px solid #26354A' }}>

      {/* Header */}
      <div style={{ padding: '16px', borderBottom: '1px solid #26354A', backgroundColor: '#161F30' }}>
        <h2 className="palantir-mono" style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '0.5px' }}>ANOMALY COMMAND CENTER</h2>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
          <div style={{ display: 'flex', gap: '4px' }}>
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="palantir-mono"
                style={{
                  padding: '4px 8px',
                  backgroundColor: filter === f ? '#26354A' : 'transparent',
                  color: filter === f ? '#e2e8f0' : '#5c7080',
                  border: '1px solid #26354A',
                  fontSize: '9px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Feed List */}
      <div style={{ flex: 1, padding: '12px 0 12px 12px', overflow: 'hidden' }}>
        {filteredIncidents.length === 0 ? (
          <div className="palantir-mono" style={{ padding: '24px', textAlign: 'center', color: '#5c7080', fontSize: '11px' }}>
            [ NO ANOMALIES RECORDED FOR STATUS: {filter} ]
          </div>
        ) : (
          <List
            ref={listRef}
            height={600}
            itemCount={filteredIncidents.length}
            itemSize={getItemSize}
            width="100%"
            style={{ height: '100%' }}
          >
            {Row}
          </List>
        )}
      </div>

    </div>
  );
}
