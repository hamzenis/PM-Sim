import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import DashboardStats from './DashboardStats';
import { taskPoolTotal } from './taskPool';

const state = (week, remainingBudget, tasks) => ({
	week,
	initial_budget: 1000,
	remaining_budget: remainingBudget,
	remaining_working_days: 20 - week * 5,
	tasks_todo: tasks,
});

const history = (week, resultingState) => ({ week_number: week, resulting_state: resultingState });
const renderStats = (current, turns = []) =>
	render(
		<ChakraProvider>
			<DashboardStats state={current} turns={turns} />
		</ChakraProvider>
	);

test('shows first-week values without inventing historical deltas', () => {
	renderStats(state(0, 1000, { easy: 2, medium: 3, hard: 4 }));

	expect(screen.getByText('9')).toBeInTheDocument();
	expect(screen.getByText('$0.00')).toBeInTheDocument();
	expect(screen.queryByText(/since last week/)).not.toBeInTheDocument();
});

test('marks a reduction in remaining tasks as favorable', () => {
	const previous = state(1, 900, { easy: 4, medium: 3, hard: 3 });
	renderStats(state(2, 800, { easy: 2, medium: 2, hard: 2 }), [history(1, previous)]);

	expect(screen.getByText('-4 since last week')).toHaveStyle('color: var(--chakra-colors-green-600)');
});

test('marks returned integration work and other task growth as unfavorable', () => {
	const previous = state(1, 900, { easy: 1, medium: 1, hard: 1 });
	renderStats(state(2, 800, { easy: 3, medium: 2, hard: 2 }), [history(1, previous)]);

	expect(screen.getByText('+4 since last week')).toHaveStyle('color: var(--chakra-colors-red-600)');
});

test('uses the preceding historical state and formats decimal currency', () => {
	const old = state(1, 950, { easy: 8, medium: 8, hard: 8 });
	const previous = state(2, 876.75, { easy: 4, medium: 4, hard: 4 });
	const current = state(3, 751.25, { easy: 3, medium: 3, hard: 3 });
	renderStats(current, [history(1, old), history(2, previous), history(3, current)]);

	expect(screen.getByText('$248.75')).toBeInTheDocument();
	expect(screen.getByText('+$125.50 since last week')).toBeInTheDocument();
	expect(screen.getByText('-3 since last week')).toBeInTheDocument();
});

test('totals task pools with all supported difficulties', () => {
	expect(taskPoolTotal({ easy: 1, medium: 2, hard: 3 })).toBe(6);
	expect(taskPoolTotal()).toBe(0);
});
