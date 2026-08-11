import { Box, Grid, Heading, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import StatCard from './StatCard';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const formatCurrency = (value) => currency.format(Number(value || 0));
const signedCurrency = (value) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${formatCurrency(Math.abs(value))}`;

const numeric = (value) => {
	const number = Number(value);
	return Number.isFinite(number) ? number : 0;
};

/** Build budget values from the public state snapshots without changing simulation accounting. */
export const selectBudgetTrend = (state, turns = []) => {
	const byWeek = new Map();
	turns.forEach((turn) => {
		if (turn.resulting_state) byWeek.set(numeric(turn.week_number), turn.resulting_state);
	});
	byWeek.set(numeric(state.week), state);

	const snapshots = [...byWeek.entries()]
		.sort(([left], [right]) => left - right)
		.map(([week, snapshot]) => {
			const initialBudget = numeric(snapshot.initial_budget);
			const elapsedDays = numeric(snapshot.elapsed_working_days);
			const scheduledDays = elapsedDays + numeric(snapshot.remaining_working_days);
			const actualCost = initialBudget - numeric(snapshot.remaining_budget);
			const plannedCost = scheduledDays > 0 ? initialBudget * (elapsedDays / scheduledDays) : 0;
			return { week, elapsedDays, scheduledDays, initialBudget, actualCost, plannedCost };
		});
	const current = snapshots.find(({ week }) => week === numeric(state.week)) || snapshots[snapshots.length - 1];
	const currentIndex = snapshots.indexOf(current);
	const previous = currentIndex > 0 ? snapshots[currentIndex - 1] : null;

	return {
		snapshots,
		current,
		remainingBudget: numeric(state.remaining_budget),
		latestSpend: current.actualCost - (previous?.actualCost || 0),
		variance: current.actualCost - current.plannedCost,
	};
};

const BudgetChart = ({ trend }) => {
	const { snapshots, current } = trend;
	const totalDays = Math.max(1, current.scheduledDays);
	const maximum = Math.max(1, current.initialBudget, ...snapshots.map(({ actualCost }) => actualCost));
	const x = (days) => 7 + (Math.min(days, totalDays) / totalDays) * 88;
	const y = (cost) => 90 - (cost / maximum) * 80;
	const actualPoints = snapshots.map(({ elapsedDays, actualCost }) => `${x(elapsedDays)},${y(actualCost)}`).join(' ');
	const plannedPoints = `7,90 95,${y(current.initialBudget)}`;

	return (
		<Box minW={0}>
			<Box as="svg" viewBox="0 0 100 100" width="100%" height="280px" role="img" aria-label="Actual and planned cumulative budget spend">
				<line x1="7" y1={y(current.initialBudget)} x2="95" y2={y(current.initialBudget)} stroke="#E53E3E" strokeWidth="1" strokeDasharray="3 2" aria-label="Initial budget limit" />
				<polyline points={plannedPoints} fill="none" stroke="#718096" strokeWidth="1.5" strokeDasharray="3 2" aria-label="Planned cumulative cost" />
				<polyline points={actualPoints} fill="none" stroke="#3182CE" strokeWidth="2.5" aria-label="Actual cumulative cost" />
				{snapshots.map(({ week, elapsedDays, actualCost }) => (
					<g key={week}>
						<circle cx={x(elapsedDays)} cy={y(actualCost)} r="1.7" fill="#3182CE" />
						<text x={x(elapsedDays)} y="98" fontSize="4" textAnchor="middle">W{week}</text>
					</g>
				))}
			</Box>
			<SimpleGrid columns={{ base: 1, sm: 3 }} spacing={2} mt={2}>
				<Text fontSize="sm" color="blue.600">● Actual cost</Text>
				<Text fontSize="sm" color="gray.600">┄ Planned spend</Text>
				<Text fontSize="sm" color="red.600">┄ Initial budget limit</Text>
			</SimpleGrid>
		</Box>
	);
};

const BudgetTrendChart = ({ state, turns = [], isComplete = false }) => {
	const trend = selectBudgetTrend(state, turns);
	const { current } = trend;
	const completedEarly = isComplete && current.elapsedDays < current.scheduledDays;

	return (
		<Box bg="white" borderRadius="2xl" p={7} mb={8}>
			<Heading size="md" mb={5}>Budget trend</Heading>
			<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 3fr) minmax(280px, 2fr)' }} gap={7}>
				<BudgetChart trend={trend} />
				<Box>
					<SimpleGrid columns={{ base: 1, sm: 2, lg: 1 }} spacing={3}>
						<StatCard label="Current cumulative cost" value={formatCurrency(current.actualCost)} isUnfavorable={current.actualCost > current.initialBudget} />
						<StatCard label="Remaining budget" value={formatCurrency(trend.remainingBudget)} isUnfavorable={trend.remainingBudget < 0} />
						<StatCard label="Spend during latest week" value={formatCurrency(trend.latestSpend)} />
						<StatCard label="Variance from plan" value={signedCurrency(trend.variance)} isUnfavorable={trend.variance > 0} />
					</SimpleGrid>
					{trend.remainingBudget < 0 && <Text mt={4} color="red.600" fontWeight="semibold">Budget exceeded by {formatCurrency(Math.abs(trend.remainingBudget))}.</Text>}
					{completedEarly && <Text mt={4} color="gray.600">Run completed {current.scheduledDays - current.elapsedDays} working days before its scheduled end; the planned line continues to the original end date.</Text>}
				</Box>
			</Grid>
		</Box>
	);
};

export default BudgetTrendChart;
