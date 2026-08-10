import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import WeeklyDecisionForm, { decisionIsValid } from './WeeklyDecisionForm';

const decision = {
	allocation: { development: 50, unit_testing: 20, bug_fixing: 20, integration_testing: 10 },
	hires: [],
	dismiss_employee_ids: [],
	overtime_hours_per_employee: 0,
	meeting_hours_per_employee: 0,
	training_hours_per_employee: 0,
};

test('adds a selected employee type to the weekly hires', () => {
	const onChange = jest.fn();
	render(
		<WeeklyDecisionForm
			decision={decision}
			employees={[]}
			employeeTypes={[{ code: 'junior', name: 'Junior developer', cost_per_day: 100 }]}
			onChange={onChange}
		/>
	);

	fireEvent.change(screen.getByLabelText('Hire Junior developer'), { target: { value: '2' } });

	expect(onChange).toHaveBeenCalledWith({
		...decision,
		hires: [{ employee_type_code: 'junior', count: 2 }],
	});
});

test('validates allocations, hours, and whole-number hires', () => {
	expect(decisionIsValid(decision)).toBe(true);
	expect(decisionIsValid({ ...decision, overtime_hours_per_employee: -1 })).toBe(false);
	expect(decisionIsValid({ ...decision, hires: [{ employee_type_code: 'junior', count: 1.5 }] })).toBe(false);
});
