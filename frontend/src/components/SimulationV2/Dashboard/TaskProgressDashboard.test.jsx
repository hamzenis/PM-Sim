import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import TaskProgressDashboard, { orderedSnapshots } from './TaskProgressDashboard';
import { taskPoolTotal } from './taskPool';

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

test('preserves task-pool selector totals across every state value', () => {
	expect(taskPoolTotal(pool(2, 3, 4))).toBe(9);
	expect(taskPoolTotal()).toBe(0);
});

test('appends an initial state and replaces a persisted latest week with the current state', () => {
	const initial = snapshot(0);
	expect(orderedSnapshots(initial, []).map(({ week }) => week)).toEqual([0]);

	const persistedLatest = snapshot(2, { tasks_completed: pool(1) });
	const current = snapshot(2, { tasks_completed: pool(3) });
	const snapshots = orderedSnapshots(current, [turn(1, snapshot(1)), turn(2, persistedLatest)]);
	expect(snapshots.map(({ week }) => week)).toEqual([1, 2]);
	expect(snapshots[1].snapshot).toBe(current);
});

test('shows current totals and changes from the preceding week', () => {
	const previous = snapshot(1, { tasks_completed: pool(2, 1), tasks_unit_tested: pool(1), tasks_todo: pool(4, 2) });
	const current = snapshot(2, { tasks_completed: pool(3, 2), tasks_unit_tested: pool(2), tasks_integration_tested: pool(1), tasks_todo: pool(3, 1) });
	renderDashboard(current, [turn(1, previous)]);

	expect(screen.getByText('+2 since last week')).toBeInTheDocument();
	expect(screen.getByText('-2 since last week')).toBeInTheDocument();
	expect(screen.getByRole('group', { name: 'Cumulative task progress by week' })).toBeInTheDocument();
	expect(screen.getByText('Project week')).toBeInTheDocument();
	expect(screen.getByText('Task count')).toBeInTheDocument();
	expect(screen.getByLabelText('Chart legend')).toHaveTextContent(/Completed.*Unit tested.*Integration tested.*Known bugs/);
	expect(screen.getByText('Task progress trend data')).toBeInTheDocument();
	expect(screen.getByText('1 of 9')).toBeInTheDocument();
	expect(screen.getByText('project tasks are integration tested')).toBeInTheDocument();
});

test('exposes every metric for each point and updates details with keyboard focus', async () => {
	const user = userEvent.setup();
	const previous = snapshot(0, {
		tasks_completed: pool(2), tasks_unit_tested: pool(1), tasks_integration_tested: pool(), known_bugs: pool(1), tasks_todo: pool(8),
	});
	const current = snapshot(1, {
		tasks_completed: pool(4), tasks_unit_tested: pool(3), tasks_integration_tested: pool(2), known_bugs: pool(1), tasks_todo: pool(6),
	});
	renderDashboard(current, [turn(0, previous)]);

	const firstPoint = screen.getByRole('button', { name: /Week 0: Completed 2, Unit tested 1, Integration tested 0, Known bugs 1, Remaining tasks 8/ });
	expect(firstPoint).toHaveAttribute('tabindex', '0');
	await user.tab();
	expect(firstPoint).toHaveFocus();
	expect(screen.getByText('Week 0 details')).toBeInTheDocument();
	expect(screen.getByText('Remaining tasks:', { exact: false }).closest('p')).toHaveTextContent('Remaining tasks: 8');
});

test('selects a week by clicking its visible chart dots', async () => {
	const user = userEvent.setup();
	const previous = snapshot(0, { tasks_completed: pool(2), tasks_todo: pool(8) });
	const current = snapshot(1, { tasks_completed: pool(4), tasks_todo: pool(6) });
	renderDashboard(current, [turn(0, previous)]);

	const weekZeroDots = screen.getByRole('button', { name: /Week 0: Completed 2/ });
	await user.click(weekZeroDots.querySelector('circle[fill="transparent"]'));
	expect(screen.getByText('Week 0 details')).toBeInTheDocument();
});

test('uses neutral bug wording until discovery evidence is visible', () => {
	const { rerender } = renderDashboard(snapshot(1), [turn(1, snapshot(1), [])]);
	expect(screen.getByText(/only reflects findings visible so far/i)).toBeInTheDocument();

	rerender(<ChakraProvider><TaskProgressDashboard state={snapshot(2)} turns={[turn(1, snapshot(1), [{ kind: 'bugs_discovered', values: pool(1) }])]} /></ChakraProvider>);
	expect(screen.queryByText(/only reflects findings visible so far/i)).not.toBeInTheDocument();
	expect(screen.queryByText(/undiscovered bugs? [1-9]/i)).not.toBeInTheDocument();
});

test('annotates the event week when integration testing returns work to the backlog', () => {
	const previous = snapshot(1, { tasks_todo: pool(1) });
	const current = snapshot(2, { tasks_todo: pool(3) });
	renderDashboard(current, [turn(1, previous), turn(2, current, [{ kind: 'tasks_returned_to_backlog', values: pool(2) }])]);

	expect(screen.getByText('+2 since last week')).toHaveStyle('color: var(--chakra-colors-red-600)');
	expect(screen.getByText(/Week 2 backlog return:/).closest('p')).toHaveTextContent('Remaining tasks increased as 2 tasks were returned from integration testing for more work.');
	expect(screen.queryByText(/Week 1 backlog return:/)).not.toBeInTheDocument();
});

test('handles all work integration tested with overlapping progress series', () => {
	const complete = snapshot(3, {
		tasks_completed: pool(10), tasks_unit_tested: pool(10), tasks_integration_tested: pool(10), tasks_todo: pool(),
	});
	renderDashboard(complete);
	expect(screen.getByText('10 of 10')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: /Completed 10, Unit tested 10, Integration tested 10.*Remaining tasks 0/ })).toBeInTheDocument();
});
