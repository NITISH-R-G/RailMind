import React, { useState, useEffect, useRef } from 'react';
import useStore from './store';
import { ShieldAlert, AlertTriangle, Terminal, Activity, Check, CheckCircle, RefreshCw } from 'lucide-react';
import LiveMap from './components/LiveMap';
import { List } from 'react-window';

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
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#00FF66',
              color: '#0A0E17',
              border: 'none',
              borderRadius: '0px',
              fontWeight: 700,
              cursor: 'pointer'
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

function MainApp() {
  const {
    trains, setTrains,
    incidents, setIncidents, addOrUpdateIncident,
    tasks, setTasks,
    logs, addLog,
    telemetry, setTelemetry,
    updateTask, updateIncident
  } = useStore();

  const [wsStatus, setWsStatus] = useState('reconnecting');
  const socketRef = useRef(null);
  const API_BASE = `http://${window.location.hostname}:8000`;

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/incidents`);
      if (res.ok) {
        const data = await res.json();
        const formatted = data.map(inc => ({
          id: inc.incident_id || inc._id,
          severity: inc.severity || "info",
          title: inc.incident_title || inc.summary || "Operations Anomaly",
          description: inc.situation_summary || inc.summary || "Investigating operational status.",
          timestamp: new Date(inc.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          incident_title: inc.incident_title || inc.summary || "Operations Anomaly",
          situation_summary: inc.situation_summary || inc.summary || "Investigating operational status.",
          reroute_plan: inc.reroute_plan || null,
          maintenance_task: inc.maintenance_task || '',
          operations_task: inc.operations_task || '',
          station_manager_task: inc.station_manager_task || '',
          passenger_sms: inc.passenger_sms || '',
          resolution_status: inc.resolution_status || 'pending',
          approved: inc.resolution_status === 'approved',
          departments: inc.departments_notified || [],
          train_number: inc.train_number || 'Unknown'
        }));
        setIncidents(formatted);
      }
    } catch (err) {
      console.error("[API] Failed to fetch incidents:", err);
    }
  };

  const fetchTrains = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/trains`);
      if (res.ok) {
        const data = await res.json();
        setTrains(data);
      }
    } catch (err) {
      console.error("[API] Failed to fetch trains:", err);
    }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dept-tasks`);
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (err) {
      console.error("[API] Failed to fetch department tasks:", err);
    }
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/telemetry`);
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (err) {
      console.error("[API] Failed to fetch telemetry:", err);
    }
  };

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
        // Trigger state recovery protocol
        socket.send(JSON.stringify({ type: "SYNC_STATE" }));
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
            addOrUpdateIncident(newIncident);
            fetchTasks();
            fetchTrains();
          } else if (payload.type === 'AGENT_LOG') {
            addLog(payload);
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
  }, []);

  const handleApprove = async (incidentId) => {
    const adminPassword = window.prompt("Enter Admin Password to approve this reroute plan:");
    if (adminPassword === null) return;
    try {
      const headers = new Headers();
      headers.set('Authorization', 'Basic ' + btoa('admin:' + adminPassword));
      const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/approve`, {
        method: 'POST',
        headers: headers
      });
      if (res.ok) {
        updateIncident(incidentId, { approved: true });
      } else {
        alert("Unauthorized or failed to approve.");
      }
    } catch (err) {
      console.error("Error approving:", err);
    }
  };

  const handleResolveTask = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/api/dept-tasks/${taskId}/resolve`, { method: 'POST' });
      if (res.ok) {
        updateTask(taskId, { status: 'resolved', urgency: 'resolved' });
      }
    } catch (err) {
      console.error("Error resolving task:", err);
    }
  };

  // --- Panels implementation will follow in next steps ---

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-main)', overflow: 'hidden' }}>

      {/* Top Bar Tactical Header */}
      <div style={{
        height: '48px',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        backgroundColor: 'var(--bg-panel)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ShieldAlert size={20} color="var(--accent-color)" />
          <span className="palantir-mono" style={{ fontSize: '16px', fontWeight: 700, letterSpacing: '1px' }}>COMMAND CORE // RAILMIND TACTICAL</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div className="palantir-mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            WS: {wsStatus === 'connected' ? <span style={{color: 'var(--accent-color)'}}>ONLINE</span> : <span style={{color: 'var(--color-critical)'}}>OFFLINE</span>}
          </div>
          <div className="palantir-mono" style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            ACTIVE TRAINS: <span style={{color: '#fff'}}>{trains.length}</span>
          </div>
        </div>
      </div>

      {/* Main Grid Area */}
      <div style={{ flex: 1, position: 'relative' }}>
        <div className="bento-grid">
          <div className="bento-panel panel-map" style={{ padding: 0, overflow: 'hidden' }}>
            <LiveMap trains={trains} incidents={incidents} />
          </div>

          <div className="bento-panel panel-a">
            <div className="bento-panel-header">
              <Terminal size={16} color="var(--accent-color)"/> LIVE INGESTION STREAM
            </div>
            <div className="bento-panel-content palantir-mono" style={{ padding: 0, backgroundColor: '#05070A', display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                {logs.length === 0 ? (
                  <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '11px', fontStyle: 'italic' }}>[ AWAITING AGENT LOGS... ]</div>
                ) : (
                  <List
                    height={1000} // React-window needs a height, we'll let it be large and overflow hidden container
                    itemCount={logs.length}
                    itemSize={24}
                    width={'100%'}
                    style={{ height: '100%' }}
                  >
                    {({ index, style }) => {
                      const log = logs[index];
                      return (
                        <div style={{ ...style, padding: '0 16px', fontSize: '10px', color: 'var(--text-secondary)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <span style={{ color: 'var(--color-warning)', minWidth: '130px' }}>{new Date().toISOString().substring(11, 23)}</span>
                          <span style={{ color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.message}</span>
                        </div>
                      );
                    }}
                  </List>
                )}
              </div>
            </div>
          </div>

          <div className="bento-panel panel-b">
            <div className="bento-panel-header">
              <AlertTriangle size={16} color="var(--color-warning)"/> CRITICAL INCIDENT CORE
            </div>
            <div className="bento-panel-content palantir-mono" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
              {incidents.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '11px', gridColumn: '1 / -1', textAlign: 'center', padding: '20px' }}>
                  [ NO CRITICAL INCIDENTS DETECTED ]
                </div>
              ) : (
                [...incidents].sort((a, b) => {
                  const severityWeight = { critical: 3, warning: 2, info: 1, low: 0 };
                  return (severityWeight[b.severity] || 0) - (severityWeight[a.severity] || 0);
                }).map(inc => {
                  const isCritical = inc.severity === 'critical';
                  const borderColor = isCritical ? 'var(--color-critical)' : inc.severity === 'warning' ? 'var(--color-warning)' : 'var(--color-info)';
                  return (
                    <div key={inc.id} style={{
                      backgroundColor: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderLeft: `4px solid ${borderColor}`,
                      padding: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, color: borderColor, textTransform: 'uppercase' }}>{inc.severity}</span>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{inc.timestamp}</span>
                      </div>
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff', marginBottom: '2px' }}>{inc.title}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>TRAIN: {inc.train_number}</div>
                      </div>
                      {inc.reroute_plan && (
                        <div style={{ marginTop: '4px', paddingTop: '8px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>REROUTE PLAN DETECTED</span>
                          {inc.approved ? (
                            <span style={{ color: 'var(--color-resolved)', fontSize: '10px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                              <Check size={12} /> APPROVED
                            </span>
                          ) : (
                            <button
                              onClick={() => handleApprove(inc.id)}
                              style={{
                                backgroundColor: 'transparent',
                                color: 'var(--accent-color)',
                                border: '1px solid var(--accent-color)',
                                padding: '4px 8px',
                                fontSize: '10px',
                                fontWeight: 700,
                                cursor: 'pointer'
                              }}
                            >
                              APPROVE
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className="bento-panel panel-c">
            <div className="bento-panel-header">
              <RefreshCw size={16} color="var(--color-info)"/> MULTI-DEPARTMENT TASK SYNC
            </div>
            <div className="bento-panel-content palantir-mono" style={{ display: 'flex', gap: '16px', overflowX: 'auto', padding: '16px' }}>
              {['Maintenance', 'Operations', 'Station Manager'].map(dept => {
                const deptTasks = tasks.filter(t => {
                  if (dept === 'Station Manager') return t.department === 'station_manager';
                  return t.department?.toLowerCase() === dept.toLowerCase();
                });
                return (
                  <div key={dept} style={{ flex: 1, minWidth: '250px', backgroundColor: 'var(--bg-main)', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '8px', borderBottom: '1px solid var(--border-color)', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'center', backgroundColor: 'var(--bg-card)' }}>
                      {dept.toUpperCase()} ({deptTasks.length})
                    </div>
                    <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
                      {deptTasks.length === 0 ? (
                        <div style={{ color: 'var(--text-muted)', fontSize: '10px', textAlign: 'center', padding: '10px' }}>[ NO TASKS ]</div>
                      ) : (
                        deptTasks.map(t => {
                          const isResolved = t.status === 'resolved';
                          return (
                            <div key={t.id || t._id} style={{
                              backgroundColor: 'var(--bg-card)',
                              border: `1px solid ${isResolved ? 'var(--color-resolved)' : 'var(--border-color)'}`,
                              padding: '10px',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '8px',
                              opacity: isResolved ? 0.6 : 1
                            }}>
                              <div style={{ fontSize: '11px', color: '#fff' }}>{t.description}</div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{t.train_number || 'N/A'}</span>
                                {isResolved ? (
                                  <span style={{ color: 'var(--color-resolved)', fontSize: '9px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                                    <CheckCircle size={10} /> RESOLVED
                                  </span>
                                ) : (
                                  <button
                                    onClick={() => handleResolveTask(t.id || t._id)}
                                    style={{
                                      backgroundColor: 'transparent',
                                      color: 'var(--text-primary)',
                                      border: '1px solid var(--border-color)',
                                      padding: '4px 8px',
                                      fontSize: '9px',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    MARK RESOLVED
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bento-panel panel-d">
            <div className="bento-panel-header">
              <Activity size={16} color="var(--accent-color)"/> TELEMETRY OVERVIEW
            </div>
            <div className="bento-panel-content palantir-mono" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[
                { label: 'AGENT COGNITION STATUS', val: telemetry?.agent_loop_status?.toUpperCase() || 'RUNNING', color: 'var(--color-info)' },
                { label: 'RAILWAYS API LATENCY', val: `${telemetry?.railways_latency_ms || 0} ms`, color: 'var(--text-primary)' },
                { label: 'AI MODEL LATENCY', val: `${telemetry?.ai_latency_ms || 0} ms`, color: 'var(--text-primary)' },
                { label: 'ACTIVE WS CONNECTIONS', val: telemetry?.websocket_clients || 0, color: 'var(--color-warning)' },
                { label: 'DB INCIDENT COLLECTIONS', val: telemetry?.mongodb_incidents || 0, color: 'var(--text-secondary)' },
                { label: 'DB TASK COLLECTIONS', val: telemetry?.mongodb_tasks || 0, color: 'var(--text-secondary)' }
              ].map((metric, i) => (
                <div key={i} style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  padding: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{metric.label}</span>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: metric.color }}>{metric.val}</span>
                </div>
              ))}
            </div>
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
