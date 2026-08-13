import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { getClassResult } from '../api/classes';
import ClassResultDetail from './ClassResultDetail';

vi.mock('../api/classes', () => ({ getClassResult: vi.fn() }));

const pool = (easy = 0, medium = 0, hard = 0) => ({ easy, medium, hard });
const state = (week) => ({
	week,
	elapsed_working_days: week * 5,
	remaining_working_days: 20 - week * 5,
	initial_budget: 1000,
	remaining_budget: 1000 - week * 100,
	tasks_todo: pool(8 - week),
	tasks_completed: pool(week * 2),
	tasks_unit_tested: pool(week),
	tasks_integration_tested: pool(week),
	known_bugs: pool(),
	employees: [{ stress: 0.2, motivation: 0.8, familiarity: 0.7 }],
});

const resultFixture = (overrides = {}) => ({
	run_id: 'run-uuid',
	student_id: 'student-uuid',
	scenario_revision_id: 'revision-uuid',
	student_username: 'learner',
	class_name: 'Project Management 101',
	scenario_name: 'Launch Week',
	status: 'submitted',
	current_week: 2,
	finished_at: '2026-01-02T15:04:00Z',
	engine_version: 'engine-secret',
	seed: 42,
	final_result: { outcome: 'submitted', score: { total: 88 } },
	current_state: state(2),
	turns: [{
		week_number: 1,
		submitted_at: '2026-01-01T15:04:00Z',
		decision: { allocation: { development: 75, unit_testing: 25 } },
		resulting_state: state(1),
		events: [{ kind: 'tasks_completed', easy: 4 }],
	}],
	contentAudit: {
		digestStatus: 'verified',
		divergences: [],
		deliveries: [{ id: 'delivery-uuid', definition: { title: 'Reflection prompt' }, definitionDigest: 'digest', status: 'completed', checkpoint: 'after_week', deliveredAt: '2026-01-01T16:00:00Z', turnWeekNumber: 1, responses: [], effects: [] }],
		effects: [],
	},
	...overrides,
});

const renderResult = async (result) => {
	getClassResult.mockResolvedValue(result);
	render(<ChakraProvider><MemoryRouter initialEntries={['/classes/class/results/run']}><Routes><Route path="/classes/:class_id/results/:run_id" element={<ClassResultDetail />} /></Routes></MemoryRouter></ChakraProvider>);
	await waitFor(() => expect(screen.getByRole('heading', { name: 'Result for learner' })).toBeInTheDocument());
};

test('shows all student-dashboard progress graphs for a completed result and preserves result details', async () => {
	const NativeDateTimeFormat = Intl.DateTimeFormat;
	vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(function StableDateTimeFormat(_locale, options) { return new NativeDateTimeFormat('en-US', { ...options, timeZone: 'UTC' }); });
	await renderResult(resultFixture());

	expect(screen.getByText('Project Management 101 · Launch Week')).toBeInTheDocument();
	expect(screen.getByText('Jan 2, 2026, 3:04 PM')).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Progress at a glance' })).toBeInTheDocument();
	['Budget trend', 'Task progress', 'Employee status'].forEach((name) =>
		expect(screen.getByRole('heading', { name })).toBeInTheDocument()
	);
	expect(screen.getByText('Schedule remaining')).toBeInTheDocument();
	expect(screen.getByText('Tasks completed')).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Final result' })).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Weekly decisions and outcomes' })).toBeInTheDocument();
});

test('passes current state and resulting-state history through the reused dashboard selectors for an active result', async () => {
	await renderResult(resultFixture({ status: 'active', finished_at: null, final_result: null }));

	expect(screen.getByRole('heading', { name: 'Progress at a glance' })).toBeInTheDocument();
	expect(screen.getByText('Budget trend data')).toBeInTheDocument();
	expect(screen.getByText('Task progress trend data')).toBeInTheDocument();
	expect(screen.getByText('Employee status trend data')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: /Week 1: actual cost \$100\.00/ })).toBeInTheDocument();
	expect(screen.getByRole('button', { name: /Week 2: actual cost \$200\.00/ })).toBeInTheDocument();
	expect(screen.getByRole('button', { name: /Week 1: Completed 2/ })).toBeInTheDocument();
	expect(screen.getByRole('button', { name: /Week 2: Completed 4/ })).toBeInTheDocument();
});

test('handles an empty no-turn result without showing incomplete graphs', async () => {
	await renderResult(resultFixture({ current_week: 0, current_state: {}, turns: [], status: 'active', finished_at: null, final_result: null }));

	expect(screen.queryByRole('heading', { name: 'Progress at a glance' })).not.toBeInTheDocument();
	expect(screen.getByText('No completed weeks')).toBeInTheDocument();
});

test('keeps technical identifiers hidden by default while replay audit information remains available', async () => {
	await renderResult(resultFixture());

	expect(screen.getByRole('heading', { name: 'Teaching-content timeline' })).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Reflection prompt' })).toBeInTheDocument();
	const details = screen.getAllByText('Technical details').map((node) => node.closest('details'));
	details.forEach((detail) => expect(detail).not.toHaveAttribute('open'));
	expect(screen.getByText(/run-uuid/)).not.toBeVisible();
	expect(screen.getByText(/student-uuid/)).not.toBeVisible();
	screen.getAllByText(/delivery-uuid/).forEach((node) => expect(node).not.toBeVisible());
	const runDetails = details.at(-1);
	fireEvent.click(within(runDetails).getByText('Technical details'));
	expect(runDetails).toHaveAttribute('open');
	expect(screen.getByText(/run-uuid/)).toBeVisible();
});
