import React, { useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import DashboardGrid from './components/Dashboard/DashboardGrid';
import { useStore } from './store';

function MainApp() {
  const fetchInitialData = useStore(state => state.fetchInitialData);
  const setWsStatus = useStore(state => state.setWsStatus);
  const updateTelemetry = useStore(state => state.updateTelemetry);
  const wsStatus = useStore(state => state.wsStatus);
  const socketRef = useRef(null);

  useEffect(() => {
    fetchInitialData();

    // Setup WS connection
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    let socket;
    let reconnectTimeout;

    const connectWS = () => {
      useStore.getState().addLog(`[AGENT_LOG] Initiating WebSocket connection to ${wsUrl}`);
      socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setWsStatus('connected');
        useStore.getState().addLog(`[AGENT_LOG] SUCCESS: Connected to RailMind Backend`);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          useStore.getState().addLog(`[AGENT_LOG] INGESTION: Received payload type ${payload.type}`);
          
          if (payload.type === 'HEARTBEAT' || payload.type === 'AGENT_LOG') {
            if (payload.data && payload.data.message) {
              useStore.getState().addLog(`[AGENT_LOG] ${payload.data.message}`);
            }
          }

          if (payload.type === 'INCIDENT_UPDATE' || payload.type === 'DEPARTMENT_TASK' || payload.type === 'TRAIN_UPDATE') {
             fetchInitialData();
          }

        } catch (err) {
          useStore.getState().addLog(`[AGENT_LOG] ERROR: Failed to parse WS message: ${err.message}`);
        }
      };

      socket.onclose = () => {
        setWsStatus('reconnecting');
        useStore.getState().addLog(`[AGENT_LOG] WARN: WebSocket disconnected. Attempting reconnect in 3s...`);
        reconnectTimeout = setTimeout(connectWS, 3000);
      };

      socket.onerror = (err) => {
        setWsStatus('error');
        useStore.getState().addLog(`[AGENT_LOG] CRITICAL: WebSocket encountered an error.`);
      };
    };

    connectWS();

    // Mock cycle countdown loop
    const cycleInterval = setInterval(() => {
      useStore.setState(state => {
        let nextCount = state.telemetry.cycleCountdown - 1;
        let loopCount = state.telemetry.loopCount;
        if (nextCount <= 0) {
          nextCount = 30;
          loopCount += 1;
          // Avoid triggering actions that call setState inside a state updater function.
          setTimeout(() => useStore.getState().addLog(`[AGENT_LOG] SYSTEM: Initiating cognitive cycle #${loopCount}`), 0);
        }
        return { telemetry: { ...state.telemetry, cycleCountdown: nextCount, loopCount } };
      });
    }, 1000);

    // Mock telemetry updates
    const telemetryInterval = setInterval(() => {
      updateTelemetry({
        workerMetrics: {
          cpu: 40 + Math.floor(Math.random() * 20),
          memory: 60 + Math.floor(Math.random() * 15),
          latency: 100 + Math.floor(Math.random() * 150),
          queueDepth: Math.floor(Math.random() * 30)
        }
      });
    }, 2000);

    return () => {
      clearInterval(cycleInterval);
      clearInterval(telemetryInterval);
      if (socketRef.current) socketRef.current.close();
      clearTimeout(reconnectTimeout);
    };
  }, [fetchInitialData, setWsStatus, updateTelemetry]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: 'var(--bg-main)',
      overflow: 'hidden'
    }}>
      <TopBar activeTab={'Rail Network'} />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar activeTab={'Dashboard'} />
        <DashboardGrid />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <MainApp />
  );
}
