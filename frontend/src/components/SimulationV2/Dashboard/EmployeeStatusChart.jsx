import { Box, Grid, SimpleGrid, Stat, StatHelpText, StatLabel, StatNumber } from '@chakra-ui/react';
import React from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';

const metrics = [
	{ key: 'stress', label: 'Stress', color: 'var(--chakra-colors-chart-stress)', marker: 'circle' },
	{ key: 'motivation', label: 'Motivation', color: 'var(--chakra-colors-chart-motivation)', marker: 'square' },
	{ key: 'familiarity', label: 'Familiarity', color: 'var(--chakra-colors-chart-familiarity)', dashed: true },
];

const finiteNumber = (value) => {
	const number = Number(value);
	return Number.isFinite(number) ? number : 0;
};

export const toPercentage = (value) => finiteNumber(value) * 100;

/**
 * Select per-week team averages from sanitized state snapshots. Each week's
 * population is independent because employees can be hired or dismissed.
 */
export const selectEmployeeStatusTrend = (state, turns = []) => {
	const byWeek = new Map();
	turns.forEach((turn) => {
		if (turn.resulting_state) byWeek.set(Number(turn.week_number), turn.resulting_state);
	});
	byWeek.set(Number(state.week), state);

	const snapshots = [...byWeek.entries()]
		.sort(([left], [right]) => left - right)
		.map(([week, snapshot]) => {
			const employees = Array.isArray(snapshot.employees) ? snapshot.employees : [];
			const averages = Object.fromEntries(metrics.map(({ key }) => [
				key,
				employees.length === 0
					? null
					: employees.reduce((total, employee) => total + finiteNumber(employee[key]), 0) / employees.length,
			]));
			return { week, employeeCount: employees.length, ...averages };
		});
	const currentIndex = snapshots.findIndex(({ week }) => week === Number(state.week));

	return {
		snapshots,
		current: snapshots[currentIndex],
		previous: currentIndex > 0 ? snapshots[currentIndex - 1] : null,
	};
};

const formatPercentage = (value) => `${toPercentage(value).toFixed(1)}%`;
const formatChange = (current, previous) => {
	if (previous === null || previous === undefined) return null;
	const change = toPercentage(current - previous);
	return `${change > 0 ? '+' : change < 0 ? '−' : ''}${Math.abs(change).toFixed(1)} pp`;
};

const TrendChart = ({ snapshots }) => {
	if (snapshots.length === 0) return <EmptyChart>No employee status history is available yet.</EmptyChart>;
	const getXPosition = (index) => (snapshots.length === 1 ? 55 : CHART.left + (index / (snapshots.length - 1)) * (CHART.right - CHART.left));
	const getYPosition = (value) => CHART.bottom - toPercentage(value) / 100 * (CHART.bottom - CHART.top);

	return (
		<Box minW={0}>
			<Box as="svg" viewBox="0 0 100 104" width="100%" height={{ base: '210px', md: '280px' }} role="img" aria-label="Weekly team-average employee status percentages">
				<desc>Stress, motivation, and familiarity team averages shown as percentages for each project week.</desc>
				<ChartGrid ticks={[0, 0.5, 1]} getYPosition={getYPosition} formatTick={(value) => `${toPercentage(value)}%`} xLabel="Project week" yLabel="Team average (%)" />
				{metrics.map(({ key, color, dashed }) => {
					const points = snapshots
						.map((snapshot, index) => snapshot[key] === null ? null : `${getXPosition(index)},${getYPosition(snapshot[key])}`)
						.filter(Boolean)
						.join(' ');
					return points && <polyline key={key} points={points} fill="none" stroke={color} strokeWidth="2" strokeDasharray={dashed ? '4 3' : undefined} />;
				})}
				{snapshots.map(({ week }, index) => <text key={week} x={getXPosition(index)} y="90" fontSize="3.5" textAnchor="middle">W{week}</text>)}
			</Box>
			<ChartLegend items={metrics} />
			<ChartDataTable caption="Employee status trend data" columns={['Week', ...metrics.map(({ label }) => label)]} rows={snapshots.map((snapshot) => [`Week ${snapshot.week}`, ...metrics.map(({ key }) => snapshot[key] === null ? 'No employees' : formatPercentage(snapshot[key]))])} />
		</Box>
	);
};

const EmployeeStatusChart = ({ state, turns = [] }) => {
	const trend = selectEmployeeStatusTrend(state, turns);
	const { current, previous } = trend;

	return (
		<ChartCard title="Employee status" description="These are per-week team averages. The employees included can change through hiring and dismissal.">
			{current.employeeCount === 0 ? (
				<EmptyChart>No employees</EmptyChart>
			) : (
				<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 3fr) minmax(260px, 2fr)' }} gap={7}>
					<TrendChart snapshots={trend.snapshots} />
					<SimpleGrid columns={{ base: 1, sm: 3, lg: 1 }} spacing={3}>
						{metrics.map(({ key, label }) => {
							const change = formatChange(current[key], previous?.[key]);
							return (
								<Box key={key} borderRadius="xl" p={5}>
									<Stat>
										<StatLabel>{label}</StatLabel>
										<StatNumber>{formatPercentage(current[key])}</StatNumber>
										{change !== null && <StatHelpText mb={0}>{change} since last week</StatHelpText>}
									</Stat>
								</Box>
							);
						})}
					</SimpleGrid>
				</Grid>
			)}
		</ChartCard>
	);
};

export default EmployeeStatusChart;
