import React from 'react';
import { useStore } from '../../store';

export default function TaskKanban() {
  const tasks = useStore((state) => state.tasks);

  const maintenanceTasks = tasks.filter(t => t.department?.toLowerCase() === 'maintenance');
  const operationsTasks = tasks.filter(t => t.department?.toLowerCase() === 'operations');
  const stationTasks = tasks.filter(t =>
    t.department?.toLowerCase() === 'station_manager' ||
    t.department?.toLowerCase() === 'station'
  );

  const Column = ({ title, colTasks }) => (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border-color)', padding: '8px' }}>
      <div className="tactical-mono" style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
        {title} [{colTasks.length}]
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto' }}>
        {colTasks.map((task, idx) => {
          const isResolved = task.status?.toLowerCase() === 'resolved' || task.urgency?.toLowerCase() === 'resolved';
          return (
            <div key={idx} style={{
              backgroundColor: 'var(--bg-main)',
              border: '1px solid var(--border-color)',
              padding: '8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
               <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                 <span className="tactical-mono" style={{ fontSize: '9px', color: isResolved ? 'var(--color-green)' : 'var(--color-amber)' }}>
                   {task.urgency?.toUpperCase() || 'NORMAL'}
                 </span>
                 <span className="tactical-mono" style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{task.id || task._id || idx}</span>
               </div>
               <span className="tactical-sans" style={{ fontSize: '11px', color: isResolved ? 'var(--text-muted)' : 'var(--text-primary)', textDecoration: isResolved ? 'line-through' : 'none' }}>
                 {task.task_description || task.description}
               </span>
               {!isResolved && (
                 <button className="tactical-mono" style={{
                   backgroundColor: 'var(--border-color)',
                   color: 'var(--text-primary)',
                   border: 'none',
                   padding: '4px',
                   fontSize: '9px',
                   marginTop: '4px',
                   cursor: 'pointer'
                 }}>
                   ACTION REQUIRED
                 </button>
               )}
            </div>
          )
        })}
      </div>
    </div>
  );

  return (
    <div className="bento-panel" style={{ height: '100%', gridArea: 'tasks' }}>
      <div className="bento-header">
        <span className="bento-title">Panel C // Multi-Department Sync</span>
      </div>
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Column title="Maintenance" colTasks={maintenanceTasks} />
        <Column title="Operations" colTasks={operationsTasks} />
        <Column title="Station" colTasks={stationTasks} />
      </div>
    </div>
  );
}
