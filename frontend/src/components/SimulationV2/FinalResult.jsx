import { Box, Heading, SimpleGrid, Stat, StatLabel, StatNumber, Text } from '@chakra-ui/react';
import React from 'react';

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const formatCurrency = (value) => currency.format(Number(value));
const formatScore = (value, total = false) => (value == null ? '—' : `${value}${total ? '/100' : ' pts'}`);
const formatDays = (value) => (value == null ? '—' : `${value} ${Number(value) === 1 ? 'day' : 'days'}`);

const formatBudgetVariance = (value) => {
	if (value == null) return '—';
	const amount = Number(value);
	const sign = amount > 0 ? '+' : amount < 0 ? '−' : '';
	return `${sign}${formatCurrency(Math.abs(amount))}`;
};

const FinalResult = ({ result }) => {
	if (!result) return <Text>No final result is available.</Text>;
	const score = result.score || {};
	const accepted = result.accepted_tasks;
	const rejected = result.rejected_tasks;
	return (
		<Box bg="white" borderRadius="2xl" p={7}>
			<Heading size="md" mb={5}>
				Final result
			</Heading>
			<SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
				<ResultStat label="Outcome" value={result.outcome} />
				<ResultStat label="Total score" value={formatScore(score.total, true)} />
				<ResultStat label="Accepted tasks" value={accepted} />
				<ResultStat label="Rejected tasks" value={rejected} />
				<ResultStat label="Quality score" value={formatScore(score.quality)} />
				<ResultStat label="Time score" value={formatScore(score.time)} />
				<ResultStat label="Budget score" value={formatScore(score.budget)} />
				<ResultStat label="Elapsed working days" value={formatDays(result.elapsed_working_days)} />
				<ResultStat label="Scheduled working days" value={formatDays(result.scheduled_working_days)} />
				<ResultStat
					label="Total cost"
					value={result.total_cost == null ? '—' : formatCurrency(result.total_cost)}
				/>
				<ResultStat label="Budget variance" value={formatBudgetVariance(result.remaining_budget)} />
			</SimpleGrid>
			<Text mt={5} color="gray.600">
				Accepted tasks are integration tested and count toward project quality. Rejected tasks are all remaining
				tasks that were not integration tested when the project ended.
			</Text>
			{result.remaining_budget != null && (
				<Text mt={2} color={Number(result.remaining_budget) < 0 ? 'red.600' : 'gray.600'}>
					{Number(result.remaining_budget) < 0
						? `The project finished ${formatCurrency(Math.abs(result.remaining_budget))} over budget.`
						: `The project finished ${formatCurrency(result.remaining_budget)} under budget.`}
				</Text>
			)}
		</Box>
	);
};

const ResultStat = ({ label, value }) => (
	<Stat>
		<StatLabel>{label}</StatLabel>
		<StatNumber>{String(value ?? '—')}</StatNumber>
	</Stat>
);

export default FinalResult;
