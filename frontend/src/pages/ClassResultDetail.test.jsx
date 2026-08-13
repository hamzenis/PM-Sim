import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { getClassResult } from '../api/classes';
import ClassResultDetail from './ClassResultDetail';

vi.mock('../api/classes', () => ({ getClassResult: vi.fn() }));

test('shows a readable result summary, localized dates, and opt-in raw details', async () => {
	const NativeDateTimeFormat = Intl.DateTimeFormat;
	vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(function StableDateTimeFormat(_locale, options) { return new NativeDateTimeFormat('en-US', { ...options, timeZone: 'UTC' }); });
	getClassResult.mockResolvedValue({ run_id: 'run-uuid', student_id: 'student-uuid', scenario_revision_id: 'revision-uuid', student_username: 'learner', class_name: 'Project Management 101', scenario_name: 'Launch Week', status: 'submitted', current_week: 3, finished_at: '2026-01-02T15:04:00Z', engine_version: 'engine-secret', seed: 42, final_result: { outcome: 'submitted', score: { total: 88 } }, current_state: {}, turns: [{ week_number: 1, submitted_at: '2026-01-01T15:04:00Z', decision: { allocation: { development: 75, unit_testing: 25 } }, events: [{ kind: 'tasks_completed', easy: 4 }] }], contentAudit: { digestStatus: 'verified', divergences: [], deliveries: [], effects: [] } });
	render(<ChakraProvider><MemoryRouter initialEntries={['/classes/class/results/run']}><Routes><Route path="/classes/:class_id/results/:run_id" element={<ClassResultDetail />} /></Routes></MemoryRouter></ChakraProvider>);
	await waitFor(() => expect(screen.getByRole('heading', { name: 'Result for learner' })).toBeInTheDocument());
	expect(screen.getByText('Project Management 101 · Launch Week')).toBeInTheDocument();
	expect(screen.getByText('Jan 2, 2026, 3:04 PM')).toBeInTheDocument();
	expect(screen.getByText('Tasks completed')).toBeInTheDocument();
	const details = screen.getAllByText('Technical details').at(-1).closest('details');
	expect(details).not.toHaveAttribute('open');
	expect(screen.getByText(/run-uuid/)).not.toBeVisible();
	expect(screen.getByText(/engine-secret/)).not.toBeVisible();
	fireEvent.click(details.querySelector('summary'));
	expect(details).toHaveAttribute('open');
	expect(screen.getByText(/run-uuid/)).toBeVisible();
});
