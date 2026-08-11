import { SimpleGrid } from '@chakra-ui/react';
import React from 'react';
import StatCard from './StatCard';
import { totalTaskPool } from './taskPool';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const formatCurrency = (value) => currency.format(Number(value || 0));
const signed = (value, formatter = String) => `${value > 0 ? '+' : ''}${formatter(value)}`;

const DashboardStats = ({ state, turns = [], showBudget = true }) => {
	const precedingTurn = [...turns]
		.filter((turn) => turn.week_number < state.week && turn.resulting_state)
		.sort((left, right) => right.week_number - left.week_number)[0];
	const previous = precedingTurn?.resulting_state;
	const expenses = Number(state.initial_budget) - Number(state.remaining_budget);
	const remainingTasks = totalTaskPool(state.tasks_todo);
	const expenseDelta = previous
		? expenses - (Number(previous.initial_budget) - Number(previous.remaining_budget))
		: null;
	const taskDelta = previous ? remainingTasks - totalTaskPool(previous.tasks_todo) : null;

	return (
		<SimpleGrid columns={{ base: 1, sm: 2, lg: showBudget ? 4 : 3 }} spacing={4} mb={8}>
			<StatCard label="Working days remaining" value={state.remaining_working_days} />
			<StatCard
				label="Cumulative expenses"
				value={formatCurrency(expenses)}
				delta={expenseDelta === null ? null : signed(expenseDelta, formatCurrency)}
				deltaIsFavorable={expenseDelta <= 0}
			/>
			<StatCard
				label="Remaining tasks"
				value={remainingTasks}
				delta={taskDelta === null ? null : signed(taskDelta)}
				deltaIsFavorable={taskDelta <= 0}
			/>
			{showBudget && (
				<StatCard
					label="Budget remaining"
					value={formatCurrency(state.remaining_budget)}
					isUnfavorable={Number(state.remaining_budget) < 0}
				/>
			)}
		</SimpleGrid>
	);
};

export default DashboardStats;
