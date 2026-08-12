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
vi.mock('../components/SimulationV2/TurnHistory', () => ({ default: () => null }));
vi.mock('../components/SimulationV2/AuthoredContent/ContentPanel', () => ({
	default: ({ version }) => <div>Run version {version}</div>,
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
	version,
	current_week: version - 1,
	status: 'active',
	deliveries: [],
	state: {
		employees: [],
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

test('completes one turn and applies its run version update once', async () => {
	getSimulationRun.mockResolvedValue(run(1));
	listSimulationTurns.mockResolvedValue([]);
	completeSimulationTurn.mockResolvedValue({ run: run(2) });

	await renderSimulation();
	await screen.findByText('Run version 1');
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
