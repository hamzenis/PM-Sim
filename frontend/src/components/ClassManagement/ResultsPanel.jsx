import { Box, Button, Flex, Heading, Text } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

const ResultsPanel = ({ classId, results }) => {
	const navigate = useNavigate();
	return (
		<Box as="section" aria-labelledby="results-heading" bg="white" p={{ base: 4, md: 6 }} borderRadius="xl" borderWidth="1px">
			<Heading size="md" mb={4}>
				<span id="results-heading">Simulation results</span>
			</Heading>
			{results.length === 0 ? (
				<Text>No simulation results yet.</Text>
			) : (
				results.map((result) => (
					<Flex key={result.run_id} justify="space-between" direction={{ base: 'column', md: 'row' }} gap={2} py={3} borderBottomWidth="1px">
						<Text>{result.student_username}</Text>
						<Text>
							{result.status}, week {result.current_week}
						</Text>
						<Button size="sm" onClick={() => navigate(`/classes/${classId}/results/${result.run_id}`)}>
							View details
						</Button>
					</Flex>
				))
			)}
		</Box>
	);
};

export default ResultsPanel;
