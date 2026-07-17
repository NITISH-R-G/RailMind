const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.jsx', 'utf8');

content = content.replace(/setIncidentCount\(formatted\.length\);/g, '');
content = content.replace(/setIncidentCount\(prev => Math\.max\(0, prev - 1\)\);/g, '');

const dashboard_render = `
  const LogRow = React.memo(({ index, style, data }) => {
    const log = data[index];
    if (!log) return null;
    return (
      <div style={{ ...style, display: 'flex', gap: '8px', borderBottom: '1px solid #26354A', padding: '4px' }}>
        <span style={{ color: '#5c7080' }}>[{log.timestamp}]</span>
        <span style={{ color: '#00FF66', minWidth: '100px' }}>{log.agent}</span>
        <span style={{ color: '#e2e8f0' }}>{log.message}</span>
      </div>
    );
  });

  const DashboardView = React.memo(({ trains, incidents, logs, handleApprove, handleAcknowledge, handleResolve, tasks }) => (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflowY: 'auto', backgroundColor: '#0A0E17' }}>

      {/* Telemetry Overview Card */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {[
          { label: "Active Connections", val: "142", col: "#00FF66" },
          { label: "Processing Latency", val: "14ms", col: "#00FF66" },
          { label: "Queue Depth", val: "2", col: "#FFB000" },
          { label: "System Load", val: "34%", col: "#00FF66" }
        ].map((m, i) => (
          <div key={i} style={{ border: '1px solid #26354A', padding: '16px', backgroundColor: '#161F30' }}>
            <div style={{ color: '#8a9ba8', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase' }}>{m.label}</div>
            <div style={{ color: m.col, fontSize: '24px', fontWeight: 'bold' }}>{m.val}</div>
          </div>
        ))}
      </div>

      {/* Bento Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px', minHeight: '500px' }}>
        {/* Map / Route Intelligence */}
        <div style={{ border: '1px solid #26354A', backgroundColor: '#161F30', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #26354A', fontWeight: 'bold', color: '#e2e8f0' }}>TACTICAL MAP OVERVIEW</div>
          <div style={{ flex: 1, position: 'relative' }}>
             <LiveMap trains={trains} incidents={incidents} />
          </div>
        </div>

        {/* Live Ingestion Stream */}
        <div style={{ border: '1px solid #26354A', backgroundColor: '#161F30', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #26354A', fontWeight: 'bold', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={16} /> LIVE INGESTION STREAM
          </div>
          <div style={{ flex: 1, padding: '8px', fontSize: '11px', fontFamily: "'JetBrains Mono', monospace", backgroundColor: '#0A0E17' }}>
            {logs.length > 0 ? (
               <List
                 height={440}
                 itemCount={logs.length}
                 itemSize={24}
                 width="100%"
                 itemData={logs}
               >
                 {LogRow}
               </List>
            ) : (
              <div style={{ color: '#5c7080' }}>Awaiting telemetry streams...</div>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
         <div style={{ border: '1px solid #26354A', backgroundColor: '#161F30', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #26354A', fontWeight: 'bold', color: '#e2e8f0' }}>CRITICAL INCIDENT CORE</div>
            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
               <IncidentFeed incidents={incidents} onApprove={handleApprove} onAcknowledge={handleAcknowledge} />
            </div>
         </div>
         <div style={{ border: '1px solid #26354A', backgroundColor: '#161F30', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #26354A', fontWeight: 'bold', color: '#e2e8f0' }}>MULTI-DEPARTMENT TASK SYNCHRONIZATION</div>
            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
               <TaskBoard tasks={tasks} onResolve={handleResolve} />
            </div>
         </div>
      </div>
    </div>
  ));
`;

content = content.replace(/const DashboardView = \(\) => \{\n\s*return \(\n\s*<div style=\{\{ padding: '24px', flex: 1, overflowY: 'auto' \}\}>[\s\S]*?\}\);/m, dashboard_render);

content = content.replace(/<DashboardView \/>/g, '<DashboardView trains={trains} incidents={incidents} logs={logs} handleApprove={handleApprove} handleAcknowledge={handleAcknowledge} handleResolve={handleResolve} tasks={tasks} />');

fs.writeFileSync('frontend/src/App.jsx', content);
