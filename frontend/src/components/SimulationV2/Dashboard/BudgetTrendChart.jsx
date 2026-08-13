import { Box, Grid, SimpleGrid, Text } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';
import StatCard from './StatCard';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const formatCurrency = (value) => currency.format(Number(value || 0));
const signedCurrency = (value) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${formatCurrency(Math.abs(value))}`;
const compactCurrency = new Intl.NumberFormat('en-US', {
	style: 'currency',
	currency: 'USD',
	notation: 'compact',
	minimumFractionDigits: 0,
	maximumFractionDigits: 1,
});

const numeric = (value) => {
	const number = Number(value);
	return Number.isFinite(number) ? number : 0;
};

const BUDGET_CHART = { ...CHART, left: 18, right: 152 };

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
	const [selectedWeek, setSelectedWeek] = useState(current?.week);
	useEffect(() => setSelectedWeek(current?.week), [current?.week]);
	if (!current || snapshots.length === 0) return <EmptyChart>No budget history is available yet.</EmptyChart>;
	const selected = snapshots.find(({ week }) => week === selectedWeek) || current;
	const totalDays = Math.max(1, current.scheduledDays);
	const maximum = Math.max(1, current.initialBudget, ...snapshots.map(({ actualCost }) => actualCost));
	const getXPosition = (days) => BUDGET_CHART.left + (Math.min(days, totalDays) / totalDays) * (BUDGET_CHART.right - BUDGET_CHART.left);
	const getYPosition = (cost) => BUDGET_CHART.bottom - (cost / maximum) * (BUDGET_CHART.bottom - BUDGET_CHART.top);
	const ticks = [0, maximum / 4, maximum / 2, (maximum * 3) / 4, maximum];
	const actualPoints = snapshots.map(({ elapsedDays, actualCost }) => `${getXPosition(elapsedDays)},${getYPosition(actualCost)}`).join(' ');
	const plannedPoints = `${BUDGET_CHART.left},${BUDGET_CHART.bottom} ${BUDGET_CHART.right},${getYPosition(current.initialBudget)}`;
	const colors = { actual: 'var(--chakra-colors-chart-actual)', planned: 'var(--chakra-colors-chart-planned)', limit: 'var(--chakra-colors-chart-limit)' };
	const selectAdjacent = (index, direction) => {
		const adjacent = snapshots[Math.max(0, Math.min(snapshots.length - 1, index + direction))];
		setSelectedWeek(adjacent.week);
	};

	return (
		<Box minW={0}>
		<Box bg="blackAlpha.50" borderWidth="1px" borderColor="border.default" borderRadius="lg" px={4} py={3} mb={3} aria-live="polite" data-testid="budget-point-detail">
			<Text fontWeight="bold">Week {selected.week}</Text>
			<Text fontSize="sm">Actual cost: <strong>{formatCurrency(selected.actualCost)}</strong> · Planned cost: <strong>{formatCurrency(selected.plannedCost)}</strong> · Variance: <strong>{signedCurrency(selected.actualCost - selected.plannedCost)}</strong></Text>
		</Box>
			<Box as="svg" viewBox="0 0 156 104" width="100%" height={{ base: '210px', md: '280px' }} role="group" aria-label="Actual and planned cumulative budget spend">
				<desc>Actual cumulative cost is compared with planned spending and the initial budget limit by week.</desc>
				<ChartGrid ticks={ticks} getYPosition={getYPosition} formatTick={(value) => compactCurrency.format(value)} xLabel="Project week" yLabel="Cumulative cost (USD)" chart={BUDGET_CHART} yLabelX={2} />
				<line x1={BUDGET_CHART.left} y1={getYPosition(current.initialBudget)} x2={BUDGET_CHART.right} y2={getYPosition(current.initialBudget)} stroke={colors.limit} strokeWidth="1.2" strokeDasharray="1 2" />
				<polyline points={plannedPoints} fill="none" stroke={colors.planned} strokeWidth="1.5" strokeDasharray="3 2" />
				<polyline points={actualPoints} fill="none" stroke={colors.actual} strokeWidth="2.5" />
				{snapshots.map(({ week, elapsedDays, actualCost, plannedCost }, index) => (
					<g key={week} role="button" tabIndex="0" aria-label={`Week ${week}: actual cost ${formatCurrency(actualCost)}, planned cost ${formatCurrency(plannedCost)}, variance ${signedCurrency(actualCost - plannedCost)}`} onMouseEnter={() => setSelectedWeek(week)} onClick={() => setSelectedWeek(week)} onFocus={() => setSelectedWeek(week)} onKeyDown={(event) => {
						if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelectedWeek(week); }
						if (event.key === 'ArrowLeft') { event.preventDefault(); selectAdjacent(index, -1); }
						if (event.key === 'ArrowRight') { event.preventDefault(); selectAdjacent(index, 1); }
					}}>
						<circle cx={getXPosition(elapsedDays)} cy={getYPosition(actualCost)} r={week === current.week ? '3.1' : '2.5'} fill="white" stroke={colors.actual} strokeWidth={week === current.week ? '1.5' : '1.1'} />
						{week === selected.week && <circle cx={getXPosition(elapsedDays)} cy={getYPosition(actualCost)} r="4.5" fill="none" stroke={colors.actual} strokeWidth="0.7" />}
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
	const exceeded = trend.remainingBudget < 0;
	const summary = exceeded
		? `Budget exceeded by ${formatCurrency(Math.abs(trend.remainingBudget))}`
		: `Spending is ${formatCurrency(Math.abs(trend.variance))} ${trend.variance > 0 ? 'over' : 'under'} plan`;
	const summaryColor = exceeded ? 'red.700' : trend.variance > 0 ? 'orange.700' : 'green.700';

	return (
		<ChartCard title="Budget trend" description="See cumulative project spending compared with the planned pace and original budget.">
			<Text color={summaryColor} fontSize={{ base: 'lg', md: 'xl' }} fontWeight="bold" mb={5}>{summary}</Text>
			<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 7fr) minmax(240px, 3fr)' }} gap={7}>
				<BudgetChart trend={trend} />
				<Box>
					<SimpleGrid columns={{ base: 1, sm: 2, lg: 1 }} spacing={3}>
						<StatCard label="Current cumulative cost" value={formatCurrency(current.actualCost)} isUnfavorable={current.actualCost > current.initialBudget} />
						<StatCard label="Remaining budget" value={formatCurrency(trend.remainingBudget)} isUnfavorable={trend.remainingBudget < 0} />
						<StatCard label="Spend during latest week" value={formatCurrency(trend.latestSpend)} />
						<StatCard label="Variance from plan" value={signedCurrency(trend.variance)} isUnfavorable={trend.variance > 0} />
					</SimpleGrid>
					{completedEarly && <Text mt={4} color="gray.600">Run completed {current.scheduledDays - current.elapsedDays} working days before its scheduled end; the planned line continues to the original end date.</Text>}
				</Box>
			</Grid>
		</ChartCard>
	);
};

export default BudgetTrendChart;
