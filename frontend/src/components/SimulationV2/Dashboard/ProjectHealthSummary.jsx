import { Box, Button, Heading, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import { selectBudgetTrend } from './BudgetTrendChart';
import { selectEmployeeStatusTrend, toPercentage } from './EmployeeStatusChart';
import { selectTaskProgress } from './TaskProgressDashboard';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const points = (value) => Math.round(Math.abs(toPercentage(value)));

export const selectProjectHealthSummary = (state, turns = []) => {
	const budget = selectBudgetTrend(state, turns);
	const tasks = selectTaskProgress(state, turns);
	const employees = selectEmployeeStatusTrend(state, turns);
	const variance = budget.variance;
	const taskChange = tasks.previousIntegrationTested === null
		? null
		: tasks.integrationTested - tasks.previousIntegrationTested;
	let teamText = 'No employee data is available';
	if (employees.current?.employeeCount > 0) {
		const previousMotivation = employees.previous?.motivation;
		if (previousMotivation === null || previousMotivation === undefined) {
			teamText = `Average motivation is ${Math.round(toPercentage(employees.current.motivation))}%`;
		} else {
			const change = employees.current.motivation - previousMotivation;
			teamText = change === 0
				? 'Average motivation was unchanged this week'
				: `Average motivation ${change > 0 ? 'increased' : 'decreased'} by ${points(change)} percentage ${points(change) === 1 ? 'point' : 'points'}`;
		}
	}

	return [
		{ label: 'Budget', text: variance === 0 ? 'Spending is on plan' : `Spending is ${currency.format(Math.abs(variance))} ${variance > 0 ? 'over' : 'under'} plan`, target: 'budget-detail' },
		{ label: 'Tasks', text: taskChange === null ? `${tasks.integrationTested} tasks are integration tested` : taskChange === 0 ? 'No additional tasks became integration tested this week' : taskChange > 0 ? `${taskChange} additional ${taskChange === 1 ? 'task' : 'tasks'} became integration tested this week` : `Integration-tested tasks decreased by ${Math.abs(taskChange)} this week`, target: 'task-detail' },
		{ label: 'Schedule', text: `${Math.max(0, budget.current.scheduledDays - budget.current.elapsedDays)} working days remain`, target: 'budget-detail' },
		{ label: 'Team', text: teamText, target: 'employee-detail' },
	];
};

const ProjectHealthSummary = ({ state, turns = [] }) => {
	const items = selectProjectHealthSummary(state, turns);
	const focusChart = (id) => document.getElementById(id)?.focus();
	return (
		<Box bg="white" borderWidth="1px" borderColor="blue.100" borderRadius="2xl" p={{ base: 4, md: 5 }} mb={5}>
			<Heading size="sm" mb={3}>Latest project movement</Heading>
			<SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={3}>
				{items.map((item) => (
					<Box key={item.label} borderLeftWidth="3px" borderColor="blue.400" pl={3} minW={0}>
						<Text fontSize="xs" color="gray.600" fontWeight="bold" textTransform="uppercase">{item.label}</Text>
						<Text fontSize="sm" fontWeight="semibold" mt={1}>{item.text}</Text>
						<Button variant="link" size="sm" mt={2} onClick={() => focusChart(item.target)}>View {item.label.toLowerCase()} details</Button>
					</Box>
				))}
			</SimpleGrid>
		</Box>
	);
};

export default ProjectHealthSummary;
