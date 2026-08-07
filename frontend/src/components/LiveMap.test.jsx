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
    CircleMarker: ({ children }) => <div data-testid="circle-marker">{children}</div>,
    Polyline: () => <div data-testid="polyline" />,
    useMap: () => ({ fitBounds: vi.fn() })
  };
});

describe('LiveMap Component', () => {
  beforeEach(() => {
    useStore.setState({
      trains: [
        {
          train_number: 12621,
          train_name: 'Chennai Exp',
          location_geo: { type: 'Point', coordinates: [80.2707, 13.0827] }, // lng, lat
          speed: 80,
          delay_minutes: 0,
          status: 'nominal'
        },
        {
          train_number: 12951,
          train_name: 'Mumbai Rajdhani',
          location_geo: { type: 'Point', coordinates: [72.8197, 18.9696] },
          speed: 120,
          delay_minutes: 5,
          status: 'nominal'
        },
        {
          train_number: 12259,
          train_name: 'Howrah Duronto',
          location_geo: { type: 'Point', coordinates: [88.2636, 22.5958] },
          speed: 100,
          delay_minutes: 0,
          status: 'nominal'
        }
      ],
      incidents: []
    });
  });

  it('renders gracefully with trains from store', () => {
    render(<LiveMap />);

    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(3); // 3 trains in store

    expect(screen.getByText('12621')).toBeInTheDocument();
    expect(screen.getByText('12951')).toBeInTheDocument();
    expect(screen.getByText('12259')).toBeInTheDocument();
  });

  it('renders with specific trains when store is updated', () => {
    const customTrains = [
      {
        train_number: "99999",
        train_name: "Test Express",
        location_geo: { type: 'Point', coordinates: [80.0, 20.0] },
        speed: "100 km/h",
        delay_minutes: 5,
        status: "nominal"
      }
    ];

    useStore.setState({ trains: customTrains });

    render(<LiveMap />);

    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(1);

    expect(screen.getByText('99999')).toBeInTheDocument();
  });
});
