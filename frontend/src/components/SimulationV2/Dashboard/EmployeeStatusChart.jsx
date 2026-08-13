import { Box, Grid, HStack, SimpleGrid, Stat, StatHelpText, StatLabel, StatNumber, Text, VStack } from '@chakra-ui/react';
import React from 'react';
import { CHART, ChartCard, ChartDataTable, ChartGrid, ChartLegend, EmptyChart } from './ChartPresentation';

const metrics = [
	{ key: 'stress', label: 'Stress', color: 'var(--chakra-colors-chart-stress)', marker: 'circle' },
	{ key: 'motivation', label: 'Motivation', color: 'var(--chakra-colors-chart-motivation)', marker: 'square' },
	{ key: 'familiarity', label: 'Familiarity', color: 'var(--chakra-colors-chart-familiarity)', marker: 'diamond', dashed: true },
];

const EMPLOYEE_CHART = { ...CHART, right: 152 };

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

const teamChange = (current, previous) => {
	if (!previous || current.employeeCount === previous.employeeCount) return null;
	return `Team ${current.employeeCount > previous.employeeCount ? 'increased' : 'decreased'} from ${previous.employeeCount} to ${current.employeeCount}`;
};

const PointMarker = ({ marker, x, y, color, latest }) => {
	const common = { fill: color, stroke: latest ? 'var(--chakra-colors-chart-axis)' : 'var(--chakra-colors-surface-bg)', strokeWidth: latest ? 1.4 : 0.8 };
	if (marker === 'square') return <rect x={x - (latest ? 2.4 : 1.9)} y={y - (latest ? 2.4 : 1.9)} width={latest ? 4.8 : 3.8} height={latest ? 4.8 : 3.8} {...common} />;
	if (marker === 'diamond') return <polygon points={`${x},${y - (latest ? 3 : 2.4)} ${x + (latest ? 3 : 2.4)},${y} ${x},${y + (latest ? 3 : 2.4)} ${x - (latest ? 3 : 2.4)},${y}`} {...common} />;
	return <circle cx={x} cy={y} r={latest ? 2.6 : 2.1} {...common} />;
};

const TrendChart = ({ snapshots }) => {
	if (snapshots.length === 0) return <EmptyChart>No employee status history is available yet.</EmptyChart>;
	const getXPosition = (index) => (snapshots.length === 1 ? (EMPLOYEE_CHART.left + EMPLOYEE_CHART.right) / 2 : EMPLOYEE_CHART.left + (index / (snapshots.length - 1)) * (EMPLOYEE_CHART.right - EMPLOYEE_CHART.left));
	const getYPosition = (value) => EMPLOYEE_CHART.bottom - toPercentage(value) / 100 * (EMPLOYEE_CHART.bottom - EMPLOYEE_CHART.top);

	return (
		<Box minW={0}>
			<Box as="svg" viewBox="0 0 156 104" width="100%" height={{ base: '210px', md: '280px' }} role="img" aria-label="Weekly team-average employee status percentages">
				<desc>Stress, motivation, and familiarity team averages shown as percentages for each project week.</desc>
				<ChartGrid ticks={[0, 0.5, 1]} getYPosition={getYPosition} formatTick={(value) => `${toPercentage(value)}%`} xLabel="Project week" yLabel="Team average (%)" chart={EMPLOYEE_CHART} />
				{metrics.map(({ key, color, dashed }) => {
					const points = snapshots
						.map((snapshot, index) => snapshot[key] === null ? null : `${getXPosition(index)},${getYPosition(snapshot[key])}`)
						.filter(Boolean)
						.join(' ');
					return points && <polyline key={key} points={points} fill="none" stroke={color} strokeWidth="2" strokeDasharray={dashed ? '4 3' : undefined} />;
				})}
				{metrics.flatMap(({ key, color, marker }) => snapshots.map((snapshot, index) => snapshot[key] === null ? null : (
					<PointMarker key={`${key}-${snapshot.week}`} marker={marker} x={getXPosition(index)} y={getYPosition(snapshot[key])} color={color} latest={index === snapshots.length - 1} />
				)))}
				{snapshots.map(({ week }, index) => <text key={week} x={getXPosition(index)} y="90" fontSize="3.5" textAnchor="middle">W{week}</text>)}
			</Box>
			<ChartLegend items={metrics} />
			<VStack align="stretch" spacing={2} mt={4} aria-label="Weekly employee status details">
				{snapshots.map((snapshot, index) => {
					const change = teamChange(snapshot, snapshots[index - 1]);
					const details = `Week ${snapshot.week}. Team size ${snapshot.employeeCount}. Average stress ${snapshot.stress === null ? 'not available' : formatPercentage(snapshot.stress)}. Average motivation ${snapshot.motivation === null ? 'not available' : formatPercentage(snapshot.motivation)}. Average familiarity ${snapshot.familiarity === null ? 'not available' : formatPercentage(snapshot.familiarity)}.`;
					return (
						<Box key={snapshot.week}>
							<Box as="button" type="button" width="100%" textAlign="left" borderWidth={index === snapshots.length - 1 ? '2px' : '1px'} borderColor={index === snapshots.length - 1 ? 'blue.400' : 'border.default'} borderRadius="md" px={3} py={2} _focusVisible={{ boxShadow: 'outline' }} aria-label={details}>
								<HStack justify="space-between"><Text fontWeight="semibold">Week {snapshot.week}</Text><Text fontSize="sm">{snapshot.employeeCount} {snapshot.employeeCount === 1 ? 'employee' : 'employees'}{index === snapshots.length - 1 ? ' · Latest' : ''}</Text></HStack>
							</Box>
							{change && <Text fontSize="xs" color="text.muted" mt={1}>{change}</Text>}
						</Box>
					);
				})}
			</VStack>
			<ChartDataTable caption="Employee status trend data" columns={['Week', 'Team size', ...metrics.map(({ label }) => label)]} rows={snapshots.map((snapshot) => [`Week ${snapshot.week}`, snapshot.employeeCount, ...metrics.map(({ key }) => snapshot[key] === null ? 'No employees' : formatPercentage(snapshot[key]))])} />
		</Box>
	);
};

const EmployeeStatusChart = ({ state, turns = [] }) => {
	const trend = selectEmployeeStatusTrend(state, turns);
	const { current, previous } = trend;

	return (
		<ChartCard title="Employee status" description="These are per-week team averages. The employees included can change through hiring and dismissal. Higher motivation and familiarity are positive; stress is shown neutrally.">
			{current.employeeCount === 0 ? (
				<EmptyChart>No employees</EmptyChart>
			) : (
				<Grid templateColumns={{ base: '1fr', lg: 'minmax(0, 7fr) minmax(240px, 3fr)' }} gap={7}>
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
