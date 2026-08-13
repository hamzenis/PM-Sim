import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import ProjectHealthSummary from './ProjectHealthSummary';

const pool = (count) => ({ easy: count, medium: 0, hard: 0 });
const snapshot = ({ week = 1, elapsed = 5, remaining = 15, budget = 800, tested = 2, employees = [] } = {}) => ({
	week,
	elapsed_working_days: elapsed,
	remaining_working_days: remaining,
	initial_budget: 1000,
	remaining_budget: budget,
	tasks_integration_tested: pool(tested),
	tasks_todo: pool(8),
	tasks_completed: pool(2),
	employees,
});
const turn = (week, state) => ({ week_number: week, resulting_state: state });
const employee = (motivation) => ({ motivation, stress: 0.3, familiarity: 0.5 });
const renderSummary = (state, turns = []) => render(<ChakraProvider><ProjectHealthSummary state={state} turns={turns} /></ChakraProvider>);

test('describes first-week levels without inventing changes', () => {
	renderSummary(snapshot({ employees: [employee(0.7)] }));
	expect(screen.getByText('2 tasks are integration tested')).toBeInTheDocument();
	expect(screen.getByText('Average motivation is 70%')).toBeInTheDocument();
});

test.each([
	[700, '$50 over plan'],
	[900, '$150 under plan'],
])('summarizes budget position versus plan', (budget, phrase) => {
	renderSummary(snapshot({ budget }));
	expect(screen.getByText(`Spending is ${phrase}`)).toBeInTheDocument();
});

test('reports additional integration-tested task progress', () => {
	const first = snapshot({ tested: 2 });
	const current = snapshot({ week: 2, elapsed: 10, remaining: 10, budget: 500, tested: 5 });
	renderSummary(current, [turn(1, first)]);
	expect(screen.getByText('3 additional tasks became integration tested this week')).toBeInTheDocument();
});

test('handles no employee data plainly', () => {
	renderSummary(snapshot());
	expect(screen.getByText('No employee data is available')).toBeInTheDocument();
});

test('moves focus to the corresponding detailed chart', async () => {
	const user = userEvent.setup();
	render(<ChakraProvider><ProjectHealthSummary state={snapshot()} /><section id="task-detail" tabIndex={-1}>Task chart</section></ChakraProvider>);
	await user.click(screen.getByRole('button', { name: 'View tasks details' }));
	expect(screen.getByText('Task chart')).toHaveFocus();
});
