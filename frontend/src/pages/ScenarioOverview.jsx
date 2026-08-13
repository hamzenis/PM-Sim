import {
	Alert,
	AlertIcon,
	Badge,
	Box,
	Button,
	Container,
	Flex,
	Grid,
	Heading,
	Progress,
	Table,
	TableContainer,
	Tbody,
	Td,
	Text,
	Th,
	Thead,
	Tr,
} from '@chakra-ui/react';
import React, { useContext, useEffect, useMemo, useRef, useState } from 'react';
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
import ConfirmDialog from '../components/ClassManagement/ConfirmDialog';
import { EmptyState, PageLoadingState, RequestError } from '../components/FeedbackStates';

export const scenarioAssignmentKey = (classId, revisionId) => `${classId}:${revisionId}`;

const studentRunPresentation = (run) => {
	if (!run) return { label: 'Ready to start', action: 'Start', colorScheme: 'blue' };
	if (run.status === 'active') return { label: 'In progress', action: 'Continue', colorScheme: 'blue' };
	return { label: 'Completed', action: 'View result', colorScheme: 'green' };
};

const StudentScenarioCard = ({ scenario, run, isStarting, onStart, onOpen }) => {
	const presentation = studentRunPresentation(run);
	const description = scenario.definition?.description?.trim();
	const currentWeek = run?.current_week ?? 0;

	return (
		<Box
			as="article"
			borderWidth="1px"
			borderColor="gray.200"
			borderRadius="xl"
			p={{ base: 5, md: 6 }}
			boxShadow="sm"
		>
			<Flex justify="space-between" align="flex-start" gap={3} mb={3}>
				<Box>
					<Heading as="h2" size="md" mb={1}>
						{scenario.definition?.name}
					</Heading>
					<Text color="gray.600" fontWeight="medium">
						{scenario.class_name}
					</Text>
				</Box>
				<Badge
					colorScheme={run?.status === 'active' ? 'blue' : run ? 'green' : 'gray'}
					px={2}
					py={1}
					borderRadius="md"
				>
					{presentation.label}
				</Badge>
			</Flex>
			{description && (
				<Text color="gray.700" mb={5}>
					{description}
				</Text>
			)}
			{run && (
				<Box mb={5}>
					<Flex justify="space-between" mb={2}>
						<Text fontSize="sm" fontWeight="semibold">
							{run.status === 'active'
								? `Week ${currentWeek} completed`
								: `Finished after week ${currentWeek}`}
						</Text>
						<Text fontSize="sm" color="gray.500">
							Revision {scenario.revision_number}
						</Text>
					</Flex>
					<Progress
						value={run.status === 'active' ? undefined : 100}
						isIndeterminate={run.status === 'active'}
						colorScheme={run.status === 'active' ? 'blue' : 'green'}
						borderRadius="full"
						aria-label={
							run.status === 'active' ? `In progress through week ${currentWeek}` : 'Scenario completed'
						}
					/>
				</Box>
			)}
			{!run && (
				<Text fontSize="sm" color="gray.500" mb={5}>
					Revision {scenario.revision_number}
				</Text>
			)}
			<Button
				w={{ base: 'full', sm: 'auto' }}
				colorScheme={presentation.colorScheme}
				isLoading={isStarting}
				loadingText="Starting"
				onClick={() => (run ? onOpen(run) : onStart(scenario))}
			>
				{presentation.action}
			</Button>
		</Box>
	);
};

const StudentScenarioSection = ({ scenarios, runsByAssignment, startingId, onStart, onOpen }) => {
	if (scenarios.length === 0) {
		return (
			<EmptyState
				title="No scenarios assigned yet"
				description="Your professor may not have assigned a scenario yet. When one is made available, it will appear here and you can start it."
			/>
		);
	}

	return (
		<Grid templateColumns={{ base: '1fr', lg: 'repeat(2, minmax(0, 1fr))' }} gap={5}>
			{scenarios.map((scenario) => {
				const assignmentKey = scenarioAssignmentKey(scenario.class_id, scenario.id);
				return (
					<StudentScenarioCard
						key={assignmentKey}
						scenario={scenario}
						run={runsByAssignment.get(assignmentKey)}
						isStarting={startingId === assignmentKey}
						onStart={onStart}
						onOpen={onOpen}
					/>
				);
			})}
		</Grid>
	);
};

