import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LiveMap from './LiveMap';

// Mock react-leaflet
vi.mock('react-leaflet', () => {
  return {
    MapContainer: ({ children }) => <div data-testid="map-container">{children}</div>,
    TileLayer: () => <div data-testid="tile-layer" />,
    Marker: ({ children, icon }) => (
      <div data-testid="marker" data-icon-html={icon?.options?.html}>
        {children}
      </div>
    ),
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
    expect(markers).toHaveLength(3); // 3 fallback trains

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

  it('renders correctly with delayed and cancelled trains', () => {
    const customTrains = [
      {
        train_number: "11111",
        train_name: "Delayed Train",
        train_id: "TN-1111",
        speed: "60 km/h",
        next_station: "DEF",
        distance_next: "5 KM",
        current_station: "GHI",
        delay_minutes: 20,
        status: "Delayed",
        lat: 22.0,
        lng: 82.0
      },
      {
        train_number: "22222",
        train_name: "Cancelled Train",
        train_id: "TN-2222",
        speed: "0 km/h",
        next_station: "JKL",
        distance_next: "0 KM",
        current_station: "MNO",
        delay_minutes: 0,
        status: "cancelled",
        lat: 24.0,
        lng: 84.0
      },
      {
        // Bare minimum train to cover fallback values
        train_number: "33333",
        current_station: "UNKNOWN_STATION"
      },
      {
        // Missing train number
        train_name: "Missing ID",
        lat: 10,
        lng: 10
      }
    ];

    render(<LiveMap trains={customTrains} />);

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(4);

    expect(screen.getByText('Delayed Train')).toBeInTheDocument();
    expect(screen.getByText('Cancelled Train')).toBeInTheDocument();

    // Delayed marker should have warning color (#ffb300)
    expect(markers[0]).toHaveAttribute('data-icon-html', expect.stringContaining('#ffb300'));

    // Cancelled marker should have critical color (#ff3366)
    expect(markers[1]).toHaveAttribute('data-icon-html', expect.stringContaining('#ff3366'));
  });
});
