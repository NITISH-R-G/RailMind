import React, { useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useStore } from '../../store';

export default function LogStream() {
  const logs = useStore((state) => state.logs);
  const listRef = useRef();

  useEffect(() => {
    if (listRef.current && logs.length > 0) {
      listRef.current.scrollToItem(logs.length - 1, 'end');
    }
  }, [logs.length]);

  const Row = ({ index, style }) => {
    const log = logs[index];
    let color = '#5c7080';
    if (log.includes('CRITICAL') || log.includes('ERROR')) color = '#FF3333';
    else if (log.includes('WARN')) color = '#FFB000';
    else if (log.includes('SUCCESS') || log.includes('RESOLVED')) color = '#00FF66';
    else if (log.includes('AGENT')) color = '#00f0ff';

    const timestamp = new Date().toISOString().substring(11, 23); // HH:mm:ss.SSS

    return (
      <div style={{ ...style, display: 'flex', gap: '8px', alignItems: 'center', padding: '0 8px', borderBottom: '1px solid #1a2433' }}>
        <span className="tactical-mono" style={{ fontSize: '10px', color: '#5c7080', flexShrink: 0 }}>[{timestamp}]</span>
        <span className="tactical-mono" style={{ fontSize: '10px', color: color, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {log}
        </span>
      </div>
    );
  };

  return (
    <div className="bento-panel" style={{ height: '100%', gridArea: 'logs' }}>
      <div className="bento-header">
        <span className="bento-title">Panel A // Ingestion Stream</span>
        <div className="pulse-dot-green"></div>
      </div>
      <div style={{ flex: 1, backgroundColor: '#0A0E17', padding: '4px 0' }}>
        {logs.length === 0 ? (
          <div className="tactical-mono" style={{ color: '#5c7080', fontSize: '10px', padding: '12px' }}>[ WAITING FOR TELEMETRY STREAM... ]</div>
        ) : (
          <List
            ref={listRef}
            height={200} // This will be dynamic based on parent size, but setting a default
            itemCount={logs.length}
            itemSize={24}
            width={'100%'}
            style={{ height: '100%' }}
          >
            {Row}
          </List>
        )}
      </div>
    </div>
  );
}
