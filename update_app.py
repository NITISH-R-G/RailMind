import re

with open("frontend/src/App.jsx", "r") as f:
    content = f.read()

# Replace local component rendering loops that were violating react hooks inside render

# Pull out sub-components outside of MainApp
# Then inject zustand variables

new_imports = """/* eslint-disable */
import React, { useState, useEffect, useRef, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import LiveMap from './components/LiveMap';
import IncidentFeed from './components/IncidentFeed';
import TaskBoard from './components/TaskBoard';
import RouteIntelligence from './components/RouteIntelligence';
import { ShieldAlert, AlertTriangle, Info, Check, CornerDownRight, Terminal, RefreshCw, X, Shield, User, HelpCircle, Activity, Bell, Settings } from 'lucide-react';
import { useStore } from './store';
import { List } from 'react-window';
"""

content = re.sub(r'/\* eslint-disable \*/\nimport React,.*?from \'lucide-react\';', new_imports, content, flags=re.DOTALL)

# Replace the MainApp state variables
state_vars = """
function MainApp() {
  const activeTab = useStore(state => state.activeTab);
  const setActiveTab = useStore(state => state.setActiveTab);
  const incidents = useStore(state => state.incidents);
  const setIncidents = useStore(state => state.setIncidents);
  const addIncident = useStore(state => state.addIncident);
  const updateIncidentApproved = useStore(state => state.updateIncidentApproved);
  const removeIncident = useStore(state => state.removeIncident);
  const tasks = useStore(state => state.tasks);
  const setTasks = useStore(state => state.setTasks);
  const resolveTask = useStore(state => state.resolveTask);
  const trains = useStore(state => state.trains);
  const setTrains = useStore(state => state.setTrains);
  const logs = useStore(state => state.logs);
  const addLog = useStore(state => state.addLog);
  const wsStatus = useStore(state => state.wsStatus);
  const setWsStatus = useStore(state => state.setWsStatus);
  const telemetry = useStore(state => state.telemetry);
  const setTelemetry = useStore(state => state.setTelemetry);

  const [loopCount, setLoopCount] = useState(0);
"""

content = re.sub(r'function MainApp\(\) \{\n\s*const \[activeTab, setActiveTab\] = useState\(\'Dashboard\'\);\n.*?const \[logs, setLogs\] = useState\(\[\]\);', state_vars, content, flags=re.DOTALL)

# Replace 'setIncidents(prev =>'
content = re.sub(r'setIncidents\(prev => \{\n\s*if \(prev\.some\(inc => inc\.id === newIncident\.id\)\) return prev;\n\s*return \[newIncident, \.\.\.prev\];\n\s*\}\);', r'addIncident(newIncident);', content, flags=re.DOTALL)

# Replace setLogs
content = re.sub(r'setLogs\(prev => \[\.\.\.prev, payload\]\.slice\(-200\)\); // Keep last 200 logs', r'addLog(payload);', content, flags=re.DOTALL)

# Replace incident acknowledge
content = re.sub(r'setIncidents\(prev => prev\.filter\(inc => inc\.id !== incidentId\)\);\n\s*setIncidentCount\(prev => Math\.max\(0, prev - 1\)\);', r'removeIncident(incidentId);', content, flags=re.DOTALL)

# Replace incident approve
content = re.sub(r'setIncidents\(prev => prev\.map\(inc => \{\n\s*if \(inc\.id === incidentId\) \{\n\s*return \{ \.\.\.inc, approved: true \};\n\s*\}\n\s*return inc;\n\s*\}\)\);', r'updateIncidentApproved(incidentId);', content, flags=re.DOTALL)

# Replace resolve task
content = re.sub(r'setTasks\(prev => prev\.map\(t => \{\n\s*if \(t\._id === taskId \|\| t\.id === taskId\) \{\n\s*return \{ \.\.\.t, status: \'resolved\', urgency: \'resolved\' \};\n\s*\}\n\s*return t;\n\s*\}\)\);', r'resolveTask(taskId);', content, flags=re.DOTALL)

# Apply bento layout to dashboard and terminal list to logs
bento = """
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

  const renderDashboard = () => (
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
  );
"""

# replace Dashboard render call in App.jsx return
content = re.sub(r'\{\s*activeTab === \'Dashboard\' &&.*?\}\s*\}', r'{activeTab === \'Dashboard\' && renderDashboard()}', content, flags=re.DOTALL)

with open("frontend/src/App.jsx", "w") as f:
    f.write(content)
