import {
	Box,
	Heading,
	SimpleGrid,
	Stat,
	StatHelpText,
	StatLabel,
	StatNumber,
	Text,
	Wrap,
	WrapItem,
} from '@chakra-ui/react';
import React from 'react';

const TASK_COLORS = {
	todo: '#DD6B20',
	completed: '#3182CE',
	unitTested: '#805AD5',
	integrationTested: '#38A169',
	knownBugs: '#E53E3E',
};

const TEAM_COLORS = {
	motivation: '#3182CE',
	stress: '#E53E3E',
	familiarity: '#38A169',
};

const total = (pool) => (pool ? Number(pool.easy || 0) + Number(pool.medium || 0) + Number(pool.hard || 0) : 0);

const average = (employees, name) => {
	if (!employees?.length) return 0;
	return employees.reduce((sum, employee) => sum + Number(employee[name] || 0), 0) / employees.length;
};

export const dashboardPoint = (state) => ({
	week: Number(state.week || 0),
	todo: total(state.tasks_todo),
	completed: total(state.tasks_completed),
	unitTested: total(state.tasks_unit_tested),
	integrationTested: total(state.tasks_integration_tested),
	knownBugs: total(state.known_bugs),
	budgetSpent: Number(state.initial_budget || 0) - Number(state.remaining_budget || 0),
	budgetRemaining: Number(state.remaining_budget || 0),
	motivation: average(state.employees, 'motivation') * 100,
	stress: average(state.employees, 'stress') * 100,
	familiarity: average(state.employees, 'familiarity') * 100,
});

const SimulationDashboard = ({ state, turns }) => {
	const historicalPoints = turns.filter((turn) => turn.state).map((turn) => dashboardPoint(turn.state));
	const currentPoint = dashboardPoint(state);
	const points = historicalPoints.length > 0 ? historicalPoints : [currentPoint];
	const previous = points.length > 1 ? points[points.length - 2] : null;

	return (
		<Box mb={8}>
			<Heading size="lg" mb={4}>
				Project dashboard
			</Heading>
			<SimpleGrid columns={{ base: 2, md: 3, xl: 6 }} spacing={4} mb={5}>
				<MetricCard label="Tasks to do" value={currentPoint.todo} previous={previous?.todo} />
				<MetricCard label="Tasks completed" value={currentPoint.completed} previous={previous?.completed} />
				<MetricCard label="Unit tested" value={currentPoint.unitTested} previous={previous?.unitTested} />
				<MetricCard
					label="Integration tested"
					value={currentPoint.integrationTested}
					previous={previous?.integrationTested}
				/>
				<MetricCard label="Known bugs" value={currentPoint.knownBugs} previous={previous?.knownBugs} />
				<MetricCard label="Employees" value={state.employees?.length || 0} />
			</SimpleGrid>

			<SimpleGrid columns={{ base: 1, xl: 2 }} spacing={5}>
				<LineChart title="Task progress and known bugs" points={points} series={TASK_COLORS} />
				<LineChart
					title="Budget"
					points={points}
					series={{ budgetSpent: '#3182CE', budgetRemaining: '#38A169' }}
				/>
				<LineChart title="Employee status" points={points} series={TEAM_COLORS} maximum={100} suffix="%" />
				<SimpleGrid columns={{ base: 2, md: 3 }} spacing={4} alignContent="start">
					<MetricCard label="Budget remaining" value={formatMoney(state.remaining_budget)} />
					<MetricCard label="Budget spent" value={formatMoney(currentPoint.budgetSpent)} />
					<MetricCard label="Working days left" value={state.remaining_working_days} />
					<MetricCard label="Average motivation" value={`${currentPoint.motivation.toFixed(0)}%`} />
					<MetricCard label="Average stress" value={`${currentPoint.stress.toFixed(0)}%`} />
					<MetricCard label="Average familiarity" value={`${currentPoint.familiarity.toFixed(0)}%`} />
				</SimpleGrid>
			</SimpleGrid>
		</Box>
	);
};

const MetricCard = ({ label, value, previous }) => {
	const numericValue = Number(value);
	const change = previous === undefined || Number.isNaN(numericValue) ? null : numericValue - previous;
	return (
		<Box bg="white" borderRadius="xl" p={4}>
			<Stat>
				<StatLabel>{label}</StatLabel>
				<StatNumber>{value}</StatNumber>
				{change !== null && (
					<StatHelpText mb={0}>
						{change === 0 ? 'No weekly change' : `${change > 0 ? '+' : ''}${change} this week`}
					</StatHelpText>
				)}
			</Stat>
		</Box>
	);
};

const LineChart = ({ title, points, series, maximum, suffix = '' }) => {
	const names = Object.keys(series);
	const values = points.flatMap((point) => names.map((name) => Number(point[name] || 0)));
	const maxValue = maximum || Math.max(...values, 1);
	const coordinates = (name) =>
		points
			.map((point, index) => {
				const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
				const y = 90 - (Number(point[name] || 0) / maxValue) * 80;
				return `${x},${y}`;
			})
			.join(' ');

	return (
		<Box bg="white" borderRadius="2xl" p={5}>
			<Heading size="md" mb={2}>
				{title}
			</Heading>
			<Text fontSize="sm" color="gray.500" mb={2}>
				Weekly values from the completed simulation turns
			</Text>
			<Box
				as="svg"
				viewBox="0 0 100 100"
				width="100%"
				height="260px"
				role="img"
				aria-label={`${title} line chart`}
			>
				<line x1="0" y1="90" x2="100" y2="90" stroke="#CBD5E0" strokeWidth="0.7" />
				<line x1="0" y1="10" x2="0" y2="90" stroke="#CBD5E0" strokeWidth="0.7" />
				{names.map((name) => (
					<polyline
						key={name}
						points={coordinates(name)}
						fill="none"
						stroke={series[name]}
						strokeWidth="1.8"
					/>
				))}
			</Box>
			<Wrap spacing={4}>
				{names.map((name) => (
					<WrapItem key={name} alignItems="center">
						<Box boxSize="10px" borderRadius="full" bg={series[name]} mr={2} />
						<Text fontSize="sm">
							{readableName(name)}: {Number(points[points.length - 1][name] || 0).toFixed(suffix ? 0 : 2)}
							{suffix}
						</Text>
					</WrapItem>
				))}
			</Wrap>
		</Box>
	);
};

const readableName = (name) => name.replace(/([A-Z])/g, ' $1').replace(/^./, (letter) => letter.toUpperCase());
const formatMoney = (value) => new Intl.NumberFormat('en', { style: 'currency', currency: 'EUR' }).format(value || 0);

export default SimulationDashboard;
