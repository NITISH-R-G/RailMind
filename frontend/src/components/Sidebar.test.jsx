import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from './Sidebar';

describe('Sidebar Component', () => {
  it('calls setActiveTab when a top menu item is clicked', () => {
    const setActiveTabMock = vi.fn();
    render(<Sidebar activeTab="Dashboard" setActiveTab={setActiveTabMock} />);

    const liveMapButton = screen.getByText('LIVE MAP');
    fireEvent.click(liveMapButton);

    expect(setActiveTabMock).toHaveBeenCalledTimes(1);
    expect(setActiveTabMock).toHaveBeenCalledWith('Live Map');
  });

  it('calls setActiveTab when a bottom menu item is clicked', () => {
    const setActiveTabMock = vi.fn();
    render(<Sidebar activeTab="Dashboard" setActiveTab={setActiveTabMock} />);

    const logsButton = screen.getByText('SYSTEM LOGS');
    fireEvent.click(logsButton);

    expect(setActiveTabMock).toHaveBeenCalledTimes(1);
    expect(setActiveTabMock).toHaveBeenCalledWith('Logs');
  });

  it('does not crash when clicked without setActiveTab provided', () => {
    render(<Sidebar activeTab="Dashboard" />);

    const dashboardButton = screen.getByText('DASHBOARD');

    expect(() => fireEvent.click(dashboardButton)).not.toThrow();
  });
});
