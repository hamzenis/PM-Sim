import { render, screen } from '@testing-library/react';
import React from 'react';
import FinalResult from './FinalResult';

test('renders scores, timing, currency, and task acceptance explanation', () => {
	render(
		<FinalResult
			result={{
				outcome: 'submitted',
				accepted_tasks: 12,
				rejected_tasks: 3,
				elapsed_working_days: 15,
				scheduled_working_days: 20,
				total_cost: 5000,
				remaining_budget: 1000,
				score: { quality: 80, time: 70, budget: 60, total: 70 },
			}}
		/>
	);

	expect(screen.getByText('submitted')).toBeInTheDocument();
	expect(screen.getByText('70/100')).toBeInTheDocument();
	expect(screen.getByText('70 pts')).toBeInTheDocument();
	expect(screen.getByText('12')).toBeInTheDocument();
	expect(screen.getByText('15 days')).toBeInTheDocument();
	expect(screen.getByText('20 days')).toBeInTheDocument();
	expect(screen.getByText('$5,000.00')).toBeInTheDocument();
	expect(screen.getByText('+$1,000.00')).toBeInTheDocument();
	expect(screen.getByText(/Accepted tasks are integration tested/)).toBeInTheDocument();
});

test('explains a budget overrun', () => {
	render(<FinalResult result={{ remaining_budget: -250, score: {} }} />);
	expect(screen.getByText('−$250.00')).toBeInTheDocument();
	expect(screen.getByText('The project finished $250.00 over budget.')).toBeInTheDocument();
});

test('renders missing optional result data safely', () => {
	render(<FinalResult result={{ outcome: 'submitted' }} />);
	expect(screen.getAllByText('—')).toHaveLength(10);
	expect(screen.queryByText(/under budget|over budget/)).not.toBeInTheDocument();
});
