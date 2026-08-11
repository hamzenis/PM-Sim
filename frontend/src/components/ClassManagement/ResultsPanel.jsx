import { Box, Button, Flex, Heading, Text } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

const ResultsPanel = ({ classId, results }) => {
	const navigate = useNavigate();
	return (
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
