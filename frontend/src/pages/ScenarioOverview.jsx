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
import {
	archiveScenario,
	createScenario,
	listAvailableScenarios,
	listOwnedScenarios,
	publishScenarioRevision,
	validateScenario,
} from '../api/scenarios';
import { listSimulationRuns, startSimulationRun } from '../api/simulations';
import { AuthContext } from '../context/AuthProvider';
import ScenarioImportDialog from '../components/ScenarioImportDialog';

export const scenarioAssignmentKey = (classId, revisionId) => `${classId}:${revisionId}`;

const ScenarioOverview = () => {
	const { currentUser } = useContext(AuthContext);
	const navigate = useNavigate();
	const [scenarios, setScenarios] = useState([]);
	const [runs, setRuns] = useState([]);
	const [isLoading, setIsLoading] = useState(true);
	const [startingId, setStartingId] = useState(null);
	const [error, setError] = useState(null);
	const [isImportOpen, setIsImportOpen] = useState(false);
	const isProfessor = currentUser?.role === 'professor';

	const refreshProfessorScenarios = async () => setScenarios(await listOwnedScenarios());

	const importScenario = async (definition) => {
		setStartingId('import');
		setError(null);
		try {
			const normalized = await validateScenario(definition);
			await createScenario(normalized);
			await refreshProfessorScenarios();
			setIsImportOpen(false);
		} catch (requestError) {
			setError(requestError.message || 'Could not import the scenario');
		} finally {
			setStartingId(null);
		}
	};

	const updateScenario = async (action) => {
		setError(null);
		try {
			await action();
			await refreshProfessorScenarios();
		} catch (requestError) {
			setError(requestError.message || 'Could not update the scenario');
		}
	};

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
			<Flex justify="space-between" align="center" mb={5}>
				<Heading>Scenarios</Heading>
				{isProfessor && (
					<Button colorScheme="blue" onClick={() => setIsImportOpen(true)}>
						Import scenario JSON
					</Button>
				)}
			</Flex>
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
							The visual scenario editor is not part of this version. Import backend-v2 scenario JSON
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
													{isProfessor && (
														<Flex justify="flex-end" gap={2}>
															{scenario.latest_status === 'draft' && (
																<Button
																	size="sm"
																	colorScheme="green"
																	onClick={() =>
																		updateScenario(() =>
																			publishScenarioRevision(
																				scenario.id,
																				scenario.latest_revision
																			)
																		)
																	}
																>
																	Publish
																</Button>
															)}
															<Button
																size="sm"
																colorScheme="red"
																variant="outline"
																onClick={() =>
																	updateScenario(() => archiveScenario(scenario.id))
																}
															>
																Archive
															</Button>
														</Flex>
													)}
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
			<ScenarioImportDialog
				isOpen={isImportOpen}
				isBusy={startingId === 'import'}
				onCancel={() => setIsImportOpen(false)}
				onImport={importScenario}
			/>
		</Flex>
	);
};

export default ScenarioOverview;
