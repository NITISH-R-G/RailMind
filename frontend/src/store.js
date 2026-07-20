import { create } from 'zustand';

const useStore = create((set) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  telemetry: null,
  wsStatus: 'disconnected',
  loopCount: 0,
  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents }),
  setTasks: (tasks) => set({ tasks }),
  setLogs: (logs) => set({ logs }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-200) })),
  addIncident: (incident) => set((state) => ({
    incidents: state.incidents.some(i => i.id === incident.id) ? state.incidents : [incident, ...state.incidents]
  })),
  setTelemetry: (telemetry) => set({ telemetry }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setLoopCount: (loopCount) => set({ loopCount }),
  updateTaskStatus: (taskId, status) => set((state) => ({
    tasks: state.tasks.map(t => t.id === taskId || t._id === taskId ? { ...t, status, urgency: status } : t)
  })),
  updateIncidentApproval: (incidentId, approved) => set((state) => ({
    incidents: state.incidents.map(i => i.id === incidentId ? { ...i, approved } : i)
  })),
  removeIncident: (incidentId) => set((state) => ({
    incidents: state.incidents.filter(i => i.id !== incidentId)
  }))
}));

export default useStore;
