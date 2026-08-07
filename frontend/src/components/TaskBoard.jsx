/* eslint-disable */
import React from 'react';
import { MoreHorizontal, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useStore } from '../store';

export default function TaskBoard({ tasks = [], onResolve, fullScreen = false, compact = false }) {
  // Use store if props are not explicitly provided
  const storeTasks = useStore(state => state.tasks);
  const storeResolve = useStore(state => state.handleResolve);

  const activeTasks = (tasks && tasks.length > 0) ? tasks : (storeTasks.length > 0 ? storeTasks : [
    {
      id: "task_001",
      department: "maintenance",
      task_description: "Engine Check - Train 402",
      urgency: "urgent",
      action_required: "DUE: 15:00",
      detail: "Anomaly detected in propulsion system. Immediate action required."
    },
    {
      id: "task_002",
      department: "operations",
      task_description: "Signal Calibration - Route 7",
      urgency: "medium",
      action_required: "ASSIGNED: ALPHA-9",
      detail: "Routine calibration needed for optimal traffic flow. No immediate impact."
    },
    {
      id: "task_003",
      department: "station_manager",
      task_description: "Platform 4 Clearance",
      urgency: "resolved",
      action_required: "COMPLETED 10:55",
      detail: "Passenger crowd dissipated, platform cleared for next service."
    }
  ]);

  const resolveHandler = onResolve || storeResolve;

  const maintenanceTasks = activeTasks.filter(t => t.department?.toLowerCase() === 'maintenance');
  const operationsTasks = activeTasks.filter(t => t.department?.toLowerCase() === 'operations');
  const stationTasks = activeTasks.filter(t =>
    t.department?.toLowerCase() === 'station_manager' ||
    t.department?.toLowerCase() === 'station'
  );

  const getUrgencyBadge = (urgency) => {
    let color = '#FF3333'; // Urgent/Critical
    let bg = 'rgba(255, 51, 51, 0.08)';
    let text = 'URGENT';

    if (urgency?.toLowerCase() === 'medium') {
      color = '#FFB000'; // Amber
      bg = 'rgba(255, 176, 0, 0.08)';
      text = 'MEDIUM';
    } else if (urgency?.toLowerCase() === 'resolved') {
      color = '#00FF66'; // Green
      bg = 'rgba(0, 255, 102, 0.08)';
      text = 'RESOLVED';
    }

    return (
      <span className="palantir-mono" style={{
        backgroundColor: bg,
        color: color,
        border: `1px solid ${color}`,
        padding: '2px 6px',
        fontSize: '9px',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        whiteSpace: 'nowrap'
      }}>
        {text}
      </span>
    );
  };

  const Column = ({ title, colTasks, count }) => (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: compact ? '8px' : '12px',
      backgroundColor: compact ? 'transparent' : '#0A0E17',
      border: compact ? 'none' : '1px solid #26354A',
      padding: compact ? '0' : '16px',
      minHeight: fullScreen ? '100%' : (compact ? 'auto' : '300px')
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #26354A', paddingBottom: '8px' }}>
        <h3 className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0' }}>{title}</h3>
        <span className="palantir-mono" style={{ backgroundColor: '#161F30', padding: '2px 8px', fontSize: '9px', color: '#8a9ba8', border: '1px solid #26354A' }}>
          {count}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1 }}>
        {colTasks.length === 0 ? (
           <div className="palantir-mono" style={{ color: '#5c7080', fontSize: '9px', textAlign: 'center', marginTop: '12px' }}>[ NO ACTIVE TASKS ]</div>
        ) : (
          colTasks.map(task => {
            const taskId = task.id || task._id;
            const isResolved = task.urgency === 'resolved' || task.status === 'resolved';

            return (
              <div key={taskId} style={{
                backgroundColor: '#161F30',
                border: '1px solid #26354A',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span className="palantir-mono" style={{ fontSize: '9px', color: '#8a9ba8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{task.action_required}</span>
                  {getUrgencyBadge(task.urgency)}
                </div>

                <div>
                  <h4 className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{task.task_description}</h4>
                  {!compact && <p className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080', lineHeight: '1.4' }}>{task.detail}</p>}
                </div>

                {!isResolved && (
                  <button
                    onClick={() => resolveHandler && resolveHandler(taskId)}
                    className="palantir-mono"
                    style={{
                      marginTop: '4px',
                      backgroundColor: 'transparent',
                      border: '1px solid #00FF66',
                      color: '#00FF66',
                      padding: '4px',
                      fontSize: '9px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(0, 255, 102, 0.1)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                  >
                    <CheckCircle2 size={10} /> RESOLVE
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: compact ? '16px' : '16px', overflow: 'hidden' }}>
      {fullScreen && (
         <div>
          <h2 className="palantir-mono" style={{ fontSize: '18px', fontWeight: 600, color: '#e2e8f0' }}>MULTI-DEPARTMENT TASK SYNCHRONIZATION</h2>
          <p className="palantir-mono" style={{ fontSize: '11px', color: '#5c7080' }}>ACTIVE COGNITIVE AGENT DISPATCHES</p>
        </div>
      )}

      {compact ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, overflowY: 'auto', paddingRight: '8px' }}>
          <Column title="MAINTENANCE" colTasks={maintenanceTasks} count={maintenanceTasks.length} />
          <Column title="OPERATIONS" colTasks={operationsTasks} count={operationsTasks.length} />
          <Column title="STATION CTRL" colTasks={stationTasks} count={stationTasks.length} />
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          flex: 1,
          overflow: 'hidden'
        }}>
          <Column title="MAINTENANCE NODE" colTasks={maintenanceTasks} count={maintenanceTasks.length} />
          <Column title="OPERATIONS NODE" colTasks={operationsTasks} count={operationsTasks.length} />
          <Column title="STATION CONTROL" colTasks={stationTasks} count={stationTasks.length} />
        </div>
      )}
    </div>
  );
}
