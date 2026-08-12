import {
	Alert,
	AlertIcon,
	Badge,
	Box,
	Button,
	Container,
	Drawer,
	DrawerBody,
	DrawerCloseButton,
	DrawerContent,
	DrawerHeader,
	DrawerOverlay,
	Flex,
	Heading,
	Modal,
	ModalBody,
	ModalCloseButton,
	ModalContent,
	ModalFooter,
	ModalHeader,
	ModalOverlay,
	Progress,
	Spinner,
	Stack,
	Text,
} from '@chakra-ui/react';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { completeSimulationTurn, getSimulationRun, listSimulationTurns, submitSimulationRun } from '../api/simulations';
import FinalResult from '../components/SimulationV2/FinalResult';
import TurnHistory from '../components/SimulationV2/TurnHistory';
import WeeklyDecisionForm, { decisionIsValid } from '../components/SimulationV2/WeeklyDecisionForm';
import ConfirmDialog from '../components/ClassManagement/ConfirmDialog';
import DashboardStats from '../components/SimulationV2/Dashboard/DashboardStats';
import TaskProgressDashboard from '../components/SimulationV2/Dashboard/TaskProgressDashboard';
import BudgetTrendChart from '../components/SimulationV2/Dashboard/BudgetTrendChart';
import EmployeeStatusChart from '../components/SimulationV2/Dashboard/EmployeeStatusChart';
import HelpContent from '../components/HelpContent';
import { taskPoolTotal } from '../components/SimulationV2/Dashboard/taskPool';
import ContentPanel from '../components/SimulationV2/AuthoredContent/ContentPanel';
import { selectContentState } from '../components/SimulationV2/AuthoredContent/selectors';

const SUBMISSION_READINESS_BENCHMARK = 80;

export const submissionReadiness = (state) => {
	const integrationTestedTasks = taskPoolTotal(state?.tasks_integration_tested);
	const totalProjectTasks = taskPoolTotal(state?.tasks_todo) + taskPoolTotal(state?.tasks_completed);
	const percentage = totalProjectTasks === 0 ? 0 : (integrationTestedTasks / totalProjectTasks) * 100;

	return { integrationTestedTasks, totalProjectTasks, percentage };
};

export const SubmissionReadiness = ({ state }) => {
	const { integrationTestedTasks, totalProjectTasks, percentage } = submissionReadiness(state);
	const roundedPercentage = Math.round(percentage);
	const isBelowBenchmark = percentage < SUBMISSION_READINESS_BENCHMARK;

	return (
		<Box mb={6}>
			<Flex justify="space-between" align="baseline" gap={3} mb={2}>
				<Text fontWeight="semibold">Submission readiness</Text>
				<Text fontSize="sm" color="gray.600">
					{integrationTestedTasks} of {totalProjectTasks} tasks integration tested ({roundedPercentage}%)
				</Text>
			</Flex>
			<Progress
				value={Math.min(percentage, 100)}
				colorScheme={isBelowBenchmark ? 'orange' : 'green'}
				borderRadius="full"
				aria-label={`Submission readiness: ${integrationTestedTasks} of ${totalProjectTasks} tasks integration tested`}
			/>
			<Text mt={2} fontSize="sm" color={isBelowBenchmark ? 'orange.700' : 'green.700'}>
				{isBelowBenchmark
					? 'You may submit now, but only integration-tested tasks count as accepted. Reaching 80% is recommended, not required.'
					: 'You have reached the recommended 80% integration-tested benchmark.'}
			</Text>
		</Box>
	);
};

const DEFAULT_ALLOCATION = {
	development: 50,
	unit_testing: 20,
	bug_fixing: 20,
	integration_testing: 10,
};

const newDecision = () => ({
	allocation: { ...DEFAULT_ALLOCATION },
	hires: [],
	dismiss_employee_ids: [],
	overtime_hours_per_employee: 0,
	meeting_hours_per_employee: 0,
	training_hours_per_employee: 0,
});

