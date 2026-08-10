import { render, screen } from '@testing-library/react';
import React from 'react';
import FinalResult from './FinalResult';

test('renders the final score without exposing raw JSON', () => {
	render(
		<FinalResult
			result={{
				outcome: 'submitted',
				accepted_tasks: 12,
				rejected_tasks: 3,
				total_cost: 5000,
				score: { quality: 80, time: 70, budget: 60, total: 70 },
			}}
		/>
	);

	expect(screen.getByText('submitted')).toBeInTheDocument();
	expect(screen.getAllByText('70')).toHaveLength(2);
	expect(screen.getByText('12')).toBeInTheDocument();
});
