import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { completeSimulationTurn, getSimulationRun, listSimulationTurns } from '../api/simulations';
import { SubmissionReadiness, submissionReadiness } from './SimulationV2';

vi.mock('../api/simulations', () => ({
	completeSimulationTurn: vi.fn(),
	getSimulationRun: vi.fn(),
	listSimulationTurns: vi.fn(),
	submitSimulationRun: vi.fn(),
}));

vi.mock('../components/SimulationV2/WeeklyDecisionForm', () => ({
	default: () => null,
	decisionIsValid: () => true,
}));
vi.mock('../components/SimulationV2/Dashboard/DashboardStats', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/Dashboard/TaskProgressDashboard', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/Dashboard/BudgetTrendChart', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/Dashboard/EmployeeStatusChart', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/Dashboard/ProjectHealthSummary', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/TurnHistory', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/AuthoredContent/ContentPanel', () => ({
	default: ({ version, deliveries = [], presentation }) => <div>Run version {version}{deliveries.some((entry) => entry.required && entry.status === 'actionable') && <p>Required before continuing: {deliveries[0].prompt}</p>}{presentation?.messages?.map((message) => <p key={message}>{message}</p>)}</div>,
}));

beforeEach(() => {
	vi.clearAllMocks();
});

const pool = (easy = 0, medium = 0, hard = 0) => ({ easy, medium, hard });

test('defines readiness as integration-tested tasks divided by all project tasks', () => {
	const state = {
		tasks_todo: pool(2, 1),
		tasks_completed: pool(3, 2),
		tasks_integration_tested: pool(1, 1),
	};

	expect(submissionReadiness(state)).toEqual({
		integrationTestedTasks: 2,
		totalProjectTasks: 8,
		percentage: 25,
	});
});

test('shows the non-overlapping readiness ratio without blocking early submission', () => {
	render(
		<ChakraProvider>
			<SubmissionReadiness
				state={{
					tasks_todo: pool(2),
					tasks_completed: pool(8),
					tasks_integration_tested: pool(7),
				}}
			/>
		</ChakraProvider>
	);

	expect(screen.getByText('7 of 10 tasks integration tested (70%)')).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Submission readiness: 7 of 10 tasks integration tested' })).toBeInTheDocument();
	expect(screen.getByText(/you may submit now/i)).toBeInTheDocument();
});

const run = (version) => ({
	id: '11111111-1111-4111-8111-111111111111',
	scenario_revision_id: '22222222-2222-4222-8222-222222222222',
	version,
	current_week: version - 1,
	status: 'active',
	scenario_title: 'Apollo Delivery Project',
	scenario_briefing: 'Deliver a reliable product within the agreed schedule and budget.',
	deliveries: [],
	state: {
		employees: [],
		elapsed_working_days: 5,
		remaining_working_days: 15,
		initial_budget: 100000,
		remaining_budget: 90000,
		tasks_todo: pool(1),
		tasks_completed: pool(),
		tasks_integration_tested: pool(),
	},
});

const renderSimulation = async () => {
	const { default: SimulationV2 } = await import('./SimulationV2');
	return render(
		<ChakraProvider>
			<MemoryRouter initialEntries={['/simulations/run-1']}>
				<Routes>
					<Route path="/simulations/:run_id" element={<SimulationV2 />} />
				</Routes>
			</MemoryRouter>
		</ChakraProvider>
	);
};

test('loads the selected run and its turns once on initial mount', async () => {
	getSimulationRun.mockResolvedValue(run(1));
	listSimulationTurns.mockResolvedValue([]);

	await renderSimulation();

	expect(await screen.findByText('Run version 1')).toBeInTheDocument();
	expect(getSimulationRun).toHaveBeenCalledTimes(1);
	expect(getSimulationRun).toHaveBeenCalledWith('run-1');
	expect(listSimulationTurns).toHaveBeenCalledTimes(1);
	expect(listSimulationTurns).toHaveBeenCalledWith('run-1');
});

test('passes the backend presentation projection to scenario updates', async () => {
	getSimulationRun.mockResolvedValue({ ...run(1), presentation: { messages: ['Week 4 sponsor notice'] } });
	listSimulationTurns.mockResolvedValue([]);

	await renderSimulation();

	expect(await screen.findByText('Week 4 sponsor notice')).toBeInTheDocument();
});

