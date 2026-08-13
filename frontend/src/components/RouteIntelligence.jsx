/* eslint-disable */
import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Folder, Train, Activity, ShieldAlert, Award, Compass } from 'lucide-react';

export default function RouteIntelligence({ trains = [] }) {
  // Route Tree States
  const [expandedSectors, setExpandedSectors] = useState(new Set(['Sector 4']));
  const [selectedTrain, setSelectedTrain] = useState('Train 402');

  const toggleSector = (sector) => {
    const next = new Set(expandedSectors);
    if (next.has(sector)) {
      next.delete(sector);
    } else {
      next.add(sector);
    }
    setExpandedSectors(next);
  };

  // Dummy / Mock active route data matching Image 2
  const activeRoute = {
    train: selectedTrain,
    sector: 'Sector 4',
    speed: selectedTrain === 'Train 402' ? '112 km/h' : selectedTrain === 'Train 403' ? '98 km/h' : '82 km/h',
    fuel: selectedTrain === 'Train 402' ? '94.2%' : '88.5%',
    delayProb: selectedTrain === 'Train 402' ? 14 : 35,
    confidence: selectedTrain === 'Train 402' ? 88 : 74,
  };

  return (
    <div style={{ display: 'flex', flex: 1, height: '100%', overflow: 'hidden' }}>
      
      {/* Route Tree Navigation (Left Column) */}
      <div style={{
        width: '240px',
        backgroundColor: '#161F30',
        borderRight: '1px solid #26354A',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        padding: '16px 0',
        flexShrink: 0
      }}>
        <div style={{ padding: '0 16px 12px 16px', borderBottom: '1px solid #26354A' }}>
          <span className="palantir-mono" style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '0.5px' }}>Route Tree</span>
        </div>
        
        <div style={{ padding: '16px 8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Network Root Folder */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 8px', cursor: 'pointer', color: '#e2e8f0' }}>
              <ChevronDown size={14} style={{ color: '#5c7080' }} />
              <Folder size={14} style={{ color: '#FFB000' }} />
              <span className="palantir-mono" style={{ fontSize: '11px', fontWeight: 600 }}>Rail Network</span>
            </div>
            
            {/* Sector Folders */}
            <div style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              {/* Sector 4 */}
              <div>
                <div 
                  onClick={() => toggleSector('Sector 4')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', cursor: 'pointer', color: '#8a9ba8' }}
                >
                  {expandedSectors.has('Sector 4') ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  <Folder size={12} style={{ color: '#ffb300' }} />
                  <span className="palantir-mono" style={{ fontSize: '11px' }}>Sector 4</span>
                </div>
                
                {expandedSectors.has('Sector 4') && (
                  <div style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '2px' }}>
                    {['Train 402'].map(tr => (
                      <div 
                        key={tr}
                        onClick={() => setSelectedTrain(tr)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', cursor: 'pointer',
                          backgroundColor: selectedTrain === tr ? 'rgba(0, 240, 255, 0.08)' : 'transparent',
                          color: selectedTrain === tr ? '#FFB000' : '#8a9ba8',
                          borderLeft: selectedTrain === tr ? '2px solid #FFB000' : '2px solid transparent'
                        }}
                      >
                        <Train size={12} />
                        <span className="palantir-mono" style={{ fontSize: '11px' }}>{tr}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Sector 5 */}
              <div>
                <div 
                  onClick={() => toggleSector('Sector 5')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', cursor: 'pointer', color: '#8a9ba8' }}
                >
                  {expandedSectors.has('Sector 5') ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  <Folder size={12} style={{ color: '#ffb300' }} />
                  <span className="palantir-mono" style={{ fontSize: '11px' }}>Sector 5</span>
                </div>
                
                {expandedSectors.has('Sector 5') && (
                  <div style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '2px', marginTop: '2px' }}>
                    {['Train 403', 'Train 404'].map(tr => (
                      <div 
                        key={tr}
                        onClick={() => setSelectedTrain(tr)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', cursor: 'pointer',
                          backgroundColor: selectedTrain === tr ? 'rgba(0, 240, 255, 0.08)' : 'transparent',
                          color: selectedTrain === tr ? '#FFB000' : '#8a9ba8',
                          borderLeft: selectedTrain === tr ? '2px solid #FFB000' : '2px solid transparent'
                        }}
                      >
                        <Train size={12} />
                        <span className="palantir-mono" style={{ fontSize: '11px' }}>{tr}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      </div>

      {/* Center Console Workspace */}
      <div style={{
        flex: 1,
        backgroundColor: '#0A0E17',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden'
      }}>
        
        {/* Breadcrumb Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid #26354A',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#161F30'
        }}>
          <div className="palantir-mono" style={{ fontSize: '11px', color: '#8a9ba8' }}>
            Rail Network &gt; {activeRoute.sector} &gt; <span style={{ color: '#FFB000', fontWeight: 600 }}>{activeRoute.train}</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palantir-mono" style={{
              fontSize: '10px',
              backgroundColor: '#161F30',
              border: '1px solid #26354A',
              color: '#8a9ba8',
              padding: '4px 10px',
              borderRadius: '0px'
            }}>
              ⚙ Last 24h
            </span>
          </div>
        </div>

        {/* Metrics Grid (Row) */}
        <div style={{ padding: '24px 24px 12px 24px' }}>
          <div className="palantir-mono" style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600, marginBottom: '12px', letterSpacing: '0.5px' }}>Metrics Grid</div>
          <div style={{ display: 'flex', gap: '16px' }}>
            
            {/* Speed Metric */}
            <div style={{
              flex: 1,
              backgroundColor: '#161F30',
              border: '1px solid #26354A',
              padding: '16px',
              position: 'relative'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#5c7080' }}>
                <span className="palantir-mono">Train Speed</span>
                <span>•••</span>
              </div>
              <div className="palantir-mono" style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', margin: '8px 0 2px 0' }}>{activeRoute.speed}</div>
              <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>Real-time</span>
              {/* Sparkline SVG */}
              <div style={{ marginTop: '10px', height: '32px' }}>
                <svg width="100%" height="100%" viewBox="0 0 100 30" preserveAspectRatio="none">
                  <path d="M0 25 Q15 5, 30 18 T60 8 T90 20 L100 15" fill="none" stroke="#FFB000" strokeWidth={1.5} />
                </svg>
              </div>
            </div>

            {/* Fuel Efficiency */}
            <div style={{
              flex: 1,
              backgroundColor: '#161F30',
              border: '1px solid #26354A',
              padding: '16px',
              position: 'relative'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#5c7080' }}>
                <span className="palantir-mono">Fuel Efficiency</span>
                <span>•••</span>
              </div>
              <div className="palantir-mono" style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', margin: '8px 0 2px 0' }}>
                {activeRoute.fuel} <span style={{ color: '#00e676', fontSize: '12px' }}>↗</span>
              </div>
              <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>Target: 92%</span>
              {/* Green Sparkline SVG */}
              <div style={{ marginTop: '10px', height: '32px' }}>
                <svg width="100%" height="100%" viewBox="0 0 100 30" preserveAspectRatio="none">
                  <path d="M0 28 Q20 20, 40 25 T80 15 T100 8" fill="none" stroke="#00e676" strokeWidth={1.5} />
                </svg>
              </div>
            </div>

            {/* Delay Probability */}
            <div style={{
              flex: 1,
              backgroundColor: '#161F30',
              border: '1px solid #26354A',
              padding: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', justifySelf: 'flex-start' }}>
                <span className="palantir-mono" style={{ fontSize: '10px', color: '#5c7080' }}>Delay Probability</span>
                <span className="palantir-mono" style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', marginTop: '8px' }}>{activeRoute.delayProb}% Low</span>
                <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080', marginTop: '4px' }}>Confidence: {activeRoute.confidence}%</span>
              </div>
              {/* Circular Progress Ring */}
              <div style={{ width: '48px', height: '48px', position: 'relative' }}>
                <svg width="100%" height="100%" viewBox="0 0 36 36">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#26354A" strokeWidth={3} />
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#00e676" strokeWidth={3} strokeDasharray={`${activeRoute.delayProb}, 100`} />
                </svg>
              </div>
            </div>

          </div>
        </div>

        {/* Route Timeline / Gantt Log Layout */}
        <div style={{ padding: '0 24px 24px 24px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div className="palantir-mono" style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600, marginBottom: '12px', letterSpacing: '0.5px' }}>Route Timeline/Log</div>
          
          <div style={{
            flex: 1,
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            {/* Timeline Hour Axis Header */}
            <div style={{
              display: 'flex',
              padding: '12px 16px',
              borderBottom: '1px solid #26354A',
              backgroundColor: '#161F30'
            }}>
              {['12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'].map((hour, index) => (
                <div key={index} className="palantir-mono" style={{ flex: 1, textAlign: 'center', fontSize: '10px', color: '#5c7080' }}>
                  {hour}
                </div>
              ))}
            </div>

            {/* Gantt Row Bars */}
            <div style={{ flex: 1, padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
              
              {/* Mumbai Block */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ width: '100px', flexShrink: 0 }} className="palantir-mono">
                  <span style={{ fontSize: '11px', color: '#e2e8f0' }}>Mumbai</span>
                </div>
                <div style={{ flex: 1, position: 'relative', height: '36px' }}>
                  <div style={{
                    position: 'absolute', left: '0%', width: '35%', height: '100%',
                    backgroundColor: '#ff3366', borderLeft: '4px solid #ff3366',
                    padding: '6px 10px', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                  }}>
                    <span className="palantir-mono" style={{ fontSize: '10px', color: '#0A0E17', fontWeight: 700 }}>Delayed</span>
                  </div>
                </div>
              </div>

              {/* Surat Block */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ width: '100px', flexShrink: 0 }} className="palantir-mono">
                  <span style={{ fontSize: '11px', color: '#e2e8f0' }}>Surat</span>
                </div>
                <div style={{ flex: 1, position: 'relative', height: '36px' }}>
                  <div style={{
                    position: 'absolute', left: '35%', width: '30%', height: '100%',
                    backgroundColor: '#00e676', borderLeft: '4px solid #00e676',
                    padding: '6px 10px', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                  }}>
                    <span className="palantir-mono" style={{ fontSize: '10px', color: '#0A0E17', fontWeight: 700 }}>On Time</span>
                  </div>
                </div>
              </div>

              {/* Nagpur Block */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ width: '100px', flexShrink: 0 }} className="palantir-mono">
                  <span style={{ fontSize: '11px', color: '#e2e8f0' }}>Nagpur</span>
                </div>
                <div style={{ flex: 1, position: 'relative', height: '36px' }}>
                  <div style={{
                    position: 'absolute', left: '65%', width: '25%', height: '100%',
                    backgroundColor: '#ffb300', borderLeft: '4px solid #ffb300',
                    padding: '6px 10px', display: 'flex', flexDirection: 'column', justifyContent: 'center'
                  }}>
                    <span className="palantir-mono" style={{ fontSize: '10px', color: '#0A0E17', fontWeight: 700 }}>Signal Warning</span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>

      {/* AI Insights & Recommendation Panel (Right Column) */}
      <div style={{
        width: '320px',
        backgroundColor: '#161F30',
        borderLeft: '1px solid #26354A',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        flexShrink: 0
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #26354A',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 className="palantir-mono" style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0', letterSpacing: '0.5px' }}>AI Insights</h2>
            <span className="palantir-mono" style={{ fontSize: '9px', color: '#5c7080' }}>Natural language summaries</span>
          </div>
          <button style={{ backgroundColor: 'transparent', border: 'none', color: '#5c7080', cursor: 'pointer' }}>
            <span style={{ fontSize: '14px', fontWeight: 700 }}>•••</span>
          </button>
        </div>

        {/* Content Details */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Performance Summary */}
          <div style={{
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            padding: '16px',
            borderRadius: '0px'
          }}>
            <h4 className="palantir-mono" style={{ fontSize: '11px', color: '#FFB000', marginBottom: '8px', fontWeight: 700 }}>
              ⎎ Performance Summary
            </h4>
            <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5' }}>
              Route running within acceptable parameters despite minor delays at Mumbai and Nagpur. Fuel efficiency is slightly above target.
            </p>
          </div>

          {/* Suggested Optimizations */}
          <div style={{
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            padding: '16px',
            borderRadius: '0px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <h4 className="palantir-mono" style={{ fontSize: '11px', color: '#ffb300', fontWeight: 700 }}>
              ↯ Suggested Optimizations
            </h4>
            <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5' }}>
              Reroute recommended due to signal maintenance at Nagpur. Suggesting alternate path via Wardha junction to avoid potential 15-minute delay.
            </p>
            <button style={{
              backgroundColor: '#1c2430',
              border: '1px solid #26354A',
              color: '#FFB000',
              padding: '8px 16px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              alignSelf: 'flex-start',
              fontFamily: "'JetBrains Mono', monospace"
            }}>
              Review Path
            </button>
          </div>

          {/* Anomaly Detection Status block */}
          <div style={{
            backgroundColor: '#161F30',
            border: '1px solid #26354A',
            padding: '16px',
            borderRadius: '0px'
          }}>
            <h4 className="palantir-mono" style={{ fontSize: '11px', color: '#5c7080', marginBottom: '8px', fontWeight: 700 }}>
              🛡 Anomaly Detection
            </h4>
            <p className="palantir-mono" style={{ fontSize: '11px', color: '#5c7080' }}>
              No current critical anomalies detected.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
}
