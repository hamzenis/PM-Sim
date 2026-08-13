import { Box, Grid, HStack, SimpleGrid, Text, Wrap, WrapItem } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';
import StatCard from './StatCard';
import { taskPoolTotal } from './taskPool';

const series = [
	{ key: 'tasks_completed', label: 'Completed', color: 'var(--chakra-colors-chart-completed)', marker: 'circle', strokeWidth: 1.8 },
	{ key: 'tasks_unit_tested', label: 'Unit tested', color: 'var(--chakra-colors-chart-unitTested)', marker: 'square', dasharray: '1 2.5', strokeWidth: 2 },
	{ key: 'tasks_integration_tested', label: 'Integration tested', color: 'var(--chakra-colors-chart-integrationTested)', marker: 'circle', strokeWidth: 3 },
	{ key: 'known_bugs', label: 'Known bugs', color: 'var(--chakra-colors-chart-bugs)', marker: 'square', dasharray: '5 2', strokeWidth: 2.4 },
];

const detailMetrics = [...series, { key: 'tasks_todo', label: 'Remaining tasks' }];
const TASK_CHART = { ...CHART, left: 18, right: 152 };

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

/** Select the task totals used by both the compact summary and detailed chart. */
export const selectTaskProgress = (state, turns = []) => {
	const snapshots = orderedSnapshots(state, turns);
	const current = state;
	const previous = snapshots.find(({ week }) => week === Number(state.week) - 1)?.snapshot;
	return {
		snapshots,
		current,
		previous,
		integrationTested: taskPoolTotal(current.tasks_integration_tested),
		previousIntegrationTested: previous === undefined ? null : taskPoolTotal(previous.tasks_integration_tested),
		projectTasks: taskPoolTotal(current.tasks_todo) + taskPoolTotal(current.tasks_completed),
	};
};

const deltaText = (current, previous) => {
	if (previous === undefined) return null;
	const change = current - previous;
	return `${change > 0 ? '+' : ''}${change}`;
};

const pointDetail = ({ week, snapshot }) =>
	`Week ${week}: ${detailMetrics.map(({ key, label }) => `${label} ${taskPoolTotal(snapshot[key])}`).join(', ')}`;

const ProgressChart = ({ snapshots }) => {
	const [selectedIndex, setSelectedIndex] = useState(Math.max(0, snapshots.length - 1));
	useEffect(() => setSelectedIndex(Math.max(0, snapshots.length - 1)), [snapshots.length]);
	if (snapshots.length === 0) return <EmptyChart>No task progress history is available yet.</EmptyChart>;
	const values = snapshots.flatMap(({ snapshot }) => series.map(({ key }) => taskPoolTotal(snapshot[key])));
	const maximum = Math.max(1, ...values);
	const getXPosition = (index) => (snapshots.length === 1 ? (TASK_CHART.left + TASK_CHART.right) / 2 : TASK_CHART.left + (index / (snapshots.length - 1)) * (TASK_CHART.right - TASK_CHART.left));
	const getYPosition = (value) => TASK_CHART.bottom - (value / maximum) * (TASK_CHART.bottom - TASK_CHART.top);
	const selected = snapshots[Math.min(selectedIndex, snapshots.length - 1)];
	const latestIndex = snapshots.length - 1;

	return (
		<Box minW={0}>
		<Box as="svg" viewBox="0 0 156 104" width="100%" height={{ base: '210px', md: '280px' }} role="group" aria-label="Cumulative task progress by week">
			<desc>Completed, unit-tested, integration-tested, and known-bug task totals for each project week.</desc>
			<ChartGrid ticks={[0, maximum / 2, maximum]} getYPosition={getYPosition} formatTick={(value) => Math.round(value).toLocaleString()} xLabel="Project week" yLabel="Task count" chart={TASK_CHART} yLabelX={2} />
			<line x1={getXPosition(latestIndex)} y1={TASK_CHART.top} x2={getXPosition(latestIndex)} y2={TASK_CHART.bottom} stroke="var(--chakra-colors-blue-100)" strokeWidth="3" opacity="0.7" aria-hidden="true" />
			{series.map(({ key, color, dasharray, strokeWidth }) => (
				<polyline
					key={key}
					fill="none"
					stroke={color}
					strokeWidth={strokeWidth}
					strokeDasharray={dasharray}
					strokeLinejoin="round"
					points={snapshots.map(({ snapshot }, index) => `${getXPosition(index)},${getYPosition(taskPoolTotal(snapshot[key]))}`).join(' ')}
				/>
			))}
			{snapshots.map((entry, index) => (
				<g key={`points-${entry.week}`} tabIndex="0" role="button" aria-label={pointDetail(entry)}
					onFocus={() => setSelectedIndex(index)} onClick={() => setSelectedIndex(index)} onKeyDown={(event) => {
					if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelectedIndex(index); }
				}}>
					<title>{pointDetail(entry)}</title>
					{series.map(({ key, color, marker }) => {
						const x = getXPosition(index);
						const y = getYPosition(taskPoolTotal(entry.snapshot[key]));
						const isLatest = index === latestIndex;
						const size = isLatest ? 1.8 : 1.3;
						return <g key={key}>
							<circle cx={x} cy={y} r="4" fill="transparent" />
							{marker === 'square'
								? <rect x={x - size} y={y - size} width={size * 2} height={size * 2} fill={color} stroke="white" strokeWidth="0.6" />
								: <circle cx={x} cy={y} r={size} fill={color} stroke="white" strokeWidth="0.6" />}
						</g>;
					})}
				</g>
			))}
			{snapshots.map(({ week }, index) => (
				<text key={week} x={getXPosition(index)} y="90" fontSize={index === latestIndex ? '4' : '3.5'} fontWeight={index === latestIndex ? 'bold' : 'normal'} textAnchor="middle">W{week}</text>
			))}
		</Box>
		<ChartLegend items={series} />
		<Box mt={3} p={3} borderWidth="1px" borderColor="blue.100" borderRadius="md" aria-live="polite">
			<Text fontWeight="bold" fontSize="sm">Week {selected.week} details{selectedIndex === latestIndex ? ' · Latest week' : ''}</Text>
			<Wrap spacingX={4} spacingY={1} mt={1}>
				{detailMetrics.map(({ key, label }) => <WrapItem key={key}><Text fontSize="sm"><strong>{label}:</strong> {taskPoolTotal(selected.snapshot[key])}</Text></WrapItem>)}
			</Wrap>
			<Text fontSize="xs" color="gray.600" mt={1}>Click a chart dot or focus a week’s dots to inspect it.</Text>
		</Box>
		<ChartDataTable caption="Task progress trend data" columns={['Week', ...series.map(({ label }) => label)]} rows={snapshots.map(({ week, snapshot }) => [`Week ${week}`, ...series.map(({ key }) => taskPoolTotal(snapshot[key]))])} />
		</Box>
	);
};

