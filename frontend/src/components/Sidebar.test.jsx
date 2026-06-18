import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from './Sidebar';

describe('Sidebar Component', () => {
  it('renders all menu items', () => {
    render(<Sidebar activeTab="Dashboard" setActiveTab={() => {}} />);

    expect(screen.getByText('DASHBOARD')).toBeInTheDocument();
    expect(screen.getByText('LIVE MAP')).toBeInTheDocument();
    expect(screen.getByText('INCIDENT FEED')).toBeInTheDocument();
    expect(screen.getByText('TASK BOARD')).toBeInTheDocument();
    expect(screen.getByText('ANALYTICS')).toBeInTheDocument();
    expect(screen.getByText('SUPPORT // HELP')).toBeInTheDocument();
    expect(screen.getByText('SYSTEM LOGS')).toBeInTheDocument();
  });

  it('highlights the active tab correctly', () => {
    render(<Sidebar activeTab="Live Map" setActiveTab={() => {}} />);

    // LIVE MAP should have the active background color
    const liveMapTab = screen.getByText('LIVE MAP').closest('button');
    expect(liveMapTab).toHaveStyle('background-color: rgb(18, 24, 32)'); // #121820 -> rgb(18, 24, 32) or just use hex

    // DASHBOARD should have transparent background
    const dashboardTab = screen.getByText('DASHBOARD').closest('button');
    expect(dashboardTab).toHaveStyle('background-color: rgba(0, 0, 0, 0)');
  });

  it('calls setActiveTab when a menu item is clicked', () => {
    const setActiveTabMock = vi.fn();
    render(<Sidebar activeTab="Dashboard" setActiveTab={setActiveTabMock} />);

    const analyticsTab = screen.getByText('ANALYTICS');
    fireEvent.click(analyticsTab);

    expect(setActiveTabMock).toHaveBeenCalledWith('Analytics');

    const supportTab = screen.getByText('SUPPORT // HELP');
    fireEvent.click(supportTab);

    expect(setActiveTabMock).toHaveBeenCalledWith('Support');
  });

  it('handles missing setActiveTab gracefully', () => {
    render(<Sidebar activeTab="Dashboard" />);

    const analyticsTab = screen.getByText('ANALYTICS');
    // Clicking should not crash the app
    fireEvent.click(analyticsTab);
  });
});
