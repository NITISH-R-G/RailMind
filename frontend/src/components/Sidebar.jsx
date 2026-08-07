/* eslint-disable */
import React from 'react';
import { LayoutDashboard, Map, BellRing, ClipboardList, BarChart3, HelpCircle, FileClock, Sliders } from 'lucide-react';
import { useStore } from '../store';

export default function Sidebar() {
  const activeTab = useStore(state => state.activeTab);
  const setActiveTab = useStore(state => state.setActiveTab);

  const menuItems = [
    { id: 'Dashboard', name: 'Overview', icon: LayoutDashboard },
    { id: 'Live Map', name: 'Real-Time Map', icon: Map },
    { id: 'Incident Feed', name: 'Incident Alerts', icon: BellRing },
    { id: 'Task Board', name: 'Tasks', icon: ClipboardList },
    { id: 'Analytics', name: 'Reports', icon: BarChart3 },
    { id: 'Simulation', name: 'Simulation Portal', icon: Sliders }
  ];

  const bottomItems = [
    { id: 'Support', name: 'Help & Support', icon: HelpCircle },
    { id: 'Logs', name: 'System Events', icon: FileClock }
  ];

  return (
    <div style={{
      width: '100%',
      backgroundColor: '#0A0E17',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: '100%',
      padding: '24px 0 16px 0',
      flexShrink: 0
    }}>
      <div>
        {/* Header */}
        <div style={{ padding: '0 24px 24px 24px', borderBottom: '1px solid #26354A' }}>
          <h2 className="palantir-mono" style={{ fontSize: '15px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '1px' }}>SYS // ALPHA</h2>
          <span className="palantir-mono" style={{ fontSize: '10px', color: '#00FF66', fontWeight: 500 }}>Monitoring: Active</span>
        </div>

        {/* Navigation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '24px 12px 0 12px' }}>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab && setActiveTab(item.id)}
                className="palantir-mono"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  backgroundColor: isActive ? '#161F30' : 'transparent',
                  border: 'none',
                  borderLeft: isActive ? '3px solid #00FF66' : '3px solid transparent',
                  color: isActive ? '#00FF66' : '#8a9ba8',
                  width: '100%',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.2s ease',
                  textTransform: 'uppercase'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = '#161F30';
                    e.currentTarget.style.color = '#e2e8f0';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#8a9ba8';
                  }
                }}
              >
                <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                {item.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom Actions */}
      <div style={{ padding: '0 12px' }}>
        <div style={{ height: '1px', backgroundColor: '#26354A', margin: '16px 12px' }}></div>
        {bottomItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab && setActiveTab(item.id)}
              className="palantir-mono"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                backgroundColor: 'transparent',
                border: 'none',
                color: isActive ? '#00FF66' : '#8a9ba8',
                width: '100%',
                textAlign: 'left',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: 500,
                transition: 'all 0.2s',
                textTransform: 'uppercase'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = '#e2e8f0'; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = '#8a9ba8'; }}
            >
              <Icon size={16} />
              {item.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}
