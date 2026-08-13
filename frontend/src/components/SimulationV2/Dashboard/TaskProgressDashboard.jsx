import { Box, Grid, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';
import StatCard from './StatCard';
import { taskPoolTotal } from './taskPool';

const series = [
	{ key: 'tasks_completed', label: 'Completed', color: 'var(--chakra-colors-chart-completed)', marker: 'circle' },
	{ key: 'tasks_unit_tested', label: 'Unit tested', color: 'var(--chakra-colors-chart-unitTested)', marker: 'square' },
	{ key: 'tasks_integration_tested', label: 'Integration tested', color: 'var(--chakra-colors-chart-integrationTested)', dashed: true },
	{ key: 'known_bugs', label: 'Known bugs', color: 'var(--chakra-colors-chart-bugs)', dashed: true },
];

export const orderedSnapshots = (state, turns = []) => {
	const byWeek = new Map();
	turns.forEach((turn) => {
		if (turn.resulting_state) byWeek.set(Number(turn.week_number), turn.resulting_state);
	});
	byWeek.set(Number(state.week), state);
	return [...byWeek.entries()]
		.sort(([left], [right]) => left - right)
		.map(([week, snapshot]) => ({ week, snapshot }));
};

const deltaText = (current, previous) => {
	if (previous === undefined) return null;
	const change = current - previous;
	return `${change > 0 ? '+' : ''}${change}`;
};

const ProgressChart = ({ snapshots }) => {
	if (snapshots.length === 0) return <EmptyChart>No task progress history is available yet.</EmptyChart>;
	const values = snapshots.flatMap(({ snapshot }) => series.map(({ key }) => taskPoolTotal(snapshot[key])));
	const maximum = Math.max(1, ...values);
	const getXPosition = (index) => (snapshots.length === 1 ? 55 : CHART.left + (index / (snapshots.length - 1)) * (CHART.right - CHART.left));
	const getYPosition = (value) => CHART.bottom - (value / maximum) * (CHART.bottom - CHART.top);

	return (
		<Box minW={0}>
		<Box as="svg" viewBox="0 0 100 104" width="100%" height={{ base: '210px', md: '280px' }} role="img" aria-label="Cumulative task progress by week">
			<desc>Completed, unit-tested, integration-tested, and known-bug task totals for each project week.</desc>
			<ChartGrid ticks={[0, maximum / 2, maximum]} getYPosition={getYPosition} formatTick={(value) => Math.round(value).toLocaleString()} xLabel="Project week" yLabel="Task count" />
			{series.map(({ key, color, dashed }) => (
				<polyline
					key={key}
					fill="none"
					stroke={color}
					strokeWidth="2"
					strokeDasharray={dashed ? '4 3' : undefined}
					points={snapshots.map(({ snapshot }, index) => `${getXPosition(index)},${getYPosition(taskPoolTotal(snapshot[key]))}`).join(' ')}
				/>
			))}
			{snapshots.map(({ week }, index) => (
				<text key={week} x={getXPosition(index)} y="90" fontSize="3.5" textAnchor="middle">W{week}</text>
			))}
		</Box>
		<ChartLegend items={series} />
		<ChartDataTable caption="Task progress trend data" columns={['Week', ...series.map(({ label }) => label)]} rows={snapshots.map(({ week, snapshot }) => [`Week ${week}`, ...series.map(({ key }) => taskPoolTotal(snapshot[key]))])} />
		</Box>
	);
};

const TaskProgressDashboard = ({ state, turns = [] }) => {
	const snapshots = orderedSnapshots(state, turns);
	const current = state;
	const previous = snapshots.find(({ week }) => week === Number(state.week) - 1)?.snapshot;
	const bugDiscoverySeen = turns.some((turn) =>
		(turn.events || []).some((event) => event.kind === 'bugs_discovered' && taskPoolTotal(event.values) > 0)
	) || snapshots.some(({ snapshot }) => taskPoolTotal(snapshot.known_bugs) > 0);
	const metrics = [
		...series.map(({ key, label }) => ({ key, label, favorable: key !== 'known_bugs' })),
		{ key: 'tasks_todo', label: 'Remaining tasks', favorable: false },
	];

	return (
		<ChartCard title="Task progress" description="Track cumulative development, testing, and known-bug totals from week to week.">
			<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 3fr) minmax(260px, 2fr)' }} gap={7}>
				<ProgressChart snapshots={snapshots} />
				<SimpleGrid columns={{ base: 1, sm: 2, lg: 1 }} spacing={3}>
					{metrics.map(({ key, label, favorable }) => {
						const total = taskPoolTotal(current[key]);
						const change = deltaText(total, previous && taskPoolTotal(previous[key]));
						return <StatCard key={key} label={label} value={total} delta={change} deltaIsFavorable={change && (favorable ? Number(change) >= 0 : Number(change) <= 0)} />;
					})}
					{!bugDiscoverySeen && <Text color="gray.600" fontSize="sm">No bugs have been discovered through testing yet; the known-bug count only reflects findings visible so far.</Text>}
				</SimpleGrid>
			</Grid>
		</ChartCard>
	);
};

export default TaskProgressDashboard;