const SimulationV2 = () => {
	const { run_id: runId } = useParams();
	const navigate = useNavigate();
	const [run, setRun] = useState(null);
	const [decision, setDecision] = useState(newDecision);
	const [isLoading, setIsLoading] = useState(true);
	const [isSaving, setIsSaving] = useState(false);
	const [error, setError] = useState(null);
	const [turns, setTurns] = useState([]);
	const [pendingSubmission, setPendingSubmission] = useState(null);
	const [isSubmitOpen, setIsSubmitOpen] = useState(false);
	const [isBriefingOpen, setIsBriefingOpen] = useState(true);
	const [drawer, setDrawer] = useState(null);

	// Loading reads only the route's runId. It must be recreated when that identity changes so
	// the effect below loads the newly selected run; stable React state setters need no dependency.
	const load = useCallback(async () => {
		setIsLoading(true);
		setError(null);
		try {
			const [loadedRun, loadedTurns] = await Promise.all([getSimulationRun(runId), listSimulationTurns(runId)]);
			setRun(loadedRun);
			setTurns(loadedTurns);
		} catch (requestError) {
			setError(requestError.message || 'Could not load the simulation');
		} finally {
			setIsLoading(false);
		}
	}, [runId]);

	useEffect(() => {
		load();
	}, [load]);

	const isDecisionValid = useMemo(() => decisionIsValid(decision), [decision]);
	const contentState = useMemo(() => selectContentState(run?.deliveries), [run?.deliveries]);

	useEffect(() => {
		if (!contentState.earliestActionableRequiredEntry) return;
		const element = document.getElementById(`content-entry-${contentState.earliestActionableRequiredEntry.sequence_entry_id}`);
		element?.focus();
		element?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
	}, [contentState.earliestActionableRequiredEntry]);

	const completeWeek = async () => {
		if (contentState.isBlocking) {
			setError('Complete the required scenario content before completing this week.');
			const element = document.getElementById(`content-entry-${contentState.earliestActionableRequiredEntry.sequence_entry_id}`);
			element?.focus();
			element?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
			return;
		}
		if (!isDecisionValid) {
			setError('Check that activity percentages total 100 and that all values are valid.');
			return;
		}
		setIsSaving(true);
		setError(null);
		const submission = pendingSubmission || {
			key: window.crypto.randomUUID(),
			decision,
		};
		setPendingSubmission(submission);
		try {
			const response = await completeSimulationTurn(
				runId,
				{
					expected_version: run.version,
					...submission.decision,
				},
				submission.key
			);
			setRun(response.run);
			setDecision(newDecision());
			setPendingSubmission(null);
			setTurns(await listSimulationTurns(runId));
		} catch (requestError) {
			if (requestError instanceof ApiError && requestError.status === 409) {
				setPendingSubmission(null);
				await load();
				setError('This run changed in another browser tab. Review the updated state before trying again.');
			} else {
				setError(`${requestError.message || 'Could not complete the week'} You can retry the same request.`);
			}
		} finally {
			setIsSaving(false);
		}
	};

	const submit = async () => {
		setIsSaving(true);
		setError(null);
		try {
			setRun(await submitSimulationRun(runId, run.version));
			setIsSubmitOpen(false);
		} catch (requestError) {
			setError(requestError.message || 'Could not submit the simulation');
		} finally {
			setIsSaving(false);
		}
	};

	if (isLoading)
		return (
			<Container py={24} textAlign="center" aria-live="polite">
				<Spinner size="xl" color="blue.500" mb={5} />
				<Heading size="md">Loading your simulation</Heading>
				<Text color="gray.600" mt={2}>Getting the latest project state and week history…</Text>
			</Container>
		);
	if (!run)
		return (
			<Container py={16}>
				<Alert status="error">
					<AlertIcon />
					<Box><Text fontWeight="bold">We couldn’t load this simulation.</Text><Text>{error || 'Check your connection and try again.'}</Text></Box>
				</Alert>
			</Container>
		);

	const state = run.state;
	const readiness = submissionReadiness(state);
	const isBelowReadinessBenchmark = readiness.percentage < SUBMISSION_READINESS_BENCHMARK;
	const totalScheduleDays = Number(state.elapsed_working_days || 0) + Number(state.remaining_working_days || 0);
	const scheduleProgress = totalScheduleDays ? (Number(state.elapsed_working_days || 0) / totalScheduleDays) * 100 : 0;
	const statusLabel = run.status === 'active' ? 'In progress' : 'Completed';
	return (
		<Container maxW="6xl" py={8}>
			<Flex mb={4} gap={3} align="center" wrap="wrap">
				<Button variant="link" mr="auto" onClick={() => navigate('/scenarios')}>
					← Scenarios
				</Button>
				<Button size="sm" variant="outline" onClick={() => setDrawer('briefing')}>
					Scenario briefing
				</Button>
				<Button size="sm" variant="outline" onClick={() => setDrawer('help')}>
					Help
				</Button>
			</Flex>
			<Box as="header" bg="white" borderRadius="2xl" p={{ base: 5, md: 7 }} mb={6}>
				<Flex justify="space-between" align={{ base: 'flex-start', md: 'center' }} gap={4} direction={{ base: 'column', md: 'row' }}>
					<Box>
						<Text color="blue.600" fontWeight="bold" fontSize="sm" textTransform="uppercase" letterSpacing="wide">Student simulation</Text>
						<Heading as="h1" size="xl" mt={1}>{run.scenario_title || 'Project management simulation'}</Heading>
						<Text color="gray.600" mt={2}>Week {run.current_week + 1} · Make decisions for the next project week</Text>
					</Box>
					<Badge colorScheme={run.status === 'active' ? 'blue' : 'green'} fontSize="sm" px={3} py={1} borderRadius="full">{statusLabel}</Badge>
				</Flex>
				<Box mt={6}>
					<Flex justify="space-between" mb={2}><Text fontWeight="semibold">Schedule progress</Text><Text color="gray.600" fontSize="sm">{Number(state.elapsed_working_days || 0).toLocaleString()} of {totalScheduleDays.toLocaleString()} working days used</Text></Flex>
					<Progress value={scheduleProgress} colorScheme="blue" borderRadius="full" aria-label={`Schedule progress: ${Math.round(scheduleProgress)}%`} />
				</Box>
			</Box>
			{error && (
				<Alert status="error" mb={5}>
					<AlertIcon />
					{error}
				</Alert>
			)}
			<Box as="section" aria-labelledby="project-health-heading">
				<Heading id="project-health-heading" size="md" mb={4}>Project health</Heading>
				<DashboardStats state={state} turns={turns} />
				<BudgetTrendChart state={state} turns={turns} isComplete={run.status !== 'active'} />
				<EmployeeStatusChart state={state} turns={turns} />
				<TaskProgressDashboard state={state} turns={turns} />
			</Box>
			<ContentPanel
				runId={runId}
				version={run.version}
				deliveries={run.deliveries}
				onRunChange={setRun}
				onConflict={load}
			/>

			{run.status === 'active' ? (
				<Box bg="white" borderWidth="1px" borderColor="blue.200" borderRadius="2xl" p={{ base: 5, md: 7 }} aria-labelledby="current-action-heading">
					<Text color="blue.600" fontWeight="bold" fontSize="sm" textTransform="uppercase" letterSpacing="wide">Current required action</Text>
					<SubmissionReadiness state={state} />
					<Heading id="current-action-heading" size="lg" mb={2}>
						Plan week {run.current_week + 1}
					</Heading>
					<Text color="gray.600" mb={6}>Allocate team capacity, set team activities, and review staffing before completing the week.</Text>
					<WeeklyDecisionForm
						decision={decision}
						employees={state.employees || []}
						employeeTypes={run.employee_types || []}
						isDisabled={Boolean(pendingSubmission) || contentState.isBlocking}
						onChange={setDecision}
					/>
					<Stack direction={{ base: 'column', md: 'row' }} mt={7}>
						{contentState.isBlocking && (
							<Alert status="info" variant="left-accent"><AlertIcon /><Box><Text fontWeight="bold">Scenario response required</Text><Text>Complete the highlighted learning activity above to unlock this week’s decision.</Text></Box></Alert>
						)}
						<Button
							colorScheme="blue"
							isLoading={isSaving}
							isDisabled={!isDecisionValid || contentState.isBlocking}
							onClick={completeWeek}
						>
							{pendingSubmission ? 'Retry week' : 'Complete week'}
						</Button>
						{pendingSubmission && (
							<Button variant="ghost" onClick={() => setPendingSubmission(null)}>
								Discard retry
							</Button>
						)}
						<Button variant="outline" isLoading={isSaving} onClick={() => setIsSubmitOpen(true)}>
							Submit project
						</Button>
					</Stack>
				</Box>
			) : (
				<FinalResult result={run.final_result} />
			)}

			<TurnHistory turns={turns} />
			<ConfirmDialog
				isOpen={isSubmitOpen}
				title="Submit project"
				message={
					isBelowReadinessBenchmark
						? `Only ${readiness.integrationTestedTasks} of ${readiness.totalProjectTasks} tasks are integration tested. You can still submit, but only integration-tested tasks count as accepted, and you will not be able to complete another week.`
						: 'Submit the project now? Only integration-tested tasks count as accepted, and you will not be able to complete another week.'
				}
				confirmLabel="Submit project"
				isBusy={isSaving}
				onCancel={() => setIsSubmitOpen(false)}
				onConfirm={submit}
			/>
			<Modal isOpen={isBriefingOpen} onClose={() => setIsBriefingOpen(false)} size="xl" isCentered>
				<ModalOverlay />
				<ModalContent>
					<ModalHeader>Scenario briefing</ModalHeader>
					<ModalCloseButton />
					<ModalBody>
						<BriefingText briefing={run.scenario_briefing} />
					</ModalBody>
					<ModalFooter>
						<Button colorScheme="blue" onClick={() => setIsBriefingOpen(false)}>
							Start simulation
						</Button>
					</ModalFooter>
				</ModalContent>
			</Modal>
			<Drawer isOpen={Boolean(drawer)} placement="right" size="lg" onClose={() => setDrawer(null)}>
				<DrawerOverlay />
				<DrawerContent>
					<DrawerCloseButton />
					<DrawerHeader>{drawer === 'help' ? 'Help' : 'Scenario briefing'}</DrawerHeader>
					<DrawerBody pb={8}>
						{drawer === 'help' ? (
							<HelpContent showIntroduction={false} />
						) : (
							<BriefingText briefing={run.scenario_briefing} />
						)}
					</DrawerBody>
				</DrawerContent>
			</Drawer>
		</Container>
	);
};

const BriefingText = ({ briefing }) => (
	<Text whiteSpace="pre-wrap" color={briefing ? 'gray.700' : 'gray.500'}>
		{briefing || 'No scenario briefing was provided.'}
	</Text>
);

export default SimulationV2;
