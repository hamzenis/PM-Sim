import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Container,
	FormControl,
	FormLabel,
	Grid,
	Heading,
	Input,
	SimpleGrid,
	Spinner,
	Stack,
	Stat,
	StatLabel,
	StatNumber,
	Text,
} from '@chakra-ui/react';
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ApiError } from '../api/client';
import { completeSimulationTurn, getSimulationRun, listSimulationTurns, submitSimulationRun } from '../api/simulations';

const DEFAULT_ALLOCATION = {
	development: 50,
	unit_testing: 20,
	bug_fixing: 20,
	integration_testing: 10,
};

const SimulationV2 = () => {
	const { run_id: runId } = useParams();
	const navigate = useNavigate();
	const [run, setRun] = useState(null);
	const [allocation, setAllocation] = useState(DEFAULT_ALLOCATION);
	const [isLoading, setIsLoading] = useState(true);
	const [isSaving, setIsSaving] = useState(false);
	const [error, setError] = useState(null);
	const [events, setEvents] = useState([]);
	const [turns, setTurns] = useState([]);
	const [pendingKey, setPendingKey] = useState(null);

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

	const allocationTotal = useMemo(
		() => Object.values(allocation).reduce((total, value) => total + Number(value), 0),
		[allocation]
	);

	const updateAllocation = (name, value) => {
		setAllocation((current) => ({ ...current, [name]: Number(value) }));
	};

	const completeWeek = async () => {
		if (allocationTotal !== 100) {
			setError('Activity percentages must add up to 100.');
			return;
		}
		setIsSaving(true);
		setError(null);
		const idempotencyKey = pendingKey || window.crypto.randomUUID();
		setPendingKey(idempotencyKey);
		try {
			const response = await completeSimulationTurn(
				runId,
				{
					expected_version: run.version,
					allocation,
					hires: [],
					dismiss_employee_ids: [],
					overtime_hours_per_employee: 0,
					meeting_hours_per_employee: 0,
					training_hours_per_employee: 0,
				},
				idempotencyKey
			);
			setRun(response.run);
			setEvents(response.events);
			setPendingKey(null);
			setTurns(await listSimulationTurns(runId));
		} catch (requestError) {
			if (requestError instanceof ApiError && requestError.status === 409) {
				setPendingKey(null);
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
					<Heading size="md" mb={2}>
						Weekly activity allocation
					</Heading>
					<Text color={allocationTotal === 100 ? 'green.600' : 'red.600'} mb={5}>
						Allocated: {allocationTotal}% of team capacity
					</Text>
					<Grid templateColumns={{ base: '1fr', md: 'repeat(4, 1fr)' }} gap={5}>
						{Object.entries(allocation).map(([name, value]) => (
							<FormControl key={name}>
								<FormLabel>{name.replaceAll('_', ' ')}</FormLabel>
								<Input
									type="number"
									min={0}
									max={100}
									value={value}
									onChange={(event) => updateAllocation(name, event.target.value)}
								/>
							</FormControl>
						))}
					</Grid>
					<Stack direction={{ base: 'column', md: 'row' }} mt={7}>
						<Button
							colorScheme="blue"
							isLoading={isSaving}
							isDisabled={allocationTotal !== 100}
							onClick={completeWeek}
						>
							Complete week
						</Button>
						<Button variant="outline" isLoading={isSaving} onClick={submit}>
							Submit project
						</Button>
					</Stack>
				</Box>
			) : (
				<Box bg="white" borderRadius="2xl" p={7}>
					<Heading size="md">Final result</Heading>
					<pre>{JSON.stringify(run.final_result, null, 2)}</pre>
				</Box>
			)}

			{events.length > 0 && (
				<Box bg="white" borderRadius="2xl" p={7} mt={6}>
					<Heading size="sm" mb={3}>
						Latest events
					</Heading>
					{events.map((event, index) => (
						<Text key={`${event.kind}-${index}`}>{event.kind}</Text>
					))}
				</Box>
			)}

			{turns.length > 0 && (
				<Box bg="white" borderRadius="2xl" p={7} mt={6}>
					<Heading size="sm" mb={3}>
						Completed weeks
					</Heading>
					{turns.map((turn) => (
						<Text key={turn.week_number}>
							Week {turn.week_number}: {turn.events.length} visible event(s)
						</Text>
					))}
				</Box>
			)}
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
