import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from './Sidebar';

describe('Sidebar Component', () => {
  it('renders correctly with default active tab', () => {
    render(<Sidebar />);

    // Check header
    expect(screen.getByText('SYS // ALPHA')).toBeInTheDocument();
    expect(screen.getByText('VIGILANCE // ACTIVE')).toBeInTheDocument();

    // Check all menu items
    expect(screen.getByText('DASHBOARD')).toBeInTheDocument();
    expect(screen.getByText('LIVE MAP')).toBeInTheDocument();
    expect(screen.getByText('INCIDENT FEED')).toBeInTheDocument();
    expect(screen.getByText('TASK BOARD')).toBeInTheDocument();
    expect(screen.getByText('ANALYTICS')).toBeInTheDocument();

    // Check bottom items
    expect(screen.getByText('SUPPORT // HELP')).toBeInTheDocument();
    expect(screen.getByText('SYSTEM LOGS')).toBeInTheDocument();
  });

  it('applies active styling to the correct tab', () => {
    const { rerender } = render(<Sidebar activeTab="Dashboard" />);

    // Check dashboard styling
    const dashboardButton = screen.getByText('DASHBOARD').closest('button');
    expect(dashboardButton).toHaveStyle('background-color: #121820'); // active

    const liveMapButton = screen.getByText('LIVE MAP').closest('button');
    expect(liveMapButton).toHaveStyle('background-color: rgba(0, 0, 0, 0)'); // inactive

    // Rerender with different active tab
    rerender(<Sidebar activeTab="Live Map" />);

    expect(screen.getByText('DASHBOARD').closest('button')).toHaveStyle('background-color: rgba(0, 0, 0, 0)');
    expect(screen.getByText('LIVE MAP').closest('button')).toHaveStyle('background-color: #121820');
  });

  it('calls setActiveTab when a menu item is clicked', () => {
    const setActiveTabMock = vi.fn();
    render(<Sidebar activeTab="Dashboard" setActiveTab={setActiveTabMock} />);

    // Click Live Map
    fireEvent.click(screen.getByText('LIVE MAP'));
    expect(setActiveTabMock).toHaveBeenCalledWith('Live Map');

    // Click Support
    fireEvent.click(screen.getByText('SUPPORT // HELP'));
    expect(setActiveTabMock).toHaveBeenCalledWith('Support');
  });

  it('does not throw when setActiveTab is not provided', () => {
    render(<Sidebar activeTab="Dashboard" />);

    // Clicking should not crash the component
    expect(() => {
      fireEvent.click(screen.getByText('LIVE MAP'));
    }).not.toThrow();
  });
});
