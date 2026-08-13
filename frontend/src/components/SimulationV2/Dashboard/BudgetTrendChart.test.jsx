import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import BudgetTrendChart, { selectBudgetTrend } from './BudgetTrendChart';

const snapshot = (week, elapsed, remainingDays, remainingBudget) => ({
	week,
	elapsed_working_days: elapsed,
	remaining_working_days: remainingDays,
	initial_budget: 1000,
	remaining_budget: remainingBudget,
});
const turn = (week, resultingState) => ({ week_number: week, resulting_state: resultingState });

test('selects actual, linear planned, latest-week, and variance values from weekly snapshots', () => {
	const current = snapshot(2, 10, 10, 400);
	const trend = selectBudgetTrend(current, [turn(1, snapshot(1, 5, 15, 750))]);

	expect(trend.snapshots.map(({ actualCost, plannedCost }) => [actualCost, plannedCost])).toEqual([[250, 250], [600, 500]]);
	expect(trend.latestSpend).toBe(350);
	expect(trend.variance).toBe(100);
});

test('highlights an overrun and explains an early completed run', () => {
	const current = snapshot(2, 10, 10, -100);
	render(<ChakraProvider><BudgetTrendChart state={current} turns={[turn(1, snapshot(1, 5, 15, 500))]} isComplete /></ChakraProvider>);

	expect(screen.getByText('Budget exceeded by $100.00')).toBeInTheDocument();
	expect(screen.getByText(/completed 10 working days before/i)).toBeInTheDocument();
	expect(screen.getByRole('group', { name: 'Actual and planned cumulative budget spend' })).toBeInTheDocument();
	expect(screen.getByText('Project week')).toBeInTheDocument();
	expect(screen.getByText('Cumulative cost (USD)')).toBeInTheDocument();
	expect(screen.getByLabelText('Chart legend')).toHaveTextContent(/Actual cost.*Planned spend.*Initial budget limit/);
	expect(screen.getByText('Budget trend data')).toBeInTheDocument();
});

test('shows compact currency ticks and labeled weeks', () => {
	const current = { ...snapshot(2, 10, 10, 25000), initial_budget: 50000 };
	const first = { ...snapshot(1, 5, 15, 37500), initial_budget: 50000 };
	render(<ChakraProvider><BudgetTrendChart state={current} turns={[turn(1, first)]} /></ChakraProvider>);

	expect(screen.getByText('$0')).toBeInTheDocument();
	expect(screen.getByText('$25K')).toBeInTheDocument();
	expect(screen.getByText('$50K')).toBeInTheDocument();
	expect(screen.getByText('W1')).toBeInTheDocument();
	expect(screen.getByText('W2')).toBeInTheDocument();
});

test('selects and fully formats the latest point by default', () => {
	const current = { ...snapshot(2, 10, 10, 399.5), initial_budget: 1000.25 };
	render(<ChakraProvider><BudgetTrendChart state={current} turns={[]} /></ChakraProvider>);

	const detail = screen.getByTestId('budget-point-detail');
	expect(detail).toHaveTextContent('Week 2');
	expect(detail).toHaveTextContent('Actual cost: $600.75');
	expect(detail).toHaveTextContent('Planned cost: $500.13');
	expect(detail).toHaveTextContent('Variance: +$100.63');
});

test('summarizes spending under plan', () => {
	render(<ChakraProvider><BudgetTrendChart state={snapshot(2, 10, 10, 600)} /></ChakraProvider>);
	expect(screen.getByText('Spending is $100.00 under plan')).toBeInTheDocument();
});

test('summarizes spending over plan', () => {
	render(<ChakraProvider><BudgetTrendChart state={snapshot(2, 10, 10, 400)} /></ChakraProvider>);
	expect(screen.getByText('Spending is $100.00 over plan')).toBeInTheDocument();
});

test('gives budget exceeded status priority over plan variance', () => {
	render(<ChakraProvider><BudgetTrendChart state={snapshot(2, 10, 10, -25.5)} /></ChakraProvider>);
	expect(screen.getByText('Budget exceeded by $25.50')).toBeInTheDocument();
});

test('lets keyboard users focus and select recorded data points', async () => {
	const user = userEvent.setup();
	render(<ChakraProvider><BudgetTrendChart state={snapshot(2, 10, 10, 400)} turns={[turn(1, snapshot(1, 5, 15, 750))]} /></ChakraProvider>);

	const firstPoint = screen.getByRole('button', { name: /Week 1: actual cost/i });
	await user.tab();
	expect(firstPoint).toHaveFocus();
	expect(screen.getByTestId('budget-point-detail')).toHaveTextContent('Week 1');
	await user.keyboard('{ArrowRight}');
	expect(screen.getByTestId('budget-point-detail')).toHaveTextContent('Week 2');
});

test('renders and selects a single initial-week data point', () => {
	render(<ChakraProvider><BudgetTrendChart state={snapshot(0, 0, 20, 1000)} /></ChakraProvider>);

	expect(screen.getAllByRole('button', { name: /Week 0:/i })).toHaveLength(1);
	expect(screen.getByTestId('budget-point-detail')).toHaveTextContent('Week 0');
	expect(screen.getByText('Spending is $0.00 under plan')).toBeInTheDocument();
});
