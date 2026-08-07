/* eslint-disable */
import React, { useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import LiveMap from './components/LiveMap';
import IncidentFeed from './components/IncidentFeed';
import TaskBoard from './components/TaskBoard';
import { X } from 'lucide-react';
import { FixedSizeList as List } from 'react-window';
import { useStore } from './store';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[ERROR BOUNDARY] Caught rendering error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px',
          backgroundColor: '#0A0E17',
          color: '#FF3333',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: "'JetBrains Mono', monospace",
          gap: '16px'
        }}>
          <h2 style={{ fontWeight: 600 }}>[ SYSTEM ERROR // RAILMIND CRASH ]</h2>
          <p style={{ color: '#8a9ba8', fontSize: '13px' }}>RailMind Dashboard encountered an unrecoverable rendering error.</p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#00f0ff',
              color: '#080a0d',
              border: '1px solid #00f0ff',
              borderRadius: '0px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
          >
            REBOOT SYSTEM
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const LogsViewStream = () => {
  // Subscribe specifically to logs to avoid rendering MainApp on high-freq updates
  const logs = useStore(state => state.logs);
  
  const Row = ({ index, style }) => {
    const log = logs[index];
    return (
      <div style={{ ...style, lineBreak: 'anywhere', padding: '0 8px', boxSizing: 'border-box' }}>
        <span style={{ color: '#FFB000' }}>{log.message.substring(0, 21)}</span>
        <span style={{ color: '#00FF66' }}>{log.message.substring(21, 35)}</span>
        <span style={{ color: '#e2e8f0' }}>{log.message.substring(35)}</span>
      </div>
    );
  };

  return (
    <div style={{ flex: 1, backgroundColor: '#0A0E17', border: '1px solid #26354A', position: 'relative', overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, padding: '6px 12px',
        borderBottom: '1px solid #26354A', backgroundColor: '#161F30', zIndex: 1,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <span className="palantir-mono" style={{ fontSize: '11px', color: '#00FF66', fontWeight: 600, letterSpacing: '0.5px' }}>LIVE INGESTION STREAM (AGENT_LOG)</span>
        <span className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080' }}>COUNT: {logs.length}</span>
      </div>
      <div style={{ height: '100%', paddingTop: '30px', boxSizing: 'border-box' }}>
        {logs.length > 0 ? (
          <List
            height={170}
            itemCount={logs.length}
            itemSize={24}
            width="100%"
            style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '11px' }}
          >
            {Row}
          </List>
        ) : (
          <div className="palantir-mono" style={{ padding: '12px', color: '#5c7080', fontSize: '11px' }}>[ NO INGESTION LOGS DETECTED ]</div>
        )}
      </div>
    </div>
  );
};

const TelemetryOverview = () => {
  const telemetry = useStore(state => state.telemetry);

  const metrics = [
    { name: 'AGENT LOOP', value: telemetry?.agent_loop_status?.toUpperCase() || 'RUNNING', color: '#00FF66' },
    { name: 'API LATENCY', value: `${telemetry?.railways_latency_ms || 0} ms`, color: '#00f0ff' },
    { name: 'AI LATENCY', value: `${telemetry?.ai_latency_ms || 0} ms`, color: '#00f0ff' },
    { name: 'WS CLIENTS', value: telemetry?.websocket_clients || 0, color: '#FFB000' }
  ];

  return (
    <div style={{ flex: 1, backgroundColor: '#0A0E17', border: '1px solid #26354A', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #26354A', backgroundColor: '#161F30' }}>
        <span className="palantir-mono" style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600, letterSpacing: '0.5px' }}>TELEMETRY OVERVIEW</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', padding: '12px', overflowY: 'auto' }}>
        {metrics.map((m, idx) => (
          <div key={idx} style={{
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            padding: '10px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <span className="palantir-mono" style={{ fontSize: '9px', fontWeight: 600, color: '#5c7080' }}>{m.name}</span>
            <span className="palantir-mono" style={{ fontSize: '14px', fontWeight: 700, color: m.color }}>{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

function MainApp() {
  const activeTab = useStore(state => state.activeTab);
  const wsStatus = useStore(state => state.wsStatus);
  const showSettings = useStore(state => state.showSettings);
  const setShowSettings = useStore(state => state.setShowSettings);
  const showNotifications = useStore(state => state.showNotifications);
  const setShowNotifications = useStore(state => state.setShowNotifications);
  const showProfile = useStore(state => state.showProfile);
  const setShowProfile = useStore(state => state.setShowProfile);
  const incidentCount = useStore(state => state.incidentCount);

  // Stable actions for hooks
  const fetchIncidents = useStore(state => state.fetchIncidents);
  const fetchTrains = useStore(state => state.fetchTrains);
  const fetchTasks = useStore(state => state.fetchTasks);
  const fetchTelemetry = useStore(state => state.fetchTelemetry);
  const setWsStatus = useStore(state => state.setWsStatus);
  const setLoopCount = useStore(state => state.setLoopCount);
  const setIncidentCount = useStore(state => state.setIncidentCount);
  const setIncidents = useStore(state => state.setIncidents);
  const setLogs = useStore(state => state.setLogs);

  const socketRef = useRef(null);

  useEffect(() => {
    fetchIncidents();
    fetchTrains();
    fetchTasks();
    fetchTelemetry();

    const trainInterval = setInterval(fetchTrains, 5000);
    const telemetryInterval = setInterval(fetchTelemetry, 5000);
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    let socket;
    let reconnectTimeout;

    const connectWS = () => {
      console.log("[WEBSOCKET] Connecting to:", wsUrl);
      socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log("[WEBSOCKET] Connected to RailMind WebSocket server");
        setWsStatus('connected');
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          
          if (payload.type === 'INCIDENT_UPDATE') {
            const report = payload.data;
            
            const newIncident = {
              id: report.incident_id,
              severity: report.severity || "info",
              title: report.incident_title || report.summary || "New Incident Logged",
              description: report.situation_summary || report.summary || "Investigating operational status.",
              timestamp: new Date(report.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              incident_title: report.incident_title || report.summary || "New Incident Logged",
              situation_summary: report.situation_summary || report.summary || "Investigating operational status.",
              reroute_plan: report.reroute_plan || null,
              maintenance_task: report.maintenance_task || '',
              operations_task: report.operations_task || '',
              station_manager_task: report.station_manager_task || '',
              passenger_sms: report.passenger_sms || '',
              resolution_status: report.resolution_status || 'pending',
              approved: report.resolution_status === 'approved',
              departments: report.departments_notified || [],
              train_number: report.train_number || 'Unknown'
            };

            const currentIncidents = useStore.getState().incidents;
            const updated = [newIncident, ...currentIncidents].filter((v,i,a)=>a.findIndex(v2=>(v2.id===v.id))===i);
            setIncidents(updated);
            setIncidentCount(updated.length);

            if (report.loop_count !== undefined) {
              setLoopCount(report.loop_count);
            }

            fetchTasks();
            fetchTrains();
          } else if (payload.type === 'AGENT_LOG') {
            const currentLogs = useStore.getState().logs;
            setLogs([...currentLogs, payload].slice(-200));
          }
        } catch (err) {
          console.error("[WEBSOCKET] Error parsing socket data:", err);
        }
      };

      socket.onclose = () => {
        console.log("[WEBSOCKET] Closed. Reconnecting in 3 seconds...");
        setWsStatus('reconnecting');
        reconnectTimeout = setTimeout(connectWS, 3000);
      };

      socket.onerror = (err) => {
        console.error("[WEBSOCKET] Error encountered:", err);
        socket.close();
      };
    };

    connectWS();

    return () => {
      if (socket) socket.close();
      clearTimeout(reconnectTimeout);
      clearInterval(trainInterval);
      clearInterval(telemetryInterval);
    };
  }, [fetchIncidents, fetchTrains, fetchTasks, fetchTelemetry, setWsStatus, setLoopCount, setIncidentCount, setIncidents, setLogs]);

  const renderContent = () => {
    switch (activeTab) {
      case 'Dashboard':
      case 'Live Map':
        return (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '250px 1fr 350px',
            gridTemplateRows: '1fr 1fr 200px',
            gap: '12px',
            height: '100%',
            padding: '12px',
            boxSizing: 'border-box'
          }}>
            {/* Left Area (Panel D: Telemetry, Panel C: Tasks) */}
            <div style={{ gridColumn: '1 / 2', gridRow: '1 / 2', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
               <TelemetryOverview />
            </div>
            <div style={{ gridColumn: '1 / 2', gridRow: '2 / 4', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
               <div style={{ flex: 1, backgroundColor: '#0A0E17', border: '1px solid #26354A', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                 <div style={{ padding: '10px 12px', borderBottom: '1px solid #26354A', backgroundColor: '#161F30' }}>
                    <span className="palantir-mono" style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600, letterSpacing: '0.5px' }}>DISPATCH QUEUE</span>
                 </div>
                 <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                    <TaskBoard compact={true} />
                 </div>
               </div>
            </div>

            {/* Center Area (Live Map) */}
            <div style={{ gridColumn: '2 / 3', gridRow: '1 / 3', border: '1px solid #26354A', backgroundColor: '#161F30', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
               <LiveMap fullScreen={false} />
            </div>

            {/* Right Area (Panel B: Incident Feed) */}
            <div style={{ gridColumn: '3 / 4', gridRow: '1 / 4', border: '1px solid #26354A', backgroundColor: '#161F30', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
               <IncidentFeed />
            </div>

            {/* Bottom Area (Panel A: Log Stream) */}
            <div style={{ gridColumn: '2 / 3', gridRow: '3 / 4', display: 'flex' }}>
               <LogsViewStream />
            </div>
          </div>
        );

      case 'Incident Feed':
        return (
          <div style={{ padding: '12px', height: '100%', boxSizing: 'border-box', backgroundColor: '#0A0E17' }}>
            <div style={{ height: '100%', border: '1px solid #26354A', backgroundColor: '#161F30' }}>
               <IncidentFeed />
            </div>
          </div>
        );

      case 'Task Board':
        return (
          <div style={{ padding: '12px', height: '100%', boxSizing: 'border-box', backgroundColor: '#0A0E17' }}>
            <TaskBoard fullScreen={true} />
          </div>
        );

      case 'Analytics':
      case 'Simulation':
      case 'Sensor Data':
      case 'Timetable':
      case 'Fleet':
        return <div className="palantir-mono" style={{ padding: '24px', fontSize: '12px', color: '#5c7080' }}>[ PANEL REDIRECTED OR NOT IMPLEMENTED IN CURRENT VIEW ]</div>;

      default:
        return <div className="palantir-mono" style={{ padding: '24px', fontSize: '12px', color: '#FF3333' }}>[ PAGE NOT DEPLOYED ]</div>;
    }
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '240px 1fr',
      gridTemplateRows: '64px 1fr',
      height: '100vh',
      backgroundColor: '#0A0E17',
      color: '#e2e8f0',
      overflow: 'hidden'
    }}>

      {/* Top Bar spanning right of sidebar */}
      <div style={{ gridColumn: '1 / 3', gridRow: '1 / 2' }}>
        <TopBar />
      </div>

      {wsStatus === 'reconnecting' && (
        <div style={{
          position: 'absolute',
          top: '64px',
          left: '240px',
          right: 0,
          backgroundColor: '#FF3333',
          color: '#ffffff',
          textAlign: 'center',
          padding: '4px 24px',
          fontSize: '10px',
          fontWeight: 700,
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: '1px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          zIndex: 1000,
          borderBottom: '1px solid #FF3333'
        }}>
          <span style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            backgroundColor: '#ffffff',
            borderRadius: '0px',
            animation: 'pulse-live 1s infinite'
          }}></span>
          [ OFFLINE // RE-ESTABLISHING AGENT CONNECTION... ]
        </div>
      )}

      {/* Sidebar */}
      <div style={{ gridColumn: '1 / 2', gridRow: '2 / 3', borderRight: '1px solid #26354A', backgroundColor: '#0A0E17', overflowY: 'auto' }}>
        <Sidebar />
      </div>

      {/* Main Content Area */}
      <div style={{ gridColumn: '2 / 3', gridRow: '2 / 3', overflow: 'hidden', position: 'relative' }}>
        {renderContent()}
      </div>

      {/* Modals */}
      {showSettings && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          backgroundColor: 'rgba(10, 14, 23, 0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999
        }}>
          <div style={{
            backgroundColor: '#161F30', border: '1px solid #00FF66', padding: '24px', width: '420px', display: 'flex', flexDirection: 'column', gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3 className="palantir-mono" style={{ fontSize: '14px', color: '#00FF66' }}>SYSTEM // CONFIGURATION</h3>
              <button onClick={() => setShowSettings(false)} style={{ background: 'transparent', border: 'none', color: '#5c7080', cursor: 'pointer' }}><X size={18} /></button>
            </div>
          </div>
        </div>
      )}

      {showNotifications && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          backgroundColor: 'rgba(10, 14, 23, 0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999
        }}>
          <div style={{
            backgroundColor: '#161F30', border: '1px solid #FF3333', padding: '24px', width: '420px', display: 'flex', flexDirection: 'column', gap: '16px'
          }}>
             <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3 className="palantir-mono" style={{ fontSize: '14px', color: '#FF3333' }}>REAL-TIME WARNINGS STREAM</h3>
              <button onClick={() => setShowNotifications(false)} style={{ background: 'transparent', border: 'none', color: '#5c7080', cursor: 'pointer' }}><X size={18} /></button>
            </div>
            <div className="palantir-mono" style={{ color: '#5c7080', fontSize: '11px' }}>{incidentCount} active alerts.</div>
          </div>
        </div>
      )}

      {showProfile && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          backgroundColor: 'rgba(10, 14, 23, 0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999
        }}>
          <div style={{
            backgroundColor: '#161F30', border: '1px solid #00f0ff', padding: '28px', width: '380px', display: 'flex', flexDirection: 'column', gap: '16px'
          }}>
             <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3 className="palantir-mono" style={{ fontSize: '14px', color: '#00f0ff' }}>OPERATOR PROFILE</h3>
              <button onClick={() => setShowProfile(false)} style={{ background: 'transparent', border: 'none', color: '#5c7080', cursor: 'pointer' }}><X size={18} /></button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <MainApp />
    </ErrorBoundary>
  );
}
