import {
	Alert,
	AlertIcon,
	Badge,
	Box,
	Button,
	Container,
	Flex,
	Heading,
	Spinner,
	Table,
	TableContainer,
	Tbody,
	Td,
	Text,
	Th,
	Thead,
	Tr,
} from '@chakra-ui/react';
import React, { useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import { listAvailableScenarios, listOwnedScenarios } from '../api/scenarios';
import { listSimulationRuns, startSimulationRun } from '../api/simulations';
import { AuthContext } from '../context/AuthProvider';

export const scenarioAssignmentKey = (classId, revisionId) => `${classId}:${revisionId}`;

const ScenarioOverview = () => {
	const { currentUser } = useContext(AuthContext);
	const navigate = useNavigate();
	const [scenarios, setScenarios] = useState([]);
	const [runs, setRuns] = useState([]);
	const [isLoading, setIsLoading] = useState(true);
	const [startingId, setStartingId] = useState(null);
	const [error, setError] = useState(null);
	const isProfessor = currentUser?.role === 'professor';

	useEffect(() => {
		let active = true;
		const load = async () => {
			setIsLoading(true);
			setError(null);
			try {
				const [loadedScenarios, loadedRuns] = await Promise.all([
					isProfessor ? listOwnedScenarios() : listAvailableScenarios(),
					isProfessor ? Promise.resolve([]) : listSimulationRuns(),
				]);
				if (active) {
					setScenarios(loadedScenarios);
					setRuns(loadedRuns);
				}
			} catch (requestError) {
				if (active) setError(requestError.message || 'Could not load scenarios');
			} finally {
				if (active) setIsLoading(false);
			}
		};
		load();
		return () => {
			active = false;
		};
	}, [isProfessor]);

	const runsByAssignment = useMemo(
		() => new Map(runs.map((run) => [scenarioAssignmentKey(run.class_id, run.scenario_revision_id), run])),
		[runs]
	);

	const start = async (scenario) => {
		const assignmentKey = scenarioAssignmentKey(scenario.class_id, scenario.id);
		setStartingId(assignmentKey);
		setError(null);
		try {
			const run = await startSimulationRun(
				scenario.id,
				Math.floor(Math.random() * 2147483647),
				scenario.class_id
			);
			navigate(`/simulations/${run.id}`);
		} catch (requestError) {
			setError(requestError instanceof ApiError ? requestError.message : 'Could not start the simulation');
		} finally {
			setStartingId(null);
		}
	};

	return (
		<Flex px={10} pt={2} flexDir="column" flexGrow={1}>
			<Heading mb={5}>Scenarios</Heading>
			{error && (
				<Alert status="error" mb={4}>
					<AlertIcon />
					{error}
				</Alert>
			)}
			<Box backgroundColor="white" borderRadius="2xl">
				<Container maxW="6xl" py={10} minH="70vh">
					{isProfessor && (
						<Alert status="info" mb={5}>
							<AlertIcon />
							Scenario authoring is not part of this version. Existing backend-v2 scenarios are listed
							here.
						</Alert>
					)}
					{isLoading ? (
						<Flex justifyContent="center">
							<Spinner size="xl" />
						</Flex>
					) : scenarios.length === 0 ? (
						<Text>No scenarios are available.</Text>
					) : (
						<TableContainer>
							<Table variant="simple">
								<Thead>
									<Tr>
										<Th>Name</Th>
										{!isProfessor && <Th>Class</Th>}
										<Th>Revision</Th>
										<Th>Status</Th>
										<Th />
									</Tr>
								</Thead>
								<Tbody>
									{scenarios.map((scenario) => {
										const revisionId = isProfessor ? null : scenario.id;
										const assignmentKey = scenarioAssignmentKey(scenario.class_id, revisionId);
										const run = revisionId ? runsByAssignment.get(assignmentKey) : null;
										return (
											<Tr key={isProfessor ? scenario.id : assignmentKey}>
												<Td fontWeight="semibold">
													{isProfessor ? scenario.name : scenario.definition.name}
												</Td>
												{!isProfessor && <Td>{scenario.class_name}</Td>}
												<Td>
													{isProfessor ? scenario.latest_revision : scenario.revision_number}
												</Td>
												<Td>
													<Badge>
														{isProfessor
															? scenario.latest_status
															: run?.status || 'available'}
													</Badge>
												</Td>
												<Td textAlign="right">
													{!isProfessor &&
														(run ? (
															<Button onClick={() => navigate(`/simulations/${run.id}`)}>
																Resume
															</Button>
														) : (
															<Button
																colorScheme="blue"
																isLoading={startingId === assignmentKey}
																onClick={() => start(scenario)}
															>
																Start
															</Button>
														))}
												</Td>
											</Tr>
										);
									})}
								</Tbody>
							</Table>
						</TableContainer>
					)}
				</Container>
			</Box>
		</Flex>
	);
};

export default ScenarioOverview;
