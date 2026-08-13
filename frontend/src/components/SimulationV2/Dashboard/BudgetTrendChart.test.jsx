import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
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

	expect(screen.getByText('Budget exceeded by $100.00.')).toBeInTheDocument();
	expect(screen.getByText(/completed 10 working days before/i)).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Actual and planned cumulative budget spend' })).toBeInTheDocument();
	expect(screen.getByText('Project week')).toBeInTheDocument();
	expect(screen.getByText('Cumulative cost (USD)')).toBeInTheDocument();
	expect(screen.getByLabelText('Chart legend')).toHaveTextContent(/Actual cost.*Planned spend.*Initial budget limit/);
	expect(screen.getByText('Budget trend data')).toBeInTheDocument();
});
