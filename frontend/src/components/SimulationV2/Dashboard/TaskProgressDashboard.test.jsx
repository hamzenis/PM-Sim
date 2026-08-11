import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import TaskProgressDashboard, { orderedSnapshots } from './TaskProgressDashboard';

const pool = (easy = 0, medium = 0, hard = 0) => ({ easy, medium, hard });
const snapshot = (week, values = {}) => ({
	week,
	tasks_completed: pool(),
	tasks_unit_tested: pool(),
	tasks_integration_tested: pool(),
	known_bugs: pool(),
	tasks_todo: pool(),
	...values,
});
const turn = (week, state, events = []) => ({ week_number: week, resulting_state: state, events });
const renderDashboard = (state, turns = []) => render(<ChakraProvider><TaskProgressDashboard state={state} turns={turns} /></ChakraProvider>);

test('orders sanitized weekly snapshots before plotting them', () => {
	const current = snapshot(3);
	expect(orderedSnapshots(current, [turn(2, snapshot(2)), turn(1, snapshot(1))]).map(({ week }) => week)).toEqual([1, 2, 3]);
});

test('shows current totals and changes from the preceding week', () => {
	const previous = snapshot(1, { tasks_completed: pool(2, 1), tasks_unit_tested: pool(1), tasks_todo: pool(4, 2) });
	const current = snapshot(2, { tasks_completed: pool(3, 2), tasks_unit_tested: pool(2), tasks_integration_tested: pool(1), tasks_todo: pool(3, 1) });
	renderDashboard(current, [turn(1, previous)]);

	expect(screen.getByText('+2 since last week')).toBeInTheDocument();
	expect(screen.getByText('-2 since last week')).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Cumulative task progress by week' })).toBeInTheDocument();
});

test('uses neutral bug wording until discovery evidence is visible', () => {
	const { rerender } = renderDashboard(snapshot(1), [turn(1, snapshot(1), [])]);
	expect(screen.getByText(/only reflects findings visible so far/i)).toBeInTheDocument();

	rerender(<ChakraProvider><TaskProgressDashboard state={snapshot(2)} turns={[turn(1, snapshot(1), [{ kind: 'bugs_discovered', values: pool(1) }])]} /></ChakraProvider>);
	expect(screen.queryByText(/only reflects findings visible so far/i)).not.toBeInTheDocument();
});

test('shows remaining tasks increasing when integration testing returns work', () => {
	const previous = snapshot(1, { tasks_todo: pool(1) });
	const current = snapshot(2, { tasks_todo: pool(3) });
	renderDashboard(current, [turn(1, previous, [{ kind: 'tasks_returned_to_backlog', values: pool(2) }])]);

	expect(screen.getByText('+2 since last week')).toHaveStyle('color: var(--chakra-colors-red-600)');
});
