import { Alert, AlertIcon, Box, Button, Container, Heading, SimpleGrid, Spinner, Text } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getClassResult } from '../api/classes';
import FinalResult from '../components/SimulationV2/FinalResult';
import ProfessorAuthoredTimeline from '../components/ProfessorAuthoredTimeline';

const ClassResultDetail = () => {
	const { class_id: classId, run_id: runId } = useParams();
	const navigate = useNavigate();
	const [result, setResult] = useState(null);
	const [error, setError] = useState('');

	useEffect(() => {
		getClassResult(classId, runId)
			.then(setResult)
			.catch((requestError) => setError(requestError.message));
	}, [classId, runId]);

	if (error)
		return (
			<Container py={10}>
				<Alert status="error">
					<AlertIcon />
					{error}
				</Alert>
			</Container>
		);
	if (!result)
		return (
			<Container py={10}>
				<Spinner />
			</Container>
		);

	return (
		<Container maxW="6xl" py={8} flexGrow={1}>
			<Button variant="link" mb={4} onClick={() => navigate('/classes')}>
				← Classes
			</Button>
			<Heading mb={2}>Run audit: {result.student_username}</Heading>
			<Text mb={6}>
				Engine {result.engine_version}, seed {result.seed}
			</Text>
			<FinalResult result={result.final_result} />
			<ProfessorAuthoredTimeline audit={result.contentAudit} />
			<Heading size="md" mt={6} mb={4}>
				Weekly audit
			</Heading>
			{result.turns.length === 0 ? (
				<Text>No turns were completed.</Text>
			) : (
				result.turns.map((turn) => (
					<Box key={turn.week_number} bg="white" p={5} borderRadius="xl" mb={4}>
						<Heading size="sm">Week {turn.week_number}</Heading>
						<SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} mt={3}>
							<Box>
								<Text fontWeight="bold">Decision</Text>
								<pre>{JSON.stringify(turn.decision, null, 2)}</pre>
							</Box>
							<Box>
								<Text fontWeight="bold">Events</Text>
								{turn.events.map((event, index) => (
									<Text key={`${event.kind}-${index}`}>{event.kind}</Text>
								))}
							</Box>
						</SimpleGrid>
					</Box>
				))
			)}
		</Container>
	);
};

export default ClassResultDetail;
