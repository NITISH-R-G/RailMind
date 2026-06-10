/* eslint-disable */
import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import LiveMap from './components/LiveMap';
import IncidentFeed from './components/IncidentFeed';
import TaskBoard from './components/TaskBoard';
import { ShieldAlert, AlertTriangle, Info, Check, CornerDownRight, Terminal, RefreshCw, X, Shield, User, HelpCircle, Activity, Bell, Settings } from 'lucide-react';

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
          backgroundColor: '#0b0d10',
          color: '#ef4444',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'system-ui, sans-serif',
          gap: '16px'
        }}>
          <h2 style={{ fontWeight: 600 }}>RailMind Dashboard encountered an error</h2>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>Please reload or contact support if the issue persists.</p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
          >
            Reload Dashboard
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainApp() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [loopCount, setLoopCount] = useState(0);
  const [incidentCount, setIncidentCount] = useState(0);
  const [incidents, setIncidents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [trains, setTrains] = useState([]);
  const [wsStatus, setWsStatus] = useState('reconnecting');
  const [logs, setLogs] = useState([]);
  
  // Modal Overlay States
  const [showSettings, setShowSettings] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const socketRef = useRef(null);
  const API_BASE = `http://${window.location.hostname}:8000`;

  // Fetch functions
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
        setIncidentCount(formatted.length);
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

  useEffect(() => {
    fetchIncidents();
    fetchTrains();
    fetchTasks();

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

            setIncidents(prev => {
              if (prev.some(inc => inc.id === newIncident.id)) return prev;
              return [newIncident, ...prev];
            });
            setIncidentCount(prev => prev + 1);
            if (report.loop_count !== undefined) {
              setLoopCount(report.loop_count);
            }

            fetchTasks();
            fetchTrains();
          } else if (payload.type === 'AGENT_LOG') {
            setLogs(prev => [...prev, payload].slice(-200)); // Keep last 200 logs
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
    };
  }, []);

  const handleApprove = async (incidentId) => {
    console.log(`Approving reroute plan for incident: ${incidentId}`);
    try {
      const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/approve`, {
        method: 'POST'
      });
      if (res.ok) {
        setIncidents(prev => prev.map(inc => {
          if (inc.id === incidentId) {
            return { ...inc, approved: true };
          }
          return inc;
        }));
      } else {
        console.error("Failed to approve incident reroute plan on backend");
      }
    } catch (err) {
      console.error("Error approving reroute plan:", err);
    }
  };

  const handleAcknowledge = (incidentId) => {
    console.log(`Acknowledging warning incident: ${incidentId}`);
    setIncidents(prev => prev.filter(inc => inc.id !== incidentId));
    setIncidentCount(prev => Math.max(0, prev - 1));
  };

  const handleResolve = async (taskId) => {
    console.log(`Resolving department task: ${taskId}`);
    try {
      const res = await fetch(`${API_BASE}/api/dept-tasks/${taskId}/resolve`, {
        method: 'POST'
      });
      if (res.ok) {
        setTasks(prev => prev.map(t => {
          if (t._id === taskId || t.id === taskId) {
            return { ...t, status: 'resolved', urgency: 'resolved' };
          }
          return t;
        }));
      } else {
        console.error("Failed to mark task resolved on API server");
      }
    } catch (err) {
      console.error("Error sending resolution request:", err);
    }
  };

  // Views Render Functions
  const IncidentFeedView = () => {
    const [filter, setFilter] = useState('ALL');
    const [expandedIncident, setExpandedIncident] = useState(null);

    const filteredIncidents = incidents.filter(inc => {
      if (filter === 'ALL') return true;
      return inc.severity?.toUpperCase() === filter;
    });

    return (
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>Active Incident Center</h2>
            <p style={{ fontSize: '13px', color: '#64748b' }}>Operations command center feeds</p>
          </div>
          {/* Filters */}
          <div style={{ display: 'flex', gap: '8px', backgroundColor: '#11141a', padding: '4px', borderRadius: '6px', border: '1px solid #1a1e26' }}>
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: filter === f ? '#3b82f6' : 'transparent',
                  color: filter === f ? '#fff' : '#94a3b8',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
          {filteredIncidents.length === 0 ? (
            <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: '#64748b', backgroundColor: '#11141a', borderRadius: '8px', border: '1px dashed #1a1e26' }}>
              No active incidents matching selection.
            </div>
          ) : (
            filteredIncidents.map(inc => {
              const isCritical = inc.severity === 'critical';
              const isWarning = inc.severity === 'warning';
              const borderColor = isCritical ? '#ef4444' : isWarning ? '#f59e0b' : '#3b82f6';

              return (
                <div key={inc.id} style={{
                  backgroundColor: '#161920',
                  border: '1px solid #1a1e26',
                  borderLeft: `4px solid ${borderColor}`,
                  borderRadius: '6px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontSize: '9px',
                      fontWeight: 700,
                      color: borderColor,
                      backgroundColor: `${borderColor}15`,
                      padding: '3px 8px',
                      borderRadius: '3px',
                      textTransform: 'uppercase'
                    }}>{inc.severity}</span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{inc.timestamp}</span>
                  </div>

                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>{inc.title}</h3>
                    <p style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '4px' }}>Train: {inc.train_number}</p>
                  </div>

                  {inc.reroute_plan && (
                    <div style={{
                      backgroundColor: 'rgba(59, 130, 246, 0.05)',
                      border: '1px dashed rgba(59, 130, 246, 0.2)',
                      padding: '10px',
                      borderRadius: '4px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', color: '#94a3b8', fontWeight: 600 }}>
                        <CornerDownRight size={12} style={{ color: '#3b82f6' }} />
                        REROUTE PLAN
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{inc.reroute_plan}</span>
                        {inc.approved ? (
                          <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
                            <Check size={12} /> APPROVED ✓
                          </span>
                        ) : (
                          <button
                            onClick={() => handleApprove(inc.id)}
                            style={{
                              backgroundColor: '#3b82f6',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '4px 10px',
                              fontSize: '10px',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            APPROVE
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  <div style={{ borderTop: '1px solid #1a1e26', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      Notified: {inc.departments.join(', ') || 'None'}
                    </span>
                    <button
                      onClick={() => setExpandedIncident(expandedIncident === inc.id ? null : inc.id)}
                      style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#3b82f6',
                        fontSize: '11px',
                        cursor: 'pointer',
                        fontWeight: 600
                      }}
                    >
                      {expandedIncident === inc.id ? 'Hide reasoning ▲' : 'Show reasoning ▼'}
                    </button>
                  </div>

                  {expandedIncident === inc.id && (
                    <div style={{
                      backgroundColor: '#0a0c10',
                      border: '1px solid #1a1e26',
                      padding: '12px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: '#94a3b8',
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      marginTop: '4px'
                    }}>
                      {inc.title}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  const AnalyticsView = () => {
    const criticalCount = incidents.filter(i => i.severity === 'critical').length;
    const warningCount = incidents.filter(i => i.severity === 'warning').length;
    const infoCount = incidents.filter(i => i.severity === 'info').length;
    const totalCount = incidents.length;

    const maxCount = Math.max(criticalCount, warningCount, infoCount, 1);

    return (
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>System Operations Analytics</h2>
          <p style={{ fontSize: '13px', color: '#64748b' }}>Historical metrics & loops telemetry</p>
        </div>

        {/* Stats Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {[
            { label: 'TOTAL INCIDENTS', val: totalCount, color: '#3b82f6' },
            { label: 'CRITICAL ALERTS', val: criticalCount, color: '#ef4444' },
            { label: 'AGENT LOOP COUNT', val: loopCount, color: '#10b981' },
            { label: 'AVG RESPONSE TIME', val: '4.2 min', color: '#a5b4fc' }
          ].map((stat, idx) => (
            <div key={idx} style={{
              backgroundColor: '#11141a',
              border: '1px solid #1a1e26',
              borderRadius: '6px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <span style={{ fontSize: '10px', fontWeight: 600, color: '#64748b', letterSpacing: '0.5px' }}>{stat.label}</span>
              <span style={{ fontSize: '28px', fontWeight: 700, color: stat.color }}>{stat.val}</span>
            </div>
          ))}
        </div>

        {/* Charts and Data Representation */}
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          {/* Custom SVG Bar Chart */}
          <div style={{
            flex: 1,
            minWidth: '340px',
            backgroundColor: '#11141a',
            border: '1px solid #1a1e26',
            borderRadius: '6px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>INCIDENTS BY SEVERITY</h3>
            <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'flex-end', height: '180px', paddingTop: '20px' }}>
              {[
                { name: 'Critical', count: criticalCount, color: '#ef4444' },
                { name: 'Warning', count: warningCount, color: '#f59e0b' },
                { name: 'Info', count: infoCount, color: '#3b82f6' }
              ].map((bar, idx) => {
                const heightPercent = (bar.count / maxCount) * 140; // max height 140px
                return (
                  <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', width: '60px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>{bar.count}</span>
                    <div style={{
                      width: '32px',
                      height: `${Math.max(heightPercent, 6)}px`,
                      backgroundColor: bar.color,
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.5s ease-out'
                    }}></div>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{bar.name}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{
            flex: 1,
            minWidth: '340px',
            backgroundColor: '#11141a',
            border: '1px solid #1a1e26',
            borderRadius: '6px',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>SYSTEM STATUS REPORT</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px', color: '#cbd5e1', marginTop: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1a1e26', paddingBottom: '6px' }}>
                <span>Operations Agent State</span>
                <span style={{ color: '#10b981', fontWeight: 600 }}>NOMINAL</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1a1e26', paddingBottom: '6px' }}>
                <span>Primary API Client</span>
                <span style={{ color: '#ef4444' }}>API FALLBACK ACTIVE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #1a1e26', paddingBottom: '6px' }}>
                <span>Database Client</span>
                <span style={{ color: '#ef4444' }}>JSON FALLBACK ACTIVE</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px' }}>
                <span>SMS Alert Dispatcher</span>
                <span style={{ color: '#3b82f6' }}>MOCK MODE active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const SupportView = () => {
    return (
      <div style={{ padding: '40px', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px', color: '#e2e8f0', textAlign: 'center' }}>
        <div style={{
          backgroundColor: '#11141a',
          border: '1px solid #1a1e26',
          borderRadius: '8px',
          padding: '40px 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '16px',
          maxWidth: '560px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)'
        }}>
          <ShieldAlert size={48} style={{ color: '#3b82f6' }} />
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc' }}>RailMind Support Portal</h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: '1.6' }}>
            RailMind v1.0 — Autonomous Railway Operations Agent.<br />
            Built for FAR AWAY 2026.
          </p>
          <div style={{ width: '100%', height: '1px', backgroundColor: '#1a1e26', margin: '10px 0' }}></div>
          <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 500, letterSpacing: '0.5px' }}>
            AUTHORIZED OPERATIONS PERSONNEL ONLY • SECURE SESSION SEC-402
          </span>
        </div>
      </div>
    );
  };

  const LogsView = ({ logs = [], onClear }) => {
    const logEndRef = useRef(null);

    useEffect(() => {
      if (logEndRef.current) {
        logEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    }, [logs]);

    return (
      <div style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={20} style={{ color: '#10b981' }} />
              Agent Live Operations Logs
            </h2>
            <p style={{ fontSize: '13px', color: '#64748b' }}>Real-time streaming agent steps and diagnostics</p>
          </div>
          <button
            onClick={onClear}
            style={{
              padding: '6px 12px',
              backgroundColor: 'transparent',
              border: '1px solid #334155',
              borderRadius: '4px',
              color: '#94a3b8',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.backgroundColor = '#1e293b'}
            onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            Clear logs
          </button>
        </div>

        <div style={{
          flex: 1,
          backgroundColor: '#05070a',
          border: '1px solid #1a1e26',
          borderRadius: '6px',
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          fontFamily: 'monospace',
          fontSize: '12px',
          color: '#34d399',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.6)'
        }}>
          {logs.length === 0 ? (
            <div style={{ color: '#64748b', fontStyle: 'italic' }}>
              [SYSTEM] Awaiting live logs from operations agent stream...
            </div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} style={{ lineBreak: 'anywhere' }}>
                <span style={{ color: '#60a5fa' }}>{log.message.substring(0, 21)}</span>
                <span style={{ color: '#c084fc' }}>{log.message.substring(21, 35)}</span>
                <span>{log.message.substring(35)}</span>
              </div>
            ))
          )}
          <div ref={logEndRef}></div>
        </div>
      </div>
    );
  };

  const TelemetryView = () => {
    const [telemetry, setTelemetry] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchTelemetry = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/telemetry`);
        if (res.ok) {
          const data = await res.json();
          setTelemetry(data);
        }
      } catch (err) {
        console.error("Failed to fetch telemetry:", err);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      fetchTelemetry();
      const interval = setInterval(fetchTelemetry, 5000);
      return () => clearInterval(interval);
    }, []);

    if (loading && !telemetry) {
      return <div style={{ padding: '24px', color: '#94a3b8' }}>Loading telemetry...</div>;
    }

    const metrics = [
      { name: 'Agent Loop Status', value: telemetry?.agent_loop_status?.toUpperCase() || 'RUNNING', color: '#10b981' },
      { name: 'Last API Call', value: telemetry?.last_api_call || 'Never', color: '#a5b4fc' },
      { name: 'Railways API Latency', value: `${telemetry?.railways_latency_ms || 0} ms`, color: '#3b82f6' },
      { name: 'AI Reasoner Latency', value: `${telemetry?.ai_latency_ms || 0} ms`, color: '#c084fc' },
      { name: 'WebSocket Clients', value: telemetry?.websocket_clients || 0, color: '#f59e0b' },
      { name: 'MongoDB Incident Count', value: telemetry?.mongodb_incidents || 0, color: '#ef4444' },
      { name: 'MongoDB Task Count', value: telemetry?.mongodb_tasks || 0, color: '#ec4899' },
    ];

    return (
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>System Telemetry</h2>
          <p style={{ fontSize: '13px', color: '#64748b' }}>Real-time operations timing and statistics</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '16px' }}>
          {metrics.map((m, idx) => (
            <div key={idx} style={{
              backgroundColor: '#11141a',
              border: '1px solid #1a1e26',
              borderRadius: '8px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <span style={{ fontSize: '12px', fontWeight: 500, color: '#94a3b8' }}>{m.name}</span>
              <span style={{ fontSize: '24px', fontWeight: 700, color: m.color, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={m.value}>{m.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const SchedulesView = () => {
    const [scheduleTrains, setScheduleTrains] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchSchedules = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/trains`);
        if (res.ok) {
          const data = await res.json();
          setScheduleTrains(data);
        }
      } catch (err) {
        console.error("Failed to fetch schedules:", err);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      fetchSchedules();
      const interval = setInterval(fetchSchedules, 30000);
      return () => clearInterval(interval);
    }, []);

    if (loading && scheduleTrains.length === 0) {
      return <div style={{ padding: '24px', color: '#94a3b8' }}>Loading schedules...</div>;
    }

    return (
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>Active Train Schedules</h2>
          <p style={{ fontSize: '13px', color: '#64748b' }}>Monitored express and passenger corridors (Auto-refresh every 30s)</p>
        </div>

        <div style={{
          backgroundColor: '#11141a',
          border: '1px solid #1a1e26',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#161920', borderBottom: '1px solid #1a1e26', color: '#94a3b8' }}>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Train No</th>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Train Name</th>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Route</th>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Last Delay</th>
                <th style={{ padding: '14px 16px', fontWeight: 600 }}>Current Station</th>
              </tr>
            </thead>
            <tbody>
              {scheduleTrains.map((train, idx) => {
                const isDelayed = train.delay_minutes > 0;
                const statusColor = train.status === 'cancelled' ? '#ef4444' : isDelayed ? '#f59e0b' : '#10b981';
                return (
                  <tr key={idx} style={{
                    borderBottom: '1px solid #161920',
                    color: '#cbd5e1',
                    backgroundColor: idx % 2 === 0 ? '#11141a' : '#14171f'
                  }}>
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: '#3b82f6' }}>{train.train_number}</td>
                    <td style={{ padding: '12px 16px' }}>{train.train_name}</td>
                    <td style={{ padding: '12px 16px' }}>{train.source || 'NDLS'} → {train.destination || 'RKMP'}</td>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: statusColor }}>
                      {train.status?.toUpperCase() || 'UNKNOWN'}
                    </td>
                    <td style={{ padding: '12px 16px', color: isDelayed ? '#f59e0b' : '#64748b' }}>
                      {isDelayed ? `${train.delay_minutes} mins` : 'None'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8' }}>{train.current_station || 'N/A'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const AssetsView = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/system-status`);
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
        }
      } catch (err) {
        console.error("Failed to fetch system status:", err);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      fetchStatus();
    }, []);

    if (loading && !status) {
      return <div style={{ padding: '24px', color: '#94a3b8' }}>Loading system assets...</div>;
    }

    const services = [
      { name: 'Agent Loop Status', status: status?.agent_status || 'ACTIVE', isConnected: true },
      { name: 'Reasoning Model', status: status?.model || 'Gemini 2.0 Flash / Claude', isConnected: true },
      { name: 'Indian Railways API Feed', status: status?.railways_api || 'Disconnected', isConnected: status?.railways_api === 'Connected' },
      { name: 'Twilio SMS Alert System', status: status?.twilio_sms || 'Disconnected', isConnected: status?.twilio_sms === 'Connected' },
      { name: 'MongoDB Cloud Database', status: status?.mongodb || 'Disconnected', isConnected: status?.mongodb === 'Connected' }
    ];

    return (
      <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#f8fafc' }}>RailMind System Assets</h2>
          <p style={{ fontSize: '13px', color: '#64748b' }}>Operations connections status and departmental coordinates</p>
        </div>

        {/* Connection Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {services.map((s, idx) => (
            <div key={idx} style={{
              backgroundColor: '#11141a',
              border: '1px solid #1a1e26',
              borderRadius: '8px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>{s.name}</span>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: s.isConnected ? '#10b981' : '#ef4444',
                  boxShadow: s.isConnected ? '0 0 8px #10b981' : '0 0 8px #ef4444'
                }}></span>
              </div>
              <span style={{ fontSize: '15px', color: s.isConnected ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                {s.status}
              </span>
            </div>
          ))}
        </div>

        {/* Contacts Section */}
        <div style={{
          backgroundColor: '#11141a',
          border: '1px solid #1a1e26',
          borderRadius: '8px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>Departmental Contacts Registry</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>MAINTENANCE COMMAND</span>
              <span style={{ fontSize: '14px', color: '#cbd5e1', fontWeight: 500 }}>{status?.contacts?.maintenance || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>OPERATIONS CONTROL</span>
              <span style={{ fontSize: '14px', color: '#cbd5e1', fontWeight: 500 }}>{status?.contacts?.operations || 'N/A'}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>STATION MANAGERS FEED</span>
              <span style={{ fontSize: '14px', color: '#cbd5e1', fontWeight: 500 }}>{status?.contacts?.station_manager || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'Dashboard':
        return (
          <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              flex: 1,
              borderRight: '1px solid #1a1e26',
              backgroundColor: '#0b0d10'
            }}>
              <div style={{ flex: 1, position: 'relative' }}>
                <LiveMap trains={trains} />
              </div>
              <TaskBoard tasks={tasks} onResolve={handleResolve} />
            </div>
            <IncidentFeed 
              incidents={incidents} 
              onApprove={handleApprove}
              onAcknowledge={handleAcknowledge}
            />
          </div>
        );

      case 'Live Map':
        return (
          <div style={{ flex: 1, position: 'relative', height: '100%' }}>
            <LiveMap trains={trains} />
          </div>
        );

      case 'Incident Feed':
        return <IncidentFeedView />;

      case 'Task Board':
        return (
          <div style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <TaskBoard tasks={tasks} onResolve={handleResolve} fullScreen={true} />
          </div>
        );

      case 'Analytics':
        return <AnalyticsView />;

      case 'Support':
        return <SupportView />;

      case 'Logs':
        return <LogsView logs={logs} onClear={() => setLogs([])} />;

      case 'Telemetry':
        return <TelemetryView />;

      case 'Schedules':
        return <SchedulesView />;

      case 'Assets':
        return <AssetsView />;

      default:
        return <div style={{ padding: '24px' }}>Page not found</div>;
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: '#0b0d10',
      overflow: 'hidden'
    }}>
      <TopBar 
        loopCount={loopCount} 
        incidentCount={incidentCount} 
        wsStatus={wsStatus} 
        activeTab={activeTab}
        onTabChange={(tab) => {
          if (tab === 'Network') {
            setActiveTab('Dashboard');
          } else {
            setActiveTab(tab);
          }
        }}
        onSettingsClick={() => setShowSettings(true)}
        onNotificationsClick={() => setShowNotifications(true)}
        onProfileClick={() => setShowProfile(true)}
      />

      {wsStatus === 'reconnecting' && (
        <div style={{
          backgroundColor: '#ef4444',
          color: '#ffffff',
          textAlign: 'center',
          padding: '10px 24px',
          fontSize: '13px',
          fontWeight: 600,
          letterSpacing: '0.5px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          zIndex: 1000,
          borderBottom: '1px solid #b91c1c',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.3)'
        }}>
          <span style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            backgroundColor: '#ffffff',
            borderRadius: '50%',
            animation: 'pulse-live 1s infinite'
          }}></span>
          Agent offline — reconnecting...
        </div>
      )}

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        {renderContent()}
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0,0,0,0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            backgroundColor: '#11141a',
            border: '1px solid #1a1e26',
            borderRadius: '8px',
            padding: '24px',
            width: '420px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings size={18} style={{ color: '#3b82f6' }} />
                System Settings
              </h3>
              <button onClick={() => setShowSettings(false)} style={{ backgroundColor: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: '#cbd5e1' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input type="checkbox" defaultChecked /> Enable autonomous routing agent
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input type="checkbox" defaultChecked /> Fallback JSON database mode active
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input type="checkbox" defaultChecked /> WebSocket notifications active
              </label>
            </div>

            <button
              onClick={() => setShowSettings(false)}
              style={{
                marginTop: '10px',
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Save Configuration
            </button>
          </div>
        </div>
      )}

      {/* Notifications Modal */}
      {showNotifications && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0,0,0,0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            backgroundColor: '#11141a',
            border: '1px solid #1a1e26',
            borderRadius: '8px',
            padding: '24px',
            width: '420px',
            maxHeight: '400px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Bell size={18} style={{ color: '#ef4444' }} />
                Real-Time Alert Feed
              </h3>
              <button onClick={() => setShowNotifications(false)} style={{ backgroundColor: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
              {(() => {
                const len = Math.min(5, incidents.length);
                const elements = [];
                for (let i = 0; i < len; i++) {
                  const inc = incidents[i];
                  elements.push(
                    <div key={inc.id} style={{
                      backgroundColor: '#161920',
                      border: '1px solid #1a1e26',
                      padding: '10px 14px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      color: '#cbd5e1'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ color: '#ef4444', fontWeight: 600 }}>{inc.severity.toUpperCase()}</span>
                        <span style={{ color: '#64748b' }}>{inc.timestamp}</span>
                      </div>
                      {inc.title}
                    </div>
                  );
                }
                return elements;
              })()}
              {incidents.length === 0 && (
                <div style={{ color: '#64748b', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                  No notifications recorded.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Profile Modal */}
      {showProfile && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: 'rgba(0,0,0,0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            backgroundColor: '#11141a',
            border: '1px solid #1a1e26',
            borderRadius: '8px',
            padding: '28px',
            width: '380px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px',
            textAlign: 'center'
          }}>
            <div style={{ alignSelf: 'stretch', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowProfile(false)} style={{ backgroundColor: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              overflow: 'hidden',
              border: '2px solid #3b82f6',
              boxShadow: '0 0 15px rgba(59, 130, 246, 0.4)'
            }}>
              <img 
                src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" 
                alt="User profile" 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>

            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc' }}>Operator: Shreyam</h3>
              <p style={{ fontSize: '13px', color: '#3b82f6', fontWeight: 600 }}>Chief Operations Manager</p>
            </div>

            <div style={{ width: '100%', height: '1px', backgroundColor: '#1a1e26' }}></div>

            <div style={{ alignSelf: 'stretch', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Operations Terminal</span>
                <span>SECURE-NODE-ALPHA</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Authorization Level</span>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>LEVEL 5 (Full Command)</span>
              </div>
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
