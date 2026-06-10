import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from './Sidebar';

describe('Sidebar', () => {
  it('renders all menu items', () => {
    render(<Sidebar setActiveTab={() => {}} />);

    // Check main menu items
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Live Map')).toBeInTheDocument();
    expect(screen.getByText('Incident Feed')).toBeInTheDocument();
    expect(screen.getByText('Task Board')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();

    // Check bottom items
    expect(screen.getByText('SUPPORT')).toBeInTheDocument();
    expect(screen.getByText('LOGS')).toBeInTheDocument();
  });

  it('calls setActiveTab when a menu item is clicked', () => {
    const mockSetActiveTab = vi.fn();
    render(<Sidebar setActiveTab={mockSetActiveTab} />);

    const liveMapButton = screen.getByText('Live Map');
    fireEvent.click(liveMapButton);

    expect(mockSetActiveTab).toHaveBeenCalledWith('Live Map');
    expect(mockSetActiveTab).toHaveBeenCalledTimes(1);
  });

  it('applies active styling to the currently active tab', () => {
    const { rerender } = render(<Sidebar activeTab="Dashboard" setActiveTab={() => {}} />);

    // Check if Dashboard is styled as active
    let dashboardButton = screen.getByText('Dashboard').closest('button');
    expect(dashboardButton).toHaveStyle({ backgroundColor: '#1c202a', color: '#f8fafc' });

    // Check if Live Map is styled as inactive
    let liveMapButton = screen.getByText('Live Map').closest('button');
    expect(liveMapButton).toHaveStyle({ color: '#cbd5e1' });
    expect(liveMapButton.style.backgroundColor).toBe('transparent');

    // Rerender with 'Live Map' active
    rerender(<Sidebar activeTab="Live Map" setActiveTab={() => {}} />);

    dashboardButton = screen.getByText('Dashboard').closest('button');
    expect(dashboardButton).toHaveStyle({ color: '#cbd5e1' });
    expect(dashboardButton.style.backgroundColor).toBe('transparent');

    liveMapButton = screen.getByText('Live Map').closest('button');
    expect(liveMapButton).toHaveStyle({ backgroundColor: '#1c202a', color: '#f8fafc' });
  });

  it('handles missing setActiveTab gracefully', () => {
    // Should not throw an error if setActiveTab is missing
    render(<Sidebar />);

    const dashboardButton = screen.getByText('Dashboard');
    fireEvent.click(dashboardButton);
    // If it didn't throw, the test passes
  });
});