const ScenarioOverview = () => {
	const { currentUser } = useContext(AuthContext);
	const navigate = useNavigate();
	const [scenarios, setScenarios] = useState([]);
	const [runs, setRuns] = useState([]);
	const [isLoading, setIsLoading] = useState(true);
	const [startingId, setStartingId] = useState(null);
	const [error, setError] = useState(null);
	const [message, setMessage] = useState('');
	const [scenarioAction, setScenarioAction] = useState(null);
	const [isImportOpen, setIsImportOpen] = useState(false);
	const startingAssignments = useRef(new Set());
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
		if (startingId) return false;
		setStartingId('scenario-action');
		setError(null);
		setMessage('');
		try {
			await action();
			await refreshProfessorScenarios();
			return true;
		} catch (requestError) {
			setError(requestError.message || 'Could not update the scenario');
			return false;
		} finally {
			setStartingId(null);
		}
	};

	const confirmArchive = async () => {
		const archived = await updateScenario(() => archiveScenario(scenarioAction.id));
		if (archived) {
			setMessage(`${scenarioAction.name} archived.`);
			setScenarioAction(null);
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
		if (startingAssignments.current.has(assignmentKey)) return;
		startingAssignments.current.add(assignmentKey);
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
			startingAssignments.current.delete(assignmentKey);
			setStartingId(null);
		}
	};

	return (
		<Flex px={{ base: 4, md: 10 }} pt={2} flexDir="column" flexGrow={1}>
			<Flex justify="space-between" align="center" mb={5}>
				<Box>
					<Heading>{isProfessor ? 'Scenarios' : 'My scenarios'}</Heading>
					{!isProfessor && (
						<Text color="gray.600" mt={1}>
							See what is assigned and pick up where you left off.
						</Text>
					)}
				</Box>
				{isProfessor && (
					<Button colorScheme="blue" onClick={() => setIsImportOpen(true)}>
						Import scenario JSON
					</Button>
				)}
			</Flex>
			{error && <RequestError title="Couldn’t complete the request" message={error} mb={4} />}
			{message && (
				<Alert status="success" mb={4}>
					<AlertIcon />
					{message}
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
						<PageLoadingState label="Loading scenarios…" />
					) : !isProfessor ? (
						<StudentScenarioSection
							scenarios={scenarios}
							runsByAssignment={runsByAssignment}
							startingId={startingId}
							onStart={start}
							onOpen={(run) => navigate(`/simulations/${run.id}`)}
						/>
					) : scenarios.length === 0 ? (
						<EmptyState
							title="No scenarios yet"
							description="No scenarios have been imported. Import a scenario JSON file to create your first teaching scenario."
							action={
								<Button colorScheme="blue" onClick={() => setIsImportOpen(true)}>
									Import scenario JSON
								</Button>
							}
						/>
					) : (
						<TableContainer>
							<Table variant="simple">
								<caption className="chakra-visually-hidden">Professor scenarios and revision status</caption>
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
																	isDisabled={Boolean(startingId)}
																>
																	Publish
																</Button>
															)}
															<Button
																size="sm"
																colorScheme="red"
																variant="outline"
																isDisabled={Boolean(startingId)}
																onClick={() =>
																	setScenarioAction({
																		id: scenario.id,
																		name: scenario.name,
																	})
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
			<ConfirmDialog
				isOpen={Boolean(scenarioAction)}
				title="Archive scenario"
				message={
					scenarioAction
						? `Archive ${scenarioAction.name}? Professors will no longer be able to publish or assign it.`
						: ''
				}
				confirmLabel="Archive"
				isBusy={startingId === 'scenario-action'}
				onCancel={() => setScenarioAction(null)}
				onConfirm={confirmArchive}
			/>
		</Flex>
	);
};

export default ScenarioOverview;
