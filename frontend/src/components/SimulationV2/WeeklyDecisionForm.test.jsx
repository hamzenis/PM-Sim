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

	expect(screen.getByText('Employee 1')).toBeInTheDocument();
	expect(screen.getByText('Employee type: Junior developer')).toBeInTheDocument();
	expect(screen.queryByText('employee-1')).not.toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Experience: 12%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Motivation: 80%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Stress: 25%' })).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Familiarity: 60%' })).toBeInTheDocument();
	expect(screen.getByText(/dismissal selections only apply when you submit the week/i)).toBeInTheDocument();

	fireEvent.click(screen.getByRole('checkbox', { name: 'Select for dismissal' }));
	expect(onChange).toHaveBeenCalledWith({ ...decision, dismiss_employee_ids: ['employee-1'] });
});

test('uses stable readable labels while preserving original dismissal IDs', () => {
	const employeeOneId = '0f51dff4-2554-4da6-af3b-00b525758c88';
	const employeeTwoId = 'e660f34a-1428-4cf2-9894-a4ce445f29b1';
	const employees = [
		{ id: employeeOneId, employee_type_code: 'junior', experience: 0.1, motivation: 0.8, stress: 0.2, familiarity: 0.3 },
		{ id: employeeTwoId, employee_type_code: 'junior', experience: 0.2, motivation: 0.7, stress: 0.3, familiarity: 0.4 },
	];
	const onChange = vi.fn();
	const { container, rerender } = render(
		<WeeklyDecisionForm decision={decision} employees={employees} employeeTypes={[employeeType]} onChange={onChange} />
	);

	expect(screen.getByText('Employee 1')).toBeInTheDocument();
	expect(screen.getByText('Employee 2')).toBeInTheDocument();
	expect(container).not.toHaveTextContent(employeeOneId);
	expect(container).not.toHaveTextContent(employeeTwoId);

	const employeeTwoCard = screen.getByText('Employee 2').parentElement;
	fireEvent.click(employeeTwoCard.querySelector('input[type="checkbox"]'));
	expect(onChange).toHaveBeenCalledWith({ ...decision, dismiss_employee_ids: [employeeTwoId] });

	rerender(<WeeklyDecisionForm decision={decision} employees={employees} employeeTypes={[employeeType]} onChange={onChange} />);
	expect(screen.getByText('Employee 1')).toBeInTheDocument();
	expect(screen.getByText('Employee 2')).toBeInTheDocument();
	expect(container).not.toHaveTextContent(employeeTwoId);
});

test('falls back to the employee type code without exposing the employee ID', () => {
	const employeeId = 'aa8a3bd1-63ac-446a-aeb8-140906118530';
	const { container } = render(
		<WeeklyDecisionForm
			decision={decision}
			employees={[{ id: employeeId, employee_type_code: 'contract_developer', experience: 0, motivation: 1, stress: 0, familiarity: 0 }]}
			employeeTypes={[]}
			onChange={vi.fn()}
		/>
	);

	expect(screen.getByText('Employee type: contract_developer')).toBeInTheDocument();
	expect(container).not.toHaveTextContent(employeeId);
});

test('validates allocations, hours, and whole-number hires', () => {
	expect(decisionIsValid(decision)).toBe(true);
	expect(decisionIsValid({ ...decision, overtime_hours_per_employee: -1 })).toBe(false);
	expect(decisionIsValid({ ...decision, hires: [{ employee_type_code: 'junior', count: 1.5 }] })).toBe(false);
});
