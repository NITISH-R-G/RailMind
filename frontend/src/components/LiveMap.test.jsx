import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import LiveMap from './LiveMap';
import useStore from '../store';

// Mock react-leaflet
vi.mock('react-leaflet', () => {
  return {
    MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => <div data-testid="tile-layer" />,
    Marker: ({ children }) => <div data-testid="marker">{children}</div>,
    Popup: ({ children }) => <div data-testid="popup">{children}</div>,
    ZoomControl: () => <div data-testid="zoom-control" />,
    Polyline: () => <div data-testid="polyline" />
  };
});

describe('LiveMap Component', () => {
  beforeEach(() => {
    // Reset Zustand store state before each test
    useStore.setState({
      trains: [],
      incidents: []
    });
  });

  it('renders gracefully with empty train array', () => {
    render(<LiveMap />);
    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();

    // Markers should not exist if trains/incidents are empty
    const markers = screen.queryAllByTestId('marker');
    expect(markers).toHaveLength(0);
  });

  it('renders with provided trains and incidents via store', () => {
    const customTrains = [
      {
        train_number: "99999",
        train_name: "Test Express",
        delay_minutes: 5,
        status: "On Time",
        lat: 20.0,
        lng: 80.0
      }
    ];

    const customIncidents = [
      {
        id: "inc1",
        train_number: "99999",
        severity: "critical",
        approved: true,
        reroute_plan: "NDLS ➔ ALD"
      }
    ];

    useStore.setState({ trains: customTrains, incidents: customIncidents });
    render(<LiveMap />);

    const markers = screen.getAllByTestId('marker');
    // 1 Train marker + 1 Anomaly marker
    expect(markers).toHaveLength(2);

    // Check if polyline for reroute is rendered
    const polylines = screen.getAllByTestId('polyline');
    expect(polylines).toHaveLength(1);
  });
});
