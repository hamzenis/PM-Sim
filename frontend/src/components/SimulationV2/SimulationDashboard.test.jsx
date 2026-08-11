import { render, screen } from '@testing-library/react';
import React from 'react';
import SimulationDashboard, { dashboardPoint } from './SimulationDashboard';

const state = {
	week: 2,
	initial_budget: 10000,
	remaining_budget: 7500,
	remaining_working_days: 20,
	tasks_todo: { easy: 2, medium: 3, hard: 4 },
	tasks_completed: { easy: 5, medium: 2, hard: 1 },
	tasks_unit_tested: { easy: 4, medium: 1, hard: 1 },
	tasks_integration_tested: { easy: 3, medium: 1, hard: 0 },
	known_bugs: { easy: 1, medium: 1, hard: 0 },
	employees: [
		{ motivation: 0.8, stress: 0.2, familiarity: 0.4 },
		{ motivation: 0.6, stress: 0.4, familiarity: 0.6 },
	],
};

test('converts simulation state into dashboard metrics', () => {
	const point = dashboardPoint(state);
	expect(point).toMatchObject({
		todo: 9,
		completed: 8,
		unitTested: 6,
		integrationTested: 4,
		knownBugs: 2,
		budgetSpent: 2500,
		motivation: 70,
		familiarity: 50,
	});
	expect(point.stress).toBeCloseTo(30);
});

test('shows task, budget, and employee charts with current counters', () => {
	render(<SimulationDashboard state={state} turns={[{ state }]} />);

	expect(screen.getByText('Tasks to do')).toBeInTheDocument();
	expect(screen.getByText('Known bugs')).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Task progress and known bugs line chart' })).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Budget line chart' })).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Employee status line chart' })).toBeInTheDocument();
	expect(screen.getByText('70%')).toBeInTheDocument();
});
