import { create } from 'zustand';

const useStore = create((set, get) => ({
  trains: [],
  incidents: [],
  tasks: [],
  logs: [],
  telemetry: {},

  setTrains: (trains) => set({ trains }),
  setIncidents: (incidents) => set({ incidents }),
  setTasks: (tasks) => set({ tasks }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log].slice(-200) })), // Keep last 200 logs
  setTelemetry: (telemetry) => set({ telemetry }),

  // Helpers to update individual items
  updateIncident: (id, updates) => set((state) => ({
    incidents: state.incidents.map((inc) => inc.id === id ? { ...inc, ...updates } : inc)
  })),
  removeIncident: (id) => set((state) => ({
    incidents: state.incidents.filter((inc) => inc.id !== id)
  })),
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map((t) => (t._id === id || t.id === id) ? { ...t, ...updates } : t)
  })),

  // Method to handle incoming incident stream
  addOrUpdateIncident: (newIncident) => set((state) => {
    const exists = state.incidents.some(inc => inc.id === newIncident.id);
    if (exists) {
      return {
        incidents: state.incidents.map(inc => inc.id === newIncident.id ? { ...inc, ...newIncident } : inc)
      };
    }
    return { incidents: [newIncident, ...state.incidents] };
  })
}));

export default useStore;
