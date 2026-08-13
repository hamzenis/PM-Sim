import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { archiveScenario, listAvailableScenarios, listOwnedScenarios } from '../api/scenarios';
import { listSimulationRuns, startSimulationRun } from '../api/simulations';
import { AuthContext } from '../context/AuthProvider';
import ScenarioOverview, { scenarioAssignmentKey } from './ScenarioOverview';

vi.mock('../api/scenarios', () => ({
	archiveScenario: vi.fn(),
	createScenario: vi.fn(),
	listAvailableScenarios: vi.fn(),
	listOwnedScenarios: vi.fn(),
	publishScenarioRevision: vi.fn(),
	validateScenario: vi.fn(),
}));
vi.mock('../api/simulations', () => ({ listSimulationRuns: vi.fn(), startSimulationRun: vi.fn() }));

const revisionId = '11111111-1111-4111-8111-111111111111';
const classId = '22222222-2222-4222-8222-222222222222';
const runId = '33333333-3333-4333-8333-333333333333';
const scenario = {
	id: revisionId,
	class_id: classId,
	class_name: 'Project Management 101',
	revision_number: 2,
	definition: { name: 'New Product Launch', description: 'Guide a team through a high-stakes product launch.' },
};

const renderStudentOverview = () =>
	render(
		<ChakraProvider>
			<AuthContext.Provider value={{ currentUser: { role: 'student' } }}>
				<MemoryRouter initialEntries={['/scenarios']}>
					<Routes>
						<Route path="/scenarios" element={<ScenarioOverview />} />
						<Route path="/simulations/:run_id" element={<div>Simulation destination</div>} />
					</Routes>
				</MemoryRouter>
			</AuthContext.Provider>
		</ChakraProvider>
	);

const renderProfessorOverview = () =>
	render(
		<ChakraProvider>
			<AuthContext.Provider value={{ currentUser: { role: 'professor' } }}>
				<MemoryRouter>
					<ScenarioOverview />
				</MemoryRouter>
			</AuthContext.Provider>
		</ChakraProvider>
	);

beforeEach(() => {
	vi.clearAllMocks();
	listAvailableScenarios.mockResolvedValue([scenario]);
	listOwnedScenarios.mockResolvedValue([]);
	listSimulationRuns.mockResolvedValue([]);
});

test('uses both class and revision IDs for scenario assignments', () => {
	expect(scenarioAssignmentKey('class-1', 'revision-1')).toBe('class-1:revision-1');
	expect(scenarioAssignmentKey('class-2', 'revision-1')).not.toBe(scenarioAssignmentKey('class-1', 'revision-1'));
});

test('shows a helpful empty state when no scenarios are assigned', async () => {
	listAvailableScenarios.mockResolvedValue([]);
	renderStudentOverview();
	expect(await screen.findByRole('heading', { name: 'No scenarios assigned yet' })).toBeInTheDocument();
	expect(screen.getByText(/professor may not have assigned/i)).toBeInTheDocument();
});

test('shows an available scenario as a student-friendly card', async () => {
	renderStudentOverview();
	expect(await screen.findByRole('heading', { name: 'New Product Launch' })).toBeInTheDocument();
	expect(screen.getByText('Project Management 101')).toBeInTheDocument();
	expect(screen.getByText(scenario.definition.description)).toBeInTheDocument();
	expect(screen.getByText('Ready to start')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument();
});

test('shows week progress and continues an active run', async () => {
	listSimulationRuns.mockResolvedValue([
		{ id: runId, class_id: classId, scenario_revision_id: revisionId, status: 'active', current_week: 3 },
	]);
	renderStudentOverview();
	expect(await screen.findByText('In progress')).toBeInTheDocument();
	expect(screen.getByText('Week 3 completed')).toBeInTheDocument();
	fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
	expect(await screen.findByText('Simulation destination')).toBeInTheDocument();
});

test('shows a completed run with a result action', async () => {
	listSimulationRuns.mockResolvedValue([
		{ id: runId, class_id: classId, scenario_revision_id: revisionId, status: 'deadline_reached', current_week: 8 },
	]);
	renderStudentOverview();
	expect(await screen.findByText('Completed')).toBeInTheDocument();
	expect(screen.getByText('Finished after week 8')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'View result' })).toBeInTheDocument();
	expect(screen.queryByText('deadline_reached')).not.toBeInTheDocument();
});

test('shows a clear error and permits retry when starting fails', async () => {
	startSimulationRun.mockRejectedValueOnce(new Error('network unavailable')).mockResolvedValueOnce({ id: runId });
	renderStudentOverview();
	fireEvent.click(await screen.findByRole('button', { name: 'Start' }));
	expect(await screen.findByRole('alert')).toHaveTextContent('Could not start the simulation');
	await waitFor(() => expect(screen.getByRole('button', { name: 'Start' })).toBeEnabled());
	fireEvent.click(screen.getByRole('button', { name: 'Start' }));
	expect(await screen.findByText('Simulation destination')).toBeInTheDocument();
});

test('does not expose UUIDs and prevents duplicate starts while a request is active', async () => {
	let resolveStart;
	startSimulationRun.mockReturnValue(
		new Promise((resolve) => {
			resolveStart = resolve;
		})
	);
	const { container } = renderStudentOverview();
	const startButton = await screen.findByRole('button', { name: 'Start' });
	fireEvent.click(startButton);
	fireEvent.click(startButton);
	expect(startSimulationRun).toHaveBeenCalledTimes(1);
	expect(startSimulationRun).toHaveBeenCalledWith(revisionId, expect.any(Number), classId);
	expect(container.textContent).not.toMatch(/[0-9a-f]{8}-[0-9a-f-]{27,}/i);
	resolveStart({ id: runId });
	await screen.findByText('Simulation destination');
});

test('names the scenario and waits for confirmation before archiving', async () => {
	listOwnedScenarios.mockResolvedValue([
		{ id: revisionId, name: 'New Product Launch', latest_revision: 2, latest_status: 'published' },
	]);
	archiveScenario.mockResolvedValue({});
	renderProfessorOverview();
	fireEvent.click(await screen.findByRole('button', { name: 'Archive' }));
	expect(screen.getByRole('alertdialog')).toHaveTextContent('Archive New Product Launch?');
	expect(archiveScenario).not.toHaveBeenCalled();
	fireEvent.click(screen.getByRole('button', { name: 'Archive' }));
	await waitFor(() => expect(archiveScenario).toHaveBeenCalledTimes(1));
	expect(await screen.findByText('New Product Launch archived.')).toBeInTheDocument();
});
