import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import TurnHistory from './TurnHistory';

const decision = { allocation: {}, hires: [], dismiss_employee_ids: [] };
const renderEvents = (events) => render(<ChakraProvider><TurnHistory turns={[{ week_number: 1, decision, events }]} /></ChakraProvider>);

test('renders task-pool totals and an available difficulty breakdown', () => {
	renderEvents([
		{ kind: 'tasks_completed', values: { easy: 2, medium: 1, hard: 0 } },
		{ kind: 'bugs_fixed', values: { total: 4 } },
		{ kind: 'tasks_returned_to_backlog', values: { easy: 0, medium: 0, hard: 1 } },
	]);

	expect(screen.getByText(/3 tasks completed \(2 easy, 1 medium\)/i)).toBeInTheDocument();
	expect(screen.getByText(/4 bugs fixed/i)).toBeInTheDocument();
	expect(screen.getByText(/1 task returned to the backlog for more work \(1 hard\)/i)).toBeInTheDocument();
});

test('renders staffing and other public event payloads as student-facing copy', () => {
	renderEvents([
		{ kind: 'staffing_changed', values: { hired: 2, dismissed: 1, team_size: 6 } },
		{ kind: 'employee_dynamics_updated', values: { overtime_hours_per_employee: 3, meeting_hours_per_employee: 2, training_hours_per_employee: 1 } },
		{ kind: 'week_completed', values: { week: 1, working_days: 5 } },
		{ kind: 'simulation_finished', values: { outcome: 'deadline_reached' } },
	]);

	expect(screen.getByText(/2 hires, 1 dismissal; 6 employees total/i)).toBeInTheDocument();
	expect(screen.getByText(/3 overtime, 2 meeting, and 1 training hours per employee/i)).toBeInTheDocument();
	expect(screen.getByText(/week 1 completed \(5 working days\)/i)).toBeInTheDocument();
	expect(screen.getByText(/simulation finished: deadline reached/i)).toBeInTheDocument();
});

test('uses a readable fallback with visible payload for future event kinds', () => {
	renderEvents([{ kind: 'stakeholder_reviewed', values: { tasks_seen: 7, result: 'looks_good' } }]);
	expect(screen.getByText(/stakeholder reviewed — tasks seen: 7, result: looks good/i)).toBeInTheDocument();
});

test('never infers or names hidden quality concepts when they are absent', () => {
	renderEvents([{ kind: 'tasks_completed', values: { easy: 1, medium: 0, hard: 0 } }]);
	expect(screen.queryByText(/bugs created|incorrect specifications/i)).not.toBeInTheDocument();
});

test('defensively omits hidden engine events', () => {
	renderEvents([
		{ kind: 'bugs_created', values: { easy: 2, medium: 0, hard: 0 } },
		{ kind: 'incorrect_specifications_created', values: { easy: 1, medium: 0, hard: 0 } },
	]);
	expect(screen.getByText('No visible events.')).toBeInTheDocument();
	expect(screen.queryByText(/bugs created|incorrect specifications/i)).not.toBeInTheDocument();
});
