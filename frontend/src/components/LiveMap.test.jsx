import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LiveMap from './LiveMap';

// Mock react-leaflet
vi.mock('react-leaflet', () => {
  return {
    MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => <div data-testid="tile-layer" />,
    Marker: ({ children }) => <div data-testid="marker">{children}</div>,
    Popup: ({ children }) => <div data-testid="popup">{children}</div>,
    ZoomControl: () => <div data-testid="zoom-control" />
  };
});

describe('LiveMap Component', () => {
  it('renders gracefully with empty train array (fallback logic)', () => {
    render(<LiveMap trains={[]} />);

    // Fallback data is expected to show 3 markers
    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(4); // 4 fallback trains

    expect(screen.getByText('Chennai Exp')).toBeInTheDocument();
    expect(screen.getByText('Mumbai Rajdhani')).toBeInTheDocument();
    expect(screen.getByText('Howrah Duronto')).toBeInTheDocument();
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

    render(<LiveMap trains={customTrains} />);

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(1);

    expect(screen.getByText('Test Express')).toBeInTheDocument();
  });
});
