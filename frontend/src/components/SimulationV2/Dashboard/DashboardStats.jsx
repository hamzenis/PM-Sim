import { SimpleGrid } from '@chakra-ui/react';
import React from 'react';
import StatCard from './StatCard';
import { taskPoolTotal } from './taskPool';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const formatCurrency = (value) => currency.format(Number(value || 0));
const signed = (value, formatter = String) => `${value > 0 ? '+' : ''}${formatter(value)}`;

const DashboardStats = ({ state, turns = [], showBudget = true }) => {
	const precedingTurn = [...turns]
		.filter((turn) => turn.week_number < state.week && turn.resulting_state)
		.sort((left, right) => right.week_number - left.week_number)[0];
	const previous = precedingTurn?.resulting_state;
	const expenses = Number(state.initial_budget) - Number(state.remaining_budget);
	const remainingTasks = taskPoolTotal(state.tasks_todo);
	const expenseDelta = previous
		? expenses - (Number(previous.initial_budget) - Number(previous.remaining_budget))
		: null;
	const taskDelta = previous ? remainingTasks - taskPoolTotal(previous.tasks_todo) : null;

	return (
		<SimpleGrid columns={{ base: 1, sm: 2, lg: showBudget ? 4 : 3 }} spacing={4} mb={8}>
			<StatCard label="Schedule remaining" value={`${Number(state.remaining_working_days || 0).toLocaleString()} days`} helper="Working days available to finish the project" />
			<StatCard
				label="Cumulative expenses"
				value={formatCurrency(expenses)}
				helper="Total project spending to date"
				delta={expenseDelta === null ? null : signed(expenseDelta, formatCurrency)}
				deltaIsFavorable={expenseDelta <= 0}
			/>
			<StatCard
				label="Remaining tasks"
				value={remainingTasks}
				helper="Tasks still waiting for development"
				delta={taskDelta === null ? null : signed(taskDelta)}
				deltaIsFavorable={taskDelta <= 0}
			/>
			{showBudget && (
				<StatCard
					label="Budget remaining"
					value={formatCurrency(state.remaining_budget)}
					helper="Funds available for future work"
					isUnfavorable={Number(state.remaining_budget) < 0}
				/>
			)}
		</SimpleGrid>
	);
};

export default DashboardStats;
