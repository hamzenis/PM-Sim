import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Container,
	Heading,
	SimpleGrid,
	Spinner,
	Stack,
	Stat,
	StatLabel,
	StatNumber,
} from '@chakra-ui/react';
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { completeSimulationTurn, getSimulationRun, listSimulationTurns, submitSimulationRun } from '../api/simulations';
import FinalResult from '../components/SimulationV2/FinalResult';
import TurnHistory from '../components/SimulationV2/TurnHistory';
import WeeklyDecisionForm, { decisionIsValid } from '../components/SimulationV2/WeeklyDecisionForm';
import ConfirmDialog from '../components/ClassManagement/ConfirmDialog';

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

	const load = async () => {
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
	};

	useEffect(() => {
		load();
		// The run ID is the identity of this screen; load is intentionally local to the component.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [runId]);

	const isDecisionValid = useMemo(() => decisionIsValid(decision), [decision]);

	const completeWeek = async () => {
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
			<Container py={16}>
				<Spinner size="xl" />
			</Container>
		);
	if (!run)
		return (
			<Container py={16}>
				<Alert status="error">
					<AlertIcon />
					{error}
				</Alert>
			</Container>
		);

	const state = run.state;
	return (
		<Container maxW="6xl" py={8}>
			<Button variant="link" mb={4} onClick={() => navigate('/scenarios')}>
				← Scenarios
			</Button>
			<Heading mb={6}>Simulation week {run.current_week + 1}</Heading>
			{error && (
				<Alert status="error" mb={5}>
					<AlertIcon />
					{error}
				</Alert>
			)}
			<SimpleGrid columns={{ base: 1, md: 4 }} spacing={4} mb={8}>
				<StatCard label="Budget remaining" value={state.remaining_budget} />
				<StatCard label="Working days remaining" value={state.remaining_working_days} />
				<StatCard label="Employees" value={state.employees?.length || 0} />
				<StatCard label="Run status" value={run.status} />
			</SimpleGrid>

			{run.status === 'active' ? (
				<Box bg="white" borderRadius="2xl" p={7}>
					<Heading size="md" mb={5}>
						Weekly decision
					</Heading>
					<WeeklyDecisionForm
						decision={decision}
						employees={state.employees || []}
						employeeTypes={run.employee_types || []}
						isDisabled={Boolean(pendingSubmission)}
						onChange={setDecision}
					/>
					<Stack direction={{ base: 'column', md: 'row' }} mt={7}>
						<Button
							colorScheme="blue"
							isLoading={isSaving}
							isDisabled={!isDecisionValid}
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
				message="Submit the project now? You will not be able to complete another week."
				confirmLabel="Submit project"
				isBusy={isSaving}
				onCancel={() => setIsSubmitOpen(false)}
				onConfirm={submit}
			/>
		</Container>
	);
};

const StatCard = ({ label, value }) => (
	<Box bg="white" borderRadius="xl" p={5}>
		<Stat>
			<StatLabel>{label}</StatLabel>
			<StatNumber>{String(value ?? '—')}</StatNumber>
		</Stat>
	</Box>
);

export default SimulationV2;
