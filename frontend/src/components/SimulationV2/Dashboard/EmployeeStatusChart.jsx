import { Box, Grid, Heading, SimpleGrid, Stat, StatHelpText, StatLabel, StatNumber, Text } from '@chakra-ui/react';
import React from 'react';

const metrics = [
	{ key: 'stress', label: 'Stress', color: '#E53E3E' },
	{ key: 'motivation', label: 'Motivation', color: '#3182CE' },
	{ key: 'familiarity', label: 'Familiarity', color: '#38A169' },
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
	const x = (index) => (snapshots.length === 1 ? 50 : 5 + (index / (snapshots.length - 1)) * 90);
	const y = (value) => 90 - toPercentage(value) * 0.8;

	return (
		<Box minW={0}>
			<Box as="svg" viewBox="0 0 100 100" width="100%" height="280px" role="img" aria-label="Weekly team-average employee status percentages">
				<line x1="5" y1="90" x2="95" y2="90" stroke="#CBD5E0" strokeWidth="0.7" />
				{metrics.map(({ key, label, color }) => {
					const points = snapshots
						.map((snapshot, index) => snapshot[key] === null ? null : `${x(index)},${y(snapshot[key])}`)
						.filter(Boolean)
						.join(' ');
					return points && <polyline key={key} aria-label={label} points={points} fill="none" stroke={color} strokeWidth="2" />;
				})}
				{snapshots.map(({ week }, index) => <text key={week} x={x(index)} y="99" fontSize="4" textAnchor="middle">W{week}</text>)}
			</Box>
			<SimpleGrid columns={{ base: 1, sm: 3 }} spacing={2} mt={2}>
				{metrics.map(({ key, label, color }) => <Text key={key} color={color} fontSize="sm">● {label}</Text>)}
			</SimpleGrid>
		</Box>
	);
};

const EmployeeStatusChart = ({ state, turns = [] }) => {
	const trend = selectEmployeeStatusTrend(state, turns);
	const { current, previous } = trend;

	return (
		<Box bg="white" borderRadius="2xl" p={7} mb={8}>
			<Heading size="md">Employee status</Heading>
			<Text color="gray.600" fontSize="sm" mt={2} mb={5}>
				These are per-week team averages. The employees included can change through hiring and dismissal.
			</Text>
			{current.employeeCount === 0 ? (
				<Text fontWeight="semibold">No employees</Text>
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
		</Box>
	);
};

export default EmployeeStatusChart;
