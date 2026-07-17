import { create } from 'zustand';

export const useStore = create((set) => ({
  incidents: [],
  tasks: [],
  trains: [],
  logs: [],
  wsStatus: 'reconnecting',
  telemetry: null,
  activeTab: 'Dashboard',

  setIncidents: (incidents) => set({ incidents }),
  setTasks: (tasks) => set({ tasks }),
  setTrains: (trains) => set({ trains }),
  setLogs: (logs) => set({ logs }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-500) })), // Keep last 500
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setTelemetry: (telemetry) => set({ telemetry }),
  setActiveTab: (activeTab) => set({ activeTab }),

  addIncident: (incident) => set((state) => ({
    incidents: state.incidents.some(i => i.id === incident.id)
      ? state.incidents
      : [incident, ...state.incidents]
  })),

  updateIncidentApproved: (incidentId) => set((state) => ({
    incidents: state.incidents.map(inc =>
      inc.id === incidentId ? { ...inc, approved: true } : inc
    )
  })),

  resolveTask: (taskId) => set((state) => ({
    tasks: state.tasks.map(t =>
      (t._id === taskId || t.id === taskId) ? { ...t, status: 'resolved', urgency: 'resolved' } : t
    )
  })),

  removeIncident: (incidentId) => set((state) => ({
    incidents: state.incidents.filter(inc => inc.id !== incidentId)
  }))
}));
