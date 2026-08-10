import { Box, Heading, SimpleGrid, Stat, StatLabel, StatNumber, Text } from '@chakra-ui/react';
import React from 'react';

const FinalResult = ({ result }) => {
	if (!result) return <Text>No final result is available.</Text>;
	const score = result.score || {};
	return (
		<Box bg="white" borderRadius="2xl" p={7}>
			<Heading size="md" mb={5}>
				Final result
			</Heading>
			<SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
				<ResultStat label="Outcome" value={result.outcome} />
				<ResultStat label="Total score" value={score.total} />
				<ResultStat label="Accepted tasks" value={result.accepted_tasks} />
				<ResultStat label="Rejected tasks" value={result.rejected_tasks} />
				<ResultStat label="Quality score" value={score.quality} />
				<ResultStat label="Time score" value={score.time} />
				<ResultStat label="Budget score" value={score.budget} />
				<ResultStat label="Total cost" value={result.total_cost} />
			</SimpleGrid>
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
