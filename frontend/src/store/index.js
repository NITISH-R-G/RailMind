import { create } from 'zustand';

export const useStore = create((set, get) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  wsStatus: 'reconnecting',
  telemetry: {
    loopCount: 0,
    cycleCountdown: 30,
    workerMetrics: {
      cpu: 45,
      memory: 62,
      latency: 120,
      queueDepth: 14
    }
  },

  setWsStatus: (status) => set({ wsStatus: status }),
  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents }),
  setTasks: (tasks) => set({ tasks }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-1000) })), // Keep last 1000 logs
  updateTelemetry: (updates) => set((state) => ({ telemetry: { ...state.telemetry, ...updates } })),

  // Actions
  fetchInitialData: async () => {
    const API_BASE = `http://${window.location.hostname}:8000`;
    try {
      const [trainsRes, incidentsRes, tasksRes] = await Promise.all([
        fetch(`${API_BASE}/api/trains`),
        fetch(`${API_BASE}/api/incidents`),
        fetch(`${API_BASE}/api/dept-tasks`)
      ]);

      if (trainsRes.ok) {
        const data = await trainsRes.json();
        set({ trains: data });
      }

      if (incidentsRes.ok) {
        const data = await incidentsRes.json();
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
        set({ incidents: formatted });
      }

      if (tasksRes.ok) {
        const data = await tasksRes.json();
        set({ tasks: data });
      }
    } catch (error) {
      console.error("[STORE] Failed to fetch initial data:", error);
    }
  }
}));