const TaskProgressDashboard = ({ state, turns = [] }) => {
	const progress = selectTaskProgress(state, turns);
	const { snapshots, current, previous, integrationTested, projectTasks } = progress;
	const bugDiscoverySeen = turns.some((turn) =>
		(turn.events || []).some((event) => event.kind === 'bugs_discovered' && taskPoolTotal(event.values) > 0)
	) || snapshots.some(({ snapshot }) => taskPoolTotal(snapshot.known_bugs) > 0);
	const metrics = [
		...series.map(({ key, label }) => ({ key, label, favorable: key !== 'known_bugs' })),
		{ key: 'tasks_todo', label: 'Remaining tasks', favorable: false },
	];
	const snapshotByWeek = new Map(snapshots.map(({ week, snapshot }) => [week, snapshot]));
	const backlogReturns = turns.flatMap((turn) => (turn.events || [])
		.filter((event) => event.kind === 'tasks_returned_to_backlog' && taskPoolTotal(event.values) > 0)
		.map((event) => ({ week: Number(turn.week_number), count: taskPoolTotal(event.values) })))
		.filter(({ week }) => taskPoolTotal(snapshotByWeek.get(week)?.tasks_todo) > taskPoolTotal(snapshotByWeek.get(week - 1)?.tasks_todo));

	return (
		<ChartCard title="Task progress" description="Track development, testing, and visible known-bug totals across the task lifecycle from week to week.">
			<HStack align="baseline" spacing={2} mb={4} flexWrap="wrap">
				<Text fontSize="2xl" fontWeight="bold" color="chart.integrationTested">{integrationTested} of {projectTasks}</Text>
				<Text fontWeight="semibold">project tasks are integration tested</Text>
			</HStack>
			<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 7fr) minmax(240px, 3fr)' }} gap={7}>
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
			{backlogReturns.map(({ week, count }) => (
				<Box key={`${week}-${count}`} mt={4} px={4} py={3} bg="orange.50" borderLeftWidth="4px" borderColor="orange.400" borderRadius="md">
					<Text fontSize="sm"><strong>Week {week} backlog return:</strong> Remaining tasks increased as {count} {count === 1 ? 'task was' : 'tasks were'} returned from integration testing for more work.</Text>
				</Box>
			))}
		</ChartCard>
	);
};

export default TaskProgressDashboard;