test('shows the briefing, scenario heading, current week, and status without internal UUIDs', async () => {
	getSimulationRun.mockResolvedValue(run(1));
	listSimulationTurns.mockResolvedValue([]);

	await renderSimulation();

	expect(await screen.findByRole('dialog', { name: 'Scenario briefing' })).toBeInTheDocument();
	expect(screen.getByText(/deliver a reliable product/i)).toBeInTheDocument();
	fireEvent.click(screen.getByRole('button', { name: 'Start simulation' }));
	await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Scenario briefing' })).not.toBeInTheDocument());
	expect(screen.getByRole('heading', { name: 'Apollo Delivery Project' })).toBeInTheDocument();
	expect(screen.getByText('Week 1 · Make decisions for the next project week')).toBeInTheDocument();
	expect(screen.getByText('In progress')).toBeInTheDocument();
	expect(screen.queryByText('11111111-1111-4111-8111-111111111111')).not.toBeInTheDocument();
	expect(screen.queryByText('22222222-2222-4222-8222-222222222222')).not.toBeInTheDocument();
});

test('makes blocking authored content the required action', async () => {
	getSimulationRun.mockResolvedValue({ ...run(1), deliveries: [{ sequence_entry_id: '33333333-3333-4333-8333-333333333333', required: true, status: 'actionable', prompt: 'Choose a response' }] });
	listSimulationTurns.mockResolvedValue([]);

	await renderSimulation();
	fireEvent.click(await screen.findByRole('button', { name: 'Start simulation' }));

	expect(screen.getByText(/required before continuing: choose a response/i)).toBeInTheDocument();
	expect(screen.getByText('Scenario response required')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'Complete week' })).toBeDisabled();
	expect(screen.queryByText('33333333-3333-4333-8333-333333333333')).not.toBeInTheDocument();
});

test('announces a useful loading state', async () => {
	getSimulationRun.mockReturnValue(new Promise(() => {}));
	listSimulationTurns.mockReturnValue(new Promise(() => {}));
	await renderSimulation();
	expect(screen.getByText('Loading your simulation')).toBeInTheDocument();
	expect(screen.getByText(/latest project state/i)).toBeInTheDocument();
});

test('preserves turn error detail and offers a retry', async () => {
	getSimulationRun.mockResolvedValue(run(1));
	listSimulationTurns.mockResolvedValue([]);
	completeSimulationTurn.mockRejectedValue(new Error('Network connection was interrupted.'));
	await renderSimulation();
	fireEvent.click(await screen.findByRole('button', { name: 'Start simulation' }));
	fireEvent.click(screen.getByRole('button', { name: 'Complete week' }));
	expect(await screen.findByText(/network connection was interrupted.*retry the same request/i)).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'Retry week' })).toBeInTheDocument();
});

test('shows the completed status and final result', async () => {
	getSimulationRun.mockResolvedValue({ ...run(2), status: 'submitted', final_result: { outcome: 'success', score: { total: 91 }, accepted_tasks: 8, rejected_tasks: 2 } });
	listSimulationTurns.mockResolvedValue([]);
	await renderSimulation();
	fireEvent.click(await screen.findByRole('button', { name: 'Start simulation' }));
	await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Scenario briefing' })).not.toBeInTheDocument());
	expect(screen.getByText('Completed')).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Final result' })).toBeInTheDocument();
	expect(screen.getByText('91/100')).toBeInTheDocument();
});

test('completes one turn and applies its run version update once', async () => {
	getSimulationRun.mockResolvedValue(run(1));
	listSimulationTurns.mockResolvedValue([]);
	completeSimulationTurn.mockResolvedValue({ run: run(2) });

	await renderSimulation();
	await screen.findByText('Run version 1');
	fireEvent.click(screen.getByRole('button', { name: 'Start simulation' }));
	await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Scenario briefing' })).not.toBeInTheDocument());
	listSimulationTurns.mockClear();

	fireEvent.click(screen.getByRole('button', { name: 'Complete week' }));

	expect(await screen.findByText('Run version 2')).toBeInTheDocument();
	await waitFor(() => expect(listSimulationTurns).toHaveBeenCalledTimes(1));
	expect(completeSimulationTurn).toHaveBeenCalledTimes(1);
	expect(completeSimulationTurn).toHaveBeenCalledWith(
		'run-1',
		expect.objectContaining({ expected_version: 1 }),
		expect.any(String)
	);
	expect(getSimulationRun).toHaveBeenCalledTimes(1);
});
