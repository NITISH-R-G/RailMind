import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import IncidentFeed from './IncidentFeed';
import { describe, it, expect, vi } from 'vitest';

describe('IncidentFeed', () => {
  const mockIncidents = [
    {
      id: 'inc-1',
      title: 'Test Incident 1',
      description: 'This is a test incident description.',
      severity: 'critical',
      timestamp: '10:00 AM',
      maintenance_task: 'Fix the tracks',
      operations_task: 'Reroute train',
      station_manager_task: 'Announce delay',
      departments: ['Maintenance', 'Operations']
    },
    {
      id: 'inc-2',
      title: 'Test Incident 2',
      description: 'This is another test incident.',
      severity: 'warning',
      timestamp: '11:00 AM',
      reroute_plan: 'Take alternate route B',
      approved: false
    }
  ];

  it('renders "No recent incidents detected." when incidents array is empty', () => {
    render(<IncidentFeed incidents={[]} />);
    expect(screen.getByText('No recent incidents detected.')).toBeInTheDocument();
  });

  it('renders a list of incidents correctly', () => {
    render(<IncidentFeed incidents={mockIncidents} />);

    // Check titles
    expect(screen.getByText('Test Incident 1')).toBeInTheDocument();
    expect(screen.getByText('Test Incident 2')).toBeInTheDocument();

    // Check descriptions
    expect(screen.getByText(/"This is a test incident description."/)).toBeInTheDocument();
  });

  it('toggles expand state to show details panels on click', () => {
    render(<IncidentFeed incidents={mockIncidents} />);

    // Initially, details are not visible
    expect(screen.queryByText('Fix the tracks')).not.toBeInTheDocument();

    // Find expand button for the first incident
    const expandButtons = screen.getAllByText('EXPAND ▼');
    fireEvent.click(expandButtons[0]);

    // Details should now be visible
    expect(screen.getByText('Fix the tracks')).toBeInTheDocument();
    expect(screen.getByText('COLLAPSE ▲')).toBeInTheDocument();

    // Click collapse
    fireEvent.click(screen.getByText('COLLAPSE ▲'));

    // Details should be hidden again
    expect(screen.queryByText('Fix the tracks')).not.toBeInTheDocument();
  });

  it('calls onApprove when approve button is clicked', () => {
    const mockOnApprove = vi.fn();
    render(<IncidentFeed incidents={mockIncidents} onApprove={mockOnApprove} />);

    // Find approve button for the second incident
    const approveButton = screen.getByText('APPROVE');
    fireEvent.click(approveButton);

    expect(mockOnApprove).toHaveBeenCalledWith('inc-2');
  });
});
