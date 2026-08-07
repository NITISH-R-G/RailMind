/* eslint-disable */
import React from 'react';
import { Bell, Settings } from 'lucide-react';
import { useStore } from '../store';

export default function TopBar() {
  const loopCount = useStore(state => state.loopCount);
  const incidentCount = useStore(state => state.incidentCount);
  const wsStatus = useStore(state => state.wsStatus);
  const activeTab = useStore(state => state.activeTab);
  const setActiveTab = useStore(state => state.setActiveTab);

  const setShowNotifications = useStore(state => state.setShowNotifications);
  const setShowSettings = useStore(state => state.setShowSettings);
  const setShowProfile = useStore(state => state.setShowProfile);

  const tabs = ['Rail Network', 'Sensor Data', 'Timetable', 'Fleet'];
  const activeTopTab = ['Sensor Data', 'Timetable', 'Fleet'].includes(activeTab) ? activeTab : 'Rail Network';
  const isConnected = wsStatus === 'connected';

  const onTabChange = (tab) => {
    if (tab === 'Rail Network') {
      setActiveTab('Dashboard');
    } else {
      setActiveTab(tab);
    }
  };

  return (
    <div style={{
      height: '64px',
      backgroundColor: '#161F30',
      borderBottom: '1px solid #26354A',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      flexShrink: 0
    }}>
      {/* Left section: Logo & Nav tabs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="palantir-mono" style={{
            fontSize: '18px',
            fontWeight: 700,
            color: '#e2e8f0', 
            letterSpacing: '1px'
          }}>RAILMIND <span style={{ color: '#5c7080', fontWeight: 500 }}>// COMMAND CENTER</span></span>
        </div>
        
        {/* Nav tabs */}
        <div style={{ display: 'flex', gap: '24px' }}>
          {tabs.map((tab) => {
            const isActive = tab === activeTopTab;
            return (
              <button
                key={tab}
                onClick={() => onTabChange(tab)}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  borderBottom: isActive ? '2px solid #00FF66' : '2px solid transparent',
                  color: isActive ? '#00FF66' : '#8a9ba8',
                  cursor: 'pointer',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '12px',
                  fontWeight: isActive ? 600 : 500,
                  height: '64px',
                  padding: '0 4px',
                  textTransform: 'uppercase',
                  transition: 'color 0.2s, border-bottom 0.2s'
                }}
              >
                {tab}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right section: System Status & User Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', borderRight: '1px solid #26354A', paddingRight: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>AGENT LOOPS</span>
            <span className="palantir-mono" style={{ fontSize: '13px', color: '#00FF66', fontWeight: 600 }}>{loopCount}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>TELEMETRY UPLINK</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{
                width: '6px',
                height: '6px',
                backgroundColor: isConnected ? '#00FF66' : '#FF3333',
                borderRadius: '0px'
              }}></span>
              <span className="palantir-mono" style={{
                fontSize: '11px',
                color: isConnected ? '#00FF66' : '#FF3333',
                fontWeight: 600
              }}>
                {isConnected ? 'SECURE' : 'DROPPED'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button 
            onClick={() => setShowNotifications(true)}
            style={{
              background: 'transparent', border: 'none', color: incidentCount > 0 ? '#FF3333' : '#8a9ba8', cursor: 'pointer', position: 'relative'
            }}
          >
            <Bell size={18} />
            {incidentCount > 0 && (
              <span className="palantir-mono" style={{
                position: 'absolute', top: '-6px', right: '-8px', backgroundColor: '#FF3333', color: '#fff',
                fontSize: '9px', fontWeight: 700, padding: '2px 4px', borderRadius: '0px'
              }}>
                {incidentCount}
              </span>
            )}
          </button>

          <button onClick={() => setShowSettings(true)} style={{ background: 'transparent', border: 'none', color: '#8a9ba8', cursor: 'pointer' }}>
            <Settings size={18} />
          </button>

          <button
            onClick={() => setShowProfile(true)}
            style={{
              width: '32px', height: '32px', borderRadius: '0px', overflow: 'hidden',
              border: '1px solid #00FF66', cursor: 'pointer', padding: 0
            }}
          >
            <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=64&q=80" alt="User" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </button>
        </div>
      </div>
    </div>
  );
}
