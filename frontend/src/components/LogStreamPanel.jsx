import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from 'lucide-react';
import { List } from 'react-window';
import useStore from '../store';

const LogRow = ({ index, style, data }) => {
  const log = data[index];
  return (
    <div style={{ ...style, display: 'flex', gap: '8px', alignItems: 'center', borderBottom: '1px solid #161F30', padding: '0 8px' }}>
      <span style={{ color: '#5c7080', fontSize: '10px' }}>
        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
      </span>
      <span style={{ color: '#00FF66', fontSize: '11px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {log.message || JSON.stringify(log)}
      </span>
    </div>
  );
};

export default function LogStreamPanel() {
  const logs = useStore((state) => state.logs);
  const listRef = useRef(null);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (listRef.current && logs.length > 0) {
      listRef.current.scrollToItem(logs.length - 1, 'end');
    }
  }, [logs]);

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
        <Terminal size={14} color="#00FF66" />
        <span className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0' }}>LIVE INGESTION STREAM</span>
      </div>

      <div ref={containerRef} style={{ flex: 1, overflow: 'hidden' }} className="palantir-mono">
        {logs.length === 0 ? (
          <div style={{ padding: '12px', color: '#5c7080', fontSize: '11px', fontStyle: 'italic' }}>
            [SYSTEM] Awaiting live logs...
          </div>
        ) : (
          <List
            ref={listRef}
            height={dimensions.height}
            itemCount={logs.length}
            itemSize={24}
            width={dimensions.width}
            itemData={logs}
          >
            {LogRow}
          </List>
        )}
      </div>
    </div>
  );
}
