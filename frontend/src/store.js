import { create } from 'zustand';

const getApiBase = () => {
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://localhost:8000';
};

const useStore = create((set, get) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  telemetry: null,
  wsStatus: 'reconnecting',
  loopCount: 0,
  incidentCount: 0,

  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents, incidentCount: incidents.length }),
  setTasks: (tasks) => set({ tasks }),
  setLogs: (logs) => set({ logs }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setTelemetry: (telemetry) => set({ telemetry }),

  fetchIncidents: async () => {
    try {
      const API_BASE = getApiBase();
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
        set({ incidents: formatted, incidentCount: formatted.length });
      }
    } catch (err) {
      console.error("[API] Failed to fetch incidents:", err);
    }
  },

  fetchTrains: async () => {
    try {
      const API_BASE = getApiBase();
      const res = await fetch(`${API_BASE}/api/trains`);
      if (res.ok) {
        const data = await res.json();
        set({ trains: data });
      }
    } catch (err) {
      console.error("[API] Failed to fetch trains:", err);
    }
  },

  fetchTasks: async () => {
    try {
      const API_BASE = getApiBase();
      const res = await fetch(`${API_BASE}/api/dept-tasks`);
      if (res.ok) {
        const data = await res.json();
        set({ tasks: data });
      }
    } catch (err) {
      console.error("[API] Failed to fetch department tasks:", err);
    }
  },

  fetchTelemetry: async () => {
    try {
      const API_BASE = getApiBase();
      const res = await fetch(`${API_BASE}/api/telemetry`);
      if (res.ok) {
        const data = await res.json();
        set({ telemetry: data });
      }
    } catch (err) {
      console.error("Failed to fetch telemetry:", err);
    }
  },

  connectWS: () => {
    if (typeof window === 'undefined') return null;
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    console.log("[WEBSOCKET] Connecting to:", wsUrl);
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("[WEBSOCKET] Connected to RailMind WebSocket server");
      set({ wsStatus: 'connected' });
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

          set(state => {
            if (state.incidents.some(inc => inc.id === newIncident.id)) return state;
            return {
              incidents: [newIncident, ...state.incidents],
              incidentCount: state.incidentCount + 1,
              loopCount: report.loop_count !== undefined ? report.loop_count : state.loopCount
            };
          });

          get().fetchTasks();
          get().fetchTrains();
        } else if (payload.type === 'AGENT_LOG') {
          set(state => ({ logs: [...state.logs, payload].slice(-200) }));
        }
      } catch (err) {
        console.error("[WEBSOCKET] Error parsing socket data:", err);
      }
    };

    socket.onclose = () => {
      console.log("[WEBSOCKET] Closed. Reconnecting in 3 seconds...");
      set({ wsStatus: 'reconnecting' });
      setTimeout(() => get().connectWS(), 3000);
    };

    socket.onerror = (err) => {
      console.error("[WEBSOCKET] Error encountered:", err);
      socket.close();
    };

    return socket;
  },

  handleApprove: async (incidentId, adminPassword) => {
    try {
      const API_BASE = getApiBase();
      const headers = new Headers();
      headers.set('Authorization', 'Basic ' + btoa('admin:' + adminPassword));
      const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/approve`, {
        method: 'POST',
        headers: headers
      });
      if (res.ok) {
        set(state => ({
          incidents: state.incidents.map(inc =>
            inc.id === incidentId ? { ...inc, approved: true } : inc
          )
        }));
        return true;
      } else if (res.status === 401) {
        alert("Incorrect admin password.");
        console.error("Unauthorized: Incorrect admin password.");
        return false;
      } else {
        console.error("Failed to approve incident reroute plan on backend");
        return false;
      }
    } catch (err) {
      console.error("Error approving reroute plan:", err);
      return false;
    }
  },

  handleAcknowledge: (incidentId) => {
    set(state => ({
      incidents: state.incidents.filter(inc => inc.id !== incidentId),
      incidentCount: Math.max(0, state.incidentCount - 1)
    }));
  },

  handleResolve: async (taskId) => {
    try {
      const API_BASE = getApiBase();
      const res = await fetch(`${API_BASE}/api/dept-tasks/${taskId}/resolve`, {
        method: 'POST'
      });
      if (res.ok) {
        set(state => ({
          tasks: state.tasks.map(t =>
            (t._id === taskId || t.id === taskId) ? { ...t, status: 'resolved', urgency: 'resolved' } : t
          )
        }));
      } else {
        console.error("Failed to mark task resolved on API server");
      }
    } catch (err) {
      console.error("Error sending resolution request:", err);
    }
  }

}));

export default useStore;
