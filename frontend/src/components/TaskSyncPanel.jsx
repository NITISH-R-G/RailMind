import React from 'react';
import { ClipboardList, CheckCircle2 } from 'lucide-react';
import useStore from '../store';

const TaskColumn = ({ title, tasks, onResolve }) => {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '180px' }}>
      <div className="palantir-mono" style={{ fontSize: '10px', fontWeight: 600, color: '#5c7080', borderBottom: '1px solid #26354A', paddingBottom: '4px' }}>
        {title} [{tasks.length}]
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
        {tasks.map(t => (
          <div key={t.id || t._id} style={{
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            padding: '8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span className="palantir-mono" style={{ fontSize: '10px', color: '#e2e8f0', fontWeight: 600, lineHeight: '1.2' }}>
                {t.task_description}
              </span>
              {t.status === 'resolved' ? (
                <CheckCircle2 size={12} color="#00FF66" />
              ) : (
                <button
                  onClick={() => onResolve(t.id || t._id)}
                  style={{
                    backgroundColor: 'transparent',
                    border: '1px solid #00FF66',
                    color: '#00FF66',
                    fontSize: '9px',
                    padding: '2px 6px',
                    cursor: 'pointer',
                    fontFamily: "'JetBrains Mono', monospace",
                    fontWeight: 600
                  }}
                >
                  RSLV
                </button>
              )}
            </div>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#8a9ba8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {t.action_required || t.detail || 'Pending...'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function TaskSyncPanel() {
  const tasks = useStore((state) => state.tasks);
  const resolveTask = useStore((state) => state.resolveTask);

  const handleResolve = async (taskId) => {
    resolveTask(taskId);
    try {
      const API_BASE = `http://${window.location.hostname}:8000`;
      await fetch(`${API_BASE}/api/dept-tasks/${taskId}/resolve`, { method: 'POST' });
    } catch (err) {
      console.error("Failed to resolve task on server:", err);
    }
  };

  const maintenanceTasks = tasks.filter(t => t.department?.toLowerCase() === 'maintenance');
  const operationsTasks = tasks.filter(t => t.department?.toLowerCase() === 'operations');
  const stationTasks = tasks.filter(t => t.department?.toLowerCase() === 'station_manager' || t.department?.toLowerCase() === 'station');

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#0A0E17',
      border: '1px solid #26354A',
    }}>
      <div style={{
        padding: '8px 12px',
        borderBottom: '1px solid #26354A',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        backgroundColor: '#161F30'
      }}>
        <ClipboardList size={14} color="#00FF66" />
        <span className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0' }}>TASK SYNCHRONIZATION</span>
      </div>

      <div style={{ flex: 1, padding: '12px', display: 'flex', gap: '16px', overflowX: 'auto' }}>
        <TaskColumn title="MAINTENANCE" tasks={maintenanceTasks} onResolve={handleResolve} />
        <TaskColumn title="OPERATIONS" tasks={operationsTasks} onResolve={handleResolve} />
        <TaskColumn title="STATION MGT" tasks={stationTasks} onResolve={handleResolve} />
      </div>
    </div>
  );
}
