import { Box, Grid, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';
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
	if (!current || snapshots.length === 0) return <EmptyChart>No budget history is available yet.</EmptyChart>;
	const totalDays = Math.max(1, current.scheduledDays);
	const maximum = Math.max(1, current.initialBudget, ...snapshots.map(({ actualCost }) => actualCost));
	const getXPosition = (days) => CHART.left + (Math.min(days, totalDays) / totalDays) * (CHART.right - CHART.left);
	const getYPosition = (cost) => CHART.bottom - (cost / maximum) * (CHART.bottom - CHART.top);
	const ticks = [0, maximum / 2, maximum];
	const actualPoints = snapshots.map(({ elapsedDays, actualCost }) => `${getXPosition(elapsedDays)},${getYPosition(actualCost)}`).join(' ');
	const plannedPoints = `${CHART.left},${CHART.bottom} ${CHART.right},${getYPosition(current.initialBudget)}`;
	const colors = { actual: 'var(--chakra-colors-chart-actual)', planned: 'var(--chakra-colors-chart-planned)', limit: 'var(--chakra-colors-chart-limit)' };

	return (
		<Box minW={0}>
			<Box as="svg" viewBox="0 0 100 104" width="100%" height={{ base: '210px', md: '280px' }} role="img" aria-label="Actual and planned cumulative budget spend">
				<desc>Actual cumulative cost is compared with planned spending and the initial budget limit by week.</desc>
				<ChartGrid ticks={ticks} getYPosition={getYPosition} formatTick={(value) => `$${Math.round(value).toLocaleString()}`} xLabel="Project week" yLabel="Cumulative cost (USD)" />
				<line x1={CHART.left} y1={getYPosition(current.initialBudget)} x2={CHART.right} y2={getYPosition(current.initialBudget)} stroke={colors.limit} strokeWidth="1" strokeDasharray="3 2" />
				<polyline points={plannedPoints} fill="none" stroke={colors.planned} strokeWidth="1.5" strokeDasharray="3 2" />
				<polyline points={actualPoints} fill="none" stroke={colors.actual} strokeWidth="2.5" />
				{snapshots.map(({ week, elapsedDays, actualCost }) => (
					<g key={week}>
						<circle cx={getXPosition(elapsedDays)} cy={getYPosition(actualCost)} r="1.7" fill={colors.actual} />
						<text x={getXPosition(elapsedDays)} y="90" fontSize="3.5" textAnchor="middle">W{week}</text>
					</g>
				))}
			</Box>
			<ChartLegend items={[{ key: 'actual', label: 'Actual cost', color: colors.actual }, { key: 'planned', label: 'Planned spend', color: colors.planned, dashed: true }, { key: 'limit', label: 'Initial budget limit', color: colors.limit, dashed: true }]} />
			<ChartDataTable caption="Budget trend data" columns={['Week', 'Actual cost', 'Planned cost']} rows={snapshots.map(({ week, actualCost, plannedCost }) => [`Week ${week}`, formatCurrency(actualCost), formatCurrency(plannedCost)])} />
		</Box>
	);
};

const BudgetTrendChart = ({ state, turns = [], isComplete = false }) => {
	const trend = selectBudgetTrend(state, turns);
	const { current } = trend;
	const completedEarly = isComplete && current.elapsedDays < current.scheduledDays;

	return (
		<ChartCard title="Budget trend" description="See cumulative project spending compared with the planned pace and original budget.">
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
		</ChartCard>
	);
};

export default BudgetTrendChart;
