import { create } from 'zustand';

const useStore = create((set) => ({
  activeTab: 'Dashboard',
  loopCount: 0,
  incidentCount: 0,
  incidents: [],
  tasks: [],
  trains: [],
  wsStatus: 'reconnecting',
  logs: [],
  telemetry: null,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setLoopCount: (count) => set({ loopCount: count }),
  setIncidentCount: (count) => set({ incidentCount: count }),
  setIncidents: (incidents) => set({ incidents }),
  addIncident: (newIncident) => set((state) => {
    if (state.incidents.some((inc) => inc.id === newIncident.id)) return state;
    return {
      incidents: [newIncident, ...state.incidents],
      incidentCount: state.incidentCount + 1,
    };
  }),
  updateIncident: (id, updates) => set((state) => ({
    incidents: state.incidents.map((inc) =>
      inc.id === id ? { ...inc, ...updates } : inc
    ),
  })),
  removeIncident: (id) => set((state) => ({
    incidents: state.incidents.filter((inc) => inc.id !== id),
    incidentCount: Math.max(0, state.incidentCount - 1),
  })),
  setTasks: (tasks) => set({ tasks }),
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t._id === id || t.id === id ? { ...t, ...updates } : t
    ),
  })),
  setTrains: (trains) => set({ trains }),
  setWsStatus: (status) => set({ wsStatus: status }),
  addLog: (log) => set((state) => ({
    logs: [...state.logs, log].slice(-1000) // Keep more logs for virtual list
  })),
  clearLogs: () => set({ logs: [] }),
  setTelemetry: (telemetry) => set({ telemetry }),
}));

export default useStore;
