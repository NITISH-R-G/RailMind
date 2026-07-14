import React, { useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import LiveMap from './components/LiveMap';
import LogStreamPanel from './components/LogStreamPanel';
import IncidentCorePanel from './components/IncidentCorePanel';
import TaskSyncPanel from './components/TaskSyncPanel';
import TelemetryOverviewPanel from './components/TelemetryOverviewPanel';
import useStore from './store';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) { return { hasError: true }; }
  componentDidCatch(error, errorInfo) { console.error("[ERROR BOUNDARY]", error, errorInfo); }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', backgroundColor: '#0A0E17', color: '#FF3333', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontFamily: "'JetBrains Mono', monospace", gap: '16px' }}>
          <h2 style={{ fontWeight: 600 }}>[ SYSTEM ERROR // UI CRASH ]</h2>
          <button onClick={() => window.location.reload()} style={{ padding: '10px 20px', backgroundColor: '#00FF66', color: '#0A0E17', border: 'none', fontWeight: 700, cursor: 'pointer' }}>REBOOT SYSTEM</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainApp() {
  const socketRef = useRef(null);
  const API_BASE = `http://${window.location.hostname}:8000`;

  const setTrains = useStore(state => state.setTrains);
  const setIncidents = useStore(state => state.setIncidents);
  const setTasks = useStore(state => state.setTasks);
  const addLog = useStore(state => state.addLog);
  const setTelemetry = useStore(state => state.setTelemetry);
  const setLoopCount = useStore(state => state.setLoopCount);
  const setWsStatus = useStore(state => state.setWsStatus);
  const addIncident = useStore(state => state.addIncident);

  const loopCount = useStore(state => state.loopCount);
  const incidentCount = useStore(state => state.incidentCount);
  const wsStatus = useStore(state => state.wsStatus);

  // Initial Fetchers
  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents`);
      if (res.ok) {
        const data = await res.json();
        const formatted = data.map(inc => ({
          id: inc.incident_id || inc._id,
          severity: inc.severity || "info",
          title: inc.incident_title || inc.summary || "Anomaly",
          description: inc.situation_summary || inc.summary || "Investigating.",
          timestamp: inc.timestamp,
          train_number: inc.train_number || 'Unknown',
          approved: inc.resolution_status === 'approved',
          reroute_plan: inc.reroute_plan
        }));
        setIncidents(formatted);
      }
    } catch (err) { console.error("Fetch incidents failed:", err); }
  };

  const fetchTrains = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/trains`);
      if (res.ok) setTrains(await res.json());
    } catch (err) { console.error("Fetch trains failed:", err); }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dept-tasks`);
      if (res.ok) setTasks(await res.json());
    } catch (err) { console.error("Fetch tasks failed:", err); }
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/telemetry`);
      if (res.ok) setTelemetry(await res.json());
    } catch (err) { console.error("Fetch telemetry failed:", err); }
  };

  // Setup Connections
  useEffect(() => {
    fetchIncidents();
    fetchTrains();
    fetchTasks();
    fetchTelemetry();

    const trainInterval = setInterval(fetchTrains, 5000);
    const telemetryInterval = setInterval(fetchTelemetry, 5000);

    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    let reconnectTimeout;

    const connectWS = () => {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => setWsStatus('connected');

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'INCIDENT_UPDATE') {
            const report = payload.data;
            addIncident({
              id: report.incident_id,
              severity: report.severity || "info",
              title: report.incident_title || report.summary || "Anomaly",
              timestamp: report.timestamp,
              train_number: report.train_number || 'Unknown',
              approved: report.resolution_status === 'approved',
              reroute_plan: report.reroute_plan
            });
            if (report.loop_count !== undefined) setLoopCount(report.loop_count);
            fetchTasks();
            fetchTrains();
          } else if (payload.type === 'AGENT_LOG') {
            addLog(payload);
          }
        } catch (err) { console.error("WS Parse error:", err); }
      };

      socket.onclose = () => {
        setWsStatus('reconnecting');
        reconnectTimeout = setTimeout(connectWS, 3000);
      };

      socket.onerror = (err) => socket.close();
    };

    connectWS();

    return () => {
      if (socketRef.current) socketRef.current.close();
      clearTimeout(reconnectTimeout);
      clearInterval(trainInterval);
      clearInterval(telemetryInterval);
    };
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0A0E17', overflow: 'hidden' }}>
      <TopBar loopCount={loopCount} incidentCount={incidentCount} wsStatus={wsStatus} />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />

        {/* CSS Grid Bento Layout for Main Content */}
        <div style={{
          flex: 1,
          padding: '16px',
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr 1fr',
          gridTemplateRows: '1.5fr 1fr',
          gap: '16px',
          overflow: 'hidden'
        }}>
          {/* Top Left: Live Map spans 2 cols, 1 row */}
          <div style={{ gridColumn: 'span 2', gridRow: 'span 1' }}>
            <LiveMap />
          </div>

          {/* Top Right: Incident Core spans 1 col, 1 row */}
          <div style={{ gridColumn: 'span 1', gridRow: 'span 1' }}>
            <IncidentCorePanel />
          </div>

          {/* Bottom Left: Log Stream spans 1 col, 1 row */}
          <div style={{ gridColumn: 'span 1', gridRow: 'span 1' }}>
            <LogStreamPanel />
          </div>

          {/* Bottom Middle: Task Sync spans 1 col, 1 row */}
          <div style={{ gridColumn: 'span 1', gridRow: 'span 1' }}>
            <TaskSyncPanel />
          </div>

          {/* Bottom Right: Telemetry spans 1 col, 1 row */}
          <div style={{ gridColumn: 'span 1', gridRow: 'span 1' }}>
            <TelemetryOverviewPanel />
          </div>
        </div>
      </div>
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
