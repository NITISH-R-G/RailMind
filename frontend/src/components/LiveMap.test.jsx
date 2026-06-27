import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import LiveMap from './LiveMap';
import { useStore } from '../store';

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
    useStore.setState({ trains: [], incidents: [] });
  });

  it('renders gracefully with empty train array (fallback logic)', () => {
    render(<LiveMap />);

    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();

    const markers = screen.getAllByTestId('marker');
    // Our refactored component falls back to 1 fallback train
    expect(markers).toHaveLength(1);

    expect(screen.getByText('Howrah Rajdhani')).toBeInTheDocument();
  });

  it('renders with provided trains', () => {
    const customTrains = [
      {
        train_number: "99999",
        train_name: "Test Express",
        train_id: "TN-9999",
        speed: "100 km/h",
        next_station: "XYZ",
        distance_next: "10 KM",
        current_station: "ABC",
        delay_minutes: 5,
        status: "On Time",
        lat: 20.0,
        lng: 80.0
      }
    ];

    useStore.setState({ trains: customTrains });

    render(<LiveMap />);

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(1);

    expect(screen.getByText('Test Express')).toBeInTheDocument();
  });
});
