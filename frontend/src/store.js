import { create } from 'zustand';

const API_BASE = `http://${window.location.hostname}:8000`;

export const useStore = create((set, get) => ({
  activeTab: 'Dashboard',
  setActiveTab: (tab) => set({ activeTab: tab }),

  loopCount: 0,
  setLoopCount: (count) => set({ loopCount: count }),

  incidentCount: 0,
  setIncidentCount: (count) => set({ incidentCount: count }),

  incidents: [],
  setIncidents: (incidents) => set({ incidents }),

  tasks: [],
  setTasks: (tasks) => set({ tasks }),

  trains: [],
  setTrains: (trains) => set({ trains }),

  wsStatus: 'reconnecting',
  setWsStatus: (status) => set({ wsStatus: status }),

  logs: [],
  setLogs: (logs) => set({ logs }),

  telemetry: null,
  setTelemetry: (telemetry) => set({ telemetry }),

  // Modal States
  showSettings: false,
  setShowSettings: (show) => set({ showSettings: show }),

  showNotifications: false,
  setShowNotifications: (show) => set({ showNotifications: show }),

  showProfile: false,
  setShowProfile: (show) => set({ showProfile: show }),

  // Fetch functions
  fetchIncidents: async () => {
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
        set({ incidents: formatted, incidentCount: formatted.length });
      }
    } catch (err) {
      console.error("[API] Failed to fetch incidents:", err);
    }
  },

  fetchTrains: async () => {
    try {
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
      const res = await fetch(`${API_BASE}/api/telemetry`);
      if (res.ok) {
        const data = await res.json();
        set({ telemetry: data });
      }
    } catch (err) {
      console.error("Failed to fetch telemetry:", err);
    }
  },

  // Handlers
  handleApprove: async (incidentId) => {
    console.log(`Approving reroute plan for incident: ${incidentId}`);
    const adminPassword = window.prompt("Enter Admin Password to approve this reroute plan:");
    if (adminPassword === null) {
      return; // User cancelled
    }
    try {
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
      } else if (res.status === 401) {
        alert("Incorrect admin password.");
        console.error("Unauthorized: Incorrect admin password.");
      } else {
        console.error("Failed to approve incident reroute plan on backend");
      }
    } catch (err) {
      console.error("Error approving reroute plan:", err);
    }
  },

  handleAcknowledge: (incidentId) => {
    console.log(`Acknowledging warning incident: ${incidentId}`);
    set(state => {
      const updatedIncidents = state.incidents.filter(inc => inc.id !== incidentId);
      return {
        incidents: updatedIncidents,
        incidentCount: Math.max(0, state.incidentCount - 1)
      };
    });
  },

  handleResolve: async (taskId) => {
    console.log(`Resolving department task: ${taskId}`);
    try {
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
