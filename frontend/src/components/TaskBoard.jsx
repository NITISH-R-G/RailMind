/* eslint-disable */
import React from 'react';
import { MoreHorizontal, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function TaskBoard({ tasks = [], onResolve, fullScreen = false }) {
  // Setup default mock tasks if tasks list is empty
  const activeTasks = tasks.length > 0 ? tasks : [
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
  ];

  // Group tasks by department
  const maintenanceTasks = activeTasks.filter(t => t.department?.toLowerCase() === 'maintenance');
  const operationsTasks = activeTasks.filter(t => t.department?.toLowerCase() === 'operations');
  const stationTasks = activeTasks.filter(t =>
    t.department?.toLowerCase() === 'station_manager' ||
    t.department?.toLowerCase() === 'station'
  );

  const getUrgencyBadge = (urgency) => {
    let color = '#ff3366'; // Red
    let bg = 'rgba(255, 51, 102, 0.08)';
    let text = 'Urgent';

    if (urgency.toLowerCase() === 'medium') {
      color = '#ffb300'; // Yellow
      bg = 'rgba(255, 179, 0, 0.08)';
      text = 'Medium';
    } else if (urgency.toLowerCase() === 'resolved') {
      color = '#00e676'; // Green
      bg = 'rgba(0, 230, 118, 0.08)';
      text = 'Resolved';
    } else if (urgency.toLowerCase() === 'low') {
      color = '#FFB000'; // Blue
      bg = 'rgba(0, 240, 255, 0.08)';
      text = 'Low';
    } else if (urgency.toLowerCase() === 'high') {
      color = '#ffb300'; // Orange
      bg = 'rgba(255, 179, 0, 0.08)';
      text = 'High';
    } else if (urgency.toLowerCase() === 'critical') {
      color = '#ff3366'; // Dark Red
      bg = 'rgba(255, 51, 102, 0.08)';
      text = 'Critical';
    }

    return (
      <span className="palantir-mono" style={{
        fontSize: '9px',
        fontWeight: 700,
        color: color,
        backgroundColor: bg,
        padding: '2px 6px',
        border: `1px solid ${color}`,
        borderRadius: '0px',
        letterSpacing: '1px'
      }}>
        {text}
      </span>
    );
  };

  const renderColumn = (title, columnTasks) => {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '16px',
        borderRight: '1px solid #26354A'
      }}>
        <h3 className="palantir-mono" style={{
          fontSize: '10px',
          fontWeight: 600,
          color: '#5c7080',
          letterSpacing: '1px',
          textTransform: 'uppercase'
        }}>
          {title}
        </h3>
        
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          overflowY: 'auto'
        }}>
          {columnTasks.map((task) => {
            const isResolved = task.status?.toLowerCase() === 'resolved' || task.urgency?.toLowerCase() === 'resolved';

            return (
              <div
                key={task.id || task._id}
                style={{
                  backgroundColor: '#161F30',
                  border: '1px solid #26354A',
                  borderRadius: '0px',
                  padding: '16px',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#17202b';
                  e.currentTarget.style.borderColor = '#FFB000';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#161F30';
                  e.currentTarget.style.borderColor = '#26354A';
                }}
              >
                {/* Badge & dots */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {getUrgencyBadge(task.urgency)}
                  {isResolved ? (
                    <CheckCircle2 size={16} style={{ color: '#00e676' }} />
                  ) : (
                    <button 
                      onClick={() => onResolve && onResolve(task._id || task.id)}
                      title="Mark task as resolved"
                      style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#5c7080',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#00e676'}
                      onMouseLeave={(e) => e.currentTarget.style.color = '#5c7080'}
                    >
                      <span style={{ fontSize: '12px', fontWeight: 'bold' }}>•••</span>
                    </button>
                  )}
                </div>

                {/* Description */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {!isResolved && task.urgency?.toLowerCase() === 'urgent' && (
                    <AlertTriangle size={16} style={{ color: '#ff3366', flexShrink: 0 }} />
                  )}
                  <span className="palantir-mono" style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: isResolved ? '#5c7080' : '#fff',
                    textDecoration: isResolved ? 'line-through' : 'none'
                  }}>
                    {task.task_description || task.description}
                  </span>
                </div>

                {/* Details */}
                <span className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080', fontWeight: 500 }}>
                  {task.action_required}
                </span>

                {/* Short Task description */}
                <span style={{ fontSize: '11px', color: '#8a9ba8', lineHeight: '1.4' }}>
                  {task.detail || task.situation_summary || "Anomaly logged. Awaiting dispatch actions."}
                </span>

                {/* Action Buttons */}
                {!isResolved ? (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <button 
                      onClick={() => onResolve && onResolve(task._id || task.id)}
                      className="palantir-mono"
                      style={{
                        flex: 1,
                        backgroundColor: '#1c2430',
                        border: '1px solid #26354A',
                        color: '#e2e8f0',
                        fontSize: '10px',
                        padding: '6px 0',
                        cursor: 'pointer',
                        borderRadius: '0px',
                        fontWeight: 600
                      }}
                    >
                      Action
                    </button>
                    <button 
                      className="palantir-mono"
                      style={{
                        flex: 1,
                        backgroundColor: '#1c2430',
                        border: '1px solid #26354A',
                        color: '#e2e8f0',
                        fontSize: '10px',
                        padding: '6px 0',
                        cursor: 'pointer',
                        borderRadius: '0px',
                        fontWeight: 600
                      }}
                    >
                      Assign
                    </button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <button 
                      disabled
                      className="palantir-mono"
                      style={{
                        flex: 1,
                        backgroundColor: 'rgba(0, 230, 118, 0.04)',
                        border: '1px solid rgba(0, 230, 118, 0.15)',
                        color: '#00e676',
                        fontSize: '10px',
                        padding: '6px 0',
                        borderRadius: '0px',
                        fontWeight: 600,
                        textAlign: 'center'
                      }}
                    >
                      Resolved ✓
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div style={{
      height: fullScreen ? '100%' : '250px',
      flex: fullScreen ? 1 : 'none',
      backgroundColor: '#161F30',
      borderTop: '1px solid #26354A',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: fullScreen ? 1 : 0
    }}>
      {/* Legend & Header */}
      <div style={{
        padding: '12px 24px',
        borderBottom: '1px solid #26354A',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '1px' }}>
          Tasks
        </h2>
        
        {/* Legend */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', backgroundColor: '#ff3366' }}></span>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080', fontWeight: 600 }}>[ Urgent ]</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', backgroundColor: '#ffb300' }}></span>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080', fontWeight: 600 }}>[ Medium ]</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', backgroundColor: '#00e676' }}></span>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080', fontWeight: 600 }}>[ Resolved ]</span>
          </div>
        </div>
      </div>

      {/* Grid columns */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {renderColumn('Maintenance', maintenanceTasks)}
        {renderColumn('Operations', operationsTasks)}
        {renderColumn('Station Manager', stationTasks)}
      </div>
    </div>
  );
}
