import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import WeeklyDecisionForm, { decisionIsValid } from './WeeklyDecisionForm';

const employeeType = {
	code: 'junior',
	name: 'Junior developer',
	cost_per_day: 100,
	throughput: { easy: 4, medium: 2, hard: 0.5 },
	error_rate: 0.06,
	management_skill: 0.3,
};

const decision = {
	allocation: { development: 50, unit_testing: 20, bug_fixing: 20, integration_testing: 10 },
	hires: [],
	dismiss_employee_ids: [],
	overtime_hours_per_employee: 0,
	meeting_hours_per_employee: 0,
	training_hours_per_employee: 0,
};

test('adds a selected employee type to the weekly hires', () => {
	const onChange = vi.fn();
	render(
		<WeeklyDecisionForm
			decision={decision}
			employees={[]}
			employeeTypes={[employeeType]}
			onChange={onChange}
		/>
	);

	fireEvent.change(screen.getByLabelText('Hire Junior developer'), { target: { value: '2' } });

	expect(onChange).toHaveBeenCalledWith({
		...decision,
		hires: [{ employee_type_code: 'junior', count: 2 }],
	});
});

test('shows responsive employee type details using the v2 metrics', () => {
	render(
		<WeeklyDecisionForm
			decision={decision}
			employees={[]}
			employeeTypes={[employeeType]}
			onChange={vi.fn()}
		/>
	);

	expect(screen.getByText('$100.00')).toBeInTheDocument();
	expect(screen.getByText('Easy throughput')).toBeInTheDocument();
	expect(screen.getByText('Medium throughput')).toBeInTheDocument();
	expect(screen.getByText('Hard throughput')).toBeInTheDocument();
	expect(screen.getByText('6%')).toBeInTheDocument();
	expect(screen.getByText('30%')).toBeInTheDocument();
	expect(screen.getByText(/per eight productive hours/i)).toBeInTheDocument();
	expect(screen.queryByText(/development quality/i)).not.toBeInTheDocument();
});

test.each([320, 1280])('shows the roster and accessible status indicators at a %ipx viewport', (width) => {
	window.innerWidth = width;
	const onChange = vi.fn();
	render(
		<WeeklyDecisionForm
			decision={decision}
			employees={[{
				id: 'employee-1',
				employee_type_code: 'junior',
				experience: 0.12,
				motivation: 0.8,
				stress: 0.25,
				familiarity: 0.6,
			}]}
			employeeTypes={[employeeType]}
			onChange={onChange}
		/>
	);

	expect(screen.getAllByText('Junior developer')).toHaveLength(2);
	expect(screen.getByRole('progressbar', { name: 'Experience: 12%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Motivation: 80%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Stress: 25%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Familiarity: 60%' })).toBeInTheDocument();
	expect(screen.getByText(/status values affect employee efficiency/i)).toBeInTheDocument();

	fireEvent.click(screen.getByRole('checkbox', { name: 'Dismiss employee-1' }));
	expect(onChange).toHaveBeenCalledWith({ ...decision, dismiss_employee_ids: ['employee-1'] });
});

test('validates allocations, hours, and whole-number hires', () => {
	expect(decisionIsValid(decision)).toBe(true);
	expect(decisionIsValid({ ...decision, overtime_hours_per_employee: -1 })).toBe(false);
	expect(decisionIsValid({ ...decision, hires: [{ employee_type_code: 'junior', count: 1.5 }] })).toBe(false);
});
