import { Box, Grid, Heading, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import StatCard from './StatCard';
import { taskPoolTotal } from './taskPool';

const series = [
	{ key: 'tasks_completed', label: 'Completed', color: '#3182ce' },
	{ key: 'tasks_unit_tested', label: 'Unit tested', color: '#805ad5' },
	{ key: 'tasks_integration_tested', label: 'Integration tested', color: '#38a169' },
	{ key: 'known_bugs', label: 'Known bugs', color: '#e53e3e' },
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
	const values = snapshots.flatMap(({ snapshot }) => series.map(({ key }) => taskPoolTotal(snapshot[key])));
	const maximum = Math.max(1, ...values);
	const x = (index) => (snapshots.length === 1 ? 50 : (index / (snapshots.length - 1)) * 100);
	const y = (value) => 92 - (value / maximum) * 80;

	return (
		<Box minW={0}>
		<Box as="svg" viewBox="0 0 100 100" width="100%" height="280px" role="img" aria-label="Cumulative task progress by week">
			<line x1="0" y1="92" x2="100" y2="92" stroke="#CBD5E0" strokeWidth="0.7" />
			{series.map(({ key, label, color }) => (
				<polyline
					key={key}
					aria-label={label}
					fill="none"
					stroke={color}
					strokeWidth="2"
					points={snapshots.map(({ snapshot }, index) => `${x(index)},${y(taskPoolTotal(snapshot[key]))}`).join(' ')}
				/>
			))}
			{snapshots.map(({ week }, index) => (
				<text key={week} x={x(index)} y="99" fontSize="4" textAnchor="middle">W{week}</text>
			))}
		</Box>
		<SimpleGrid columns={{ base: 2, md: 4 }} spacing={2} mt={2}>
			{series.map(({ key, label, color }) => <Text key={key} fontSize="sm" color={color}>● {label}</Text>)}
		</SimpleGrid>
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
		<Box bg="white" borderRadius="2xl" p={7} mb={8}>
			<Heading size="md" mb={5}>Task progress</Heading>
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
		</Box>
	);
};

export default TaskProgressDashboard;
