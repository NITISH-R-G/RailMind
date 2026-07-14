import { create } from 'zustand';

const useStore = create((set, get) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  telemetry: {},
  loopCount: 0,
  incidentCount: 0,
  wsStatus: 'reconnecting',

  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents, incidentCount: incidents.length }),
  setTasks: (tasks) => set({ tasks }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-200) })), // Keep last 200 logs
  setTelemetry: (telemetry) => set({ telemetry }),
  setLoopCount: (loopCount) => set({ loopCount }),
  setWsStatus: (wsStatus) => set({ wsStatus }),

  // Handlers for specific updates
  addIncident: (incident) => set((state) => {
    if (state.incidents.some((inc) => inc.id === incident.id)) return state;
    const newIncidents = [incident, ...state.incidents];
    return { incidents: newIncidents, incidentCount: newIncidents.length };
  }),

  approveIncident: (incidentId) => set((state) => ({
    incidents: state.incidents.map((inc) =>
      inc.id === incidentId ? { ...inc, approved: true } : inc
    )
  })),

  acknowledgeIncident: (incidentId) => set((state) => {
    const newIncidents = state.incidents.filter((inc) => inc.id !== incidentId);
    return { incidents: newIncidents, incidentCount: newIncidents.length };
  }),

  resolveTask: (taskId) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t._id === taskId || t.id === taskId ? { ...t, status: 'resolved', urgency: 'resolved' } : t
    )
  })),
}));

export default useStore;
