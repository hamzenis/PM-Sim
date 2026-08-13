import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ScenarioPanel from './ScenarioPanel';

test('uses human-readable assignment labels and keeps identifiers hidden', () => {
	const onUnassign = vi.fn();
	render(<ScenarioPanel selectedId="6b8d4cf0-9b31-4a4f-8031-1e5ccb66d272" revisions={[]} assignments={[{
		id: '561cd5c9-3791-480e-934b-29b1922ed88a', scenario_id: 'hidden-id', scenario_name: 'City Transit Launch', revision_number: 3, status: 'published',
	}]} isBusy={false} onAssign={vi.fn()} onUnassign={onUnassign} />);

	expect(screen.getByText('City Transit Launch')).toBeInTheDocument();
	expect(screen.getByText(/Revision 3/)).toBeInTheDocument();
	expect(screen.getByText('published')).toBeInTheDocument();
	expect(screen.queryByText(/561cd5c9|6b8d4cf0|hidden-id/)).not.toBeInTheDocument();
	fireEvent.click(screen.getByRole('button', { name: 'Unassign' }));
	expect(onUnassign).toHaveBeenCalled();
});
