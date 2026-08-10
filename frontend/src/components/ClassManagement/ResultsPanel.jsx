import { Box, Flex, Heading, Text } from '@chakra-ui/react';
import React from 'react';

const ResultsPanel = ({ results }) => (
	<Box bg="white" p={6} borderRadius="xl" mt={6}>
		<Heading size="md" mb={4}>
			Simulation results
		</Heading>
		{results.length === 0 ? (
			<Text>No simulation results yet.</Text>
		) : (
			results.map((result) => (
				<Flex key={result.run_id} justify="space-between" py={2}>
					<Text>{result.student_username}</Text>
					<Text>
						{result.status}, week {result.current_week}
					</Text>
				</Flex>
			))
		)}
	</Box>
);

export default ResultsPanel;
