import { Badge, Box, Button, Container, Heading, SimpleGrid, Text, VStack } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getClassResult } from '../api/classes';
import FinalResult from '../components/SimulationV2/FinalResult';
import ProfessorAuthoredTimeline from '../components/ProfessorAuthoredTimeline';
import {
	formatDateTime,
	formatTeachingValue,
	plainLanguageLabel,
	readableStatus,
	statusColor,
} from '../utils/resultPresentation';
import { EmptyState, PageLoadingState, RequestError } from '../components/FeedbackStates';

export const TeachingFields = ({ values }) => (
	<VStack align="stretch" spacing={2}>
		{Object.entries(values || {}).map(([key, value]) => (
			<Text key={key}>
				<Text as="span" fontWeight="semibold">
					{plainLanguageLabel(key)}:
				</Text>{' '}
				{formatTeachingValue(key, value)}
			</Text>
		))}
	</VStack>
);

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
				<RequestError title="Couldn’t load this result" message={error} />
			</Container>
		);
	if (!result)
		return (
			<Container py={10}>
				<PageLoadingState label="Loading class result…" />
			</Container>
		);
	return (
		<Container maxW="6xl" py={8} flexGrow={1}>
			<Button variant="link" mb={4} onClick={() => navigate('/classes')}>
				← Classes
			</Button>
			<Heading mb={1}>Result for {result.student_username}</Heading>
			<Text fontSize="lg" mb={5}>
				{result.class_name} · {result.scenario_name}
			</Text>
			<SimpleGrid
				columns={{ base: 1, md: 3 }}
				spacing={4}
				bg="white"
				p={5}
				borderRadius="xl"
				borderWidth="1px"
				mb={6}
			>
				<Box>
					<Text color="gray.600">Status</Text>
					<Badge colorScheme={statusColor(result.status)}>{readableStatus(result.status)}</Badge>
				</Box>
				<Box>
					<Text color="gray.600">Final week</Text>
					<Text fontWeight="bold">Week {result.current_week}</Text>
				</Box>
				<Box>
					<Text color="gray.600">Completed</Text>
					<Text fontWeight="bold">{formatDateTime(result.finished_at)}</Text>
				</Box>
			</SimpleGrid>
			<FinalResult result={result.final_result} />
			<ProfessorAuthoredTimeline audit={result.contentAudit} />
			<Heading size="md" mt={8} mb={4}>
				Weekly decisions and outcomes
			</Heading>
			{result.turns.length === 0 ? (
				<EmptyState
					title="No completed weeks"
					description="This student has not submitted a weekly decision yet. Decisions and outcomes will appear here after the simulation progresses."
				/>
			) : (
				result.turns.map((turn) => (
					<Box key={turn.week_number} bg="white" p={5} borderRadius="xl" mb={4} borderWidth="1px">
						<Heading size="sm" mb={1}>
							Week {turn.week_number}
						</Heading>
						<Text color="gray.600" mb={4}>
							Submitted {formatDateTime(turn.submitted_at)}
						</Text>
						<SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
							<Box>
								<Heading size="xs" mb={2}>
									Decisions
								</Heading>
								<TeachingFields values={turn.decision} />
							</Box>
							<Box>
								<Heading size="xs" mb={2}>
									Outcomes
								</Heading>
								{turn.events.length ? (
									turn.events.map((event, index) => (
										<Box key={`${event.kind}-${index}`} mb={2}>
											<Text fontWeight="semibold">{plainLanguageLabel(event.kind)}</Text>
											<TeachingFields
												values={Object.fromEntries(
													Object.entries(event).filter(([key]) => key !== 'kind')
												)}
											/>
										</Box>
									))
								) : (
									<Text>No recorded events.</Text>
								)}
							</Box>
						</SimpleGrid>
					</Box>
				))
			)}
			<Box as="details" mt={6} bg="gray.50" p={4} borderRadius="md">
				<Box as="summary" cursor="pointer" fontWeight="bold">
					Technical details
				</Box>
				<TeachingFields
					values={{
						engine_version: result.engine_version,
						seed: result.seed,
						run_id: result.run_id,
						student_id: result.student_id,
						scenario_revision_id: result.scenario_revision_id,
					}}
				/>
				<Heading size="xs" mt={4}>
					Raw run payload
				</Heading>
				<Box as="pre" overflowX="auto" fontSize="xs">
					{JSON.stringify({ current_state: result.current_state, turns: result.turns }, null, 2)}
				</Box>
			</Box>
		</Container>
	);
};
export default ClassResultDetail;
