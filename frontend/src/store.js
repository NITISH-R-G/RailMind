import { create } from 'zustand';

export const useStore = create((set) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  telemetry: null,
  loopCount: 0,
  incidentCount: 0,
  wsStatus: 'reconnecting',

  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents, incidentCount: incidents.length }),
  addIncident: (incident) => set((state) => {
    if (state.incidents.some(inc => inc.id === incident.id)) return state;
    return {
      incidents: [incident, ...state.incidents],
      incidentCount: state.incidentCount + 1
    };
  }),
  setTasks: (tasks) => set({ tasks }),
  addLog: (log) => set((state) => ({
    logs: [...state.logs, log].slice(-200) // Keep last 200 logs
  })),
  clearLogs: () => set({ logs: [] }),
  setTelemetry: (telemetry) => set({ telemetry }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setLoopCount: (loopCount) => set({ loopCount }),

  updateIncidentApproved: (incidentId) => set((state) => ({
    incidents: state.incidents.map(inc => inc.id === incidentId ? { ...inc, approved: true } : inc)
  })),
  removeIncident: (incidentId) => set((state) => ({
    incidents: state.incidents.filter(inc => inc.id !== incidentId),
    incidentCount: Math.max(0, state.incidentCount - 1)
  })),
  resolveTask: (taskId) => set((state) => ({
    tasks: state.tasks.map(t => (t._id === taskId || t.id === taskId) ? { ...t, status: 'resolved', urgency: 'resolved' } : t)
  }))
}));
