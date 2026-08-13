import { Badge, Box, Button, Flex, Heading, SimpleGrid, Text } from '@chakra-ui/react';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDateTime, readableStatus, statusColor } from '../../utils/resultPresentation';

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
					<Flex key={result.run_id} justify="space-between" direction={{ base: 'column', md: 'row' }} gap={3} py={4} borderBottomWidth="1px">
						<SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} flex="1">
							<Box><Text fontSize="sm" color="gray.600">Student</Text><Text fontWeight="bold">{result.student_username}</Text></Box>
							<Box><Text fontSize="sm" color="gray.600">Class and scenario</Text><Text>{result.class_name} · {result.scenario_name}</Text></Box>
							<Box><Text fontSize="sm" color="gray.600">Progress</Text><Badge colorScheme={statusColor(result.status)}>{readableStatus(result.status)}</Badge><Text>Final week {result.current_week}</Text></Box>
							<Box><Text fontSize="sm" color="gray.600">Completed</Text><Text>{formatDateTime(result.finished_at)}</Text><Text fontWeight="bold">{result.final_result?.score?.total != null ? `Score: ${result.final_result.score.total}` : 'No final score'}</Text></Box>
						</SimpleGrid>
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
