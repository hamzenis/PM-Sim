import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import EmployeeStatusChart, { selectEmployeeStatusTrend, toPercentage } from './EmployeeStatusChart';

const employee = (stress, motivation, familiarity) => ({ stress, motivation, familiarity });
const snapshot = (week, employees) => ({ week, employees });
const turn = (week, resultingState) => ({ week_number: week, resulting_state: resultingState });

test('converts simulation ratios to percentages', () => {
	expect(toPercentage(0.375)).toBe(37.5);
});

test('averages all employees in a snapshot', () => {
	const trend = selectEmployeeStatusTrend(snapshot(1, [employee(0.2, 0.8, 0.4), employee(0.6, 0.4, 0.8)]));
	expect(trend.current.employeeCount).toBe(2);
	expect(trend.current.stress).toBeCloseTo(0.4);
	expect(trend.current.motivation).toBeCloseTo(0.6);
	expect(trend.current.familiarity).toBeCloseTo(0.6);
});

test('recalculates each snapshot for workforce changes rather than tracking employee identities', () => {
	const first = snapshot(1, [employee(0.2, 0.4, 0.6), employee(0.4, 0.6, 0.8)]);
	const current = snapshot(2, [employee(0.9, 0.8, 0.7)]);
	const trend = selectEmployeeStatusTrend(current, [turn(1, first)]);
	expect(trend.previous.employeeCount).toBe(2);
	expect(trend.previous.stress).toBeCloseTo(0.3);
	expect(trend.previous.motivation).toBeCloseTo(0.5);
	expect(trend.previous.familiarity).toBeCloseTo(0.7);
	expect(trend.current).toMatchObject({ employeeCount: 1, stress: 0.9, motivation: 0.8, familiarity: 0.7 });
});

test('renders an explicit empty-workforce state without percentages', () => {
	render(<ChakraProvider><EmployeeStatusChart state={snapshot(2, [])} turns={[turn(1, snapshot(1, [employee(0.2, 0.5, 0.7)]))]} /></ChakraProvider>);
	expect(screen.getByText('No employees')).toBeInTheDocument();
	expect(screen.queryByText('NaN%')).not.toBeInTheDocument();
	expect(screen.queryByRole('img')).not.toBeInTheDocument();
});

test('shows current percentages and changes from the preceding snapshot', () => {
	render(<ChakraProvider><EmployeeStatusChart state={snapshot(2, [employee(0.3, 0.6, 0.8)])} turns={[turn(1, snapshot(1, [employee(0.2, 0.7, 0.5)]))]} /></ChakraProvider>);
	expect(screen.getAllByText('30.0%')).toHaveLength(2);
	expect(screen.getByText('+10.0 pp since last week')).toBeInTheDocument();
	expect(screen.getByText('−10.0 pp since last week')).toBeInTheDocument();
	expect(screen.getByRole('img', { name: 'Weekly team-average employee status percentages' })).toBeInTheDocument();
	expect(screen.getByText('Project week')).toBeInTheDocument();
	expect(screen.getByText('Team average (%)')).toBeInTheDocument();
	expect(screen.getByLabelText('Chart legend')).toHaveTextContent(/Stress.*Motivation.*Familiarity/);
	expect(screen.getByText('Employee status trend data')).toBeInTheDocument();
});

test('labels the percentage axis from zero to one hundred percent', () => {
	render(<ChakraProvider><EmployeeStatusChart state={snapshot(1, [employee(0.5, 0.6, 0.7)])} /></ChakraProvider>);
	expect(screen.getByText('0%')).toBeInTheDocument();
	expect(screen.getByText('50%')).toBeInTheDocument();
	expect(screen.getByText('100%')).toBeInTheDocument();
	expect(screen.getByText('W1')).toBeInTheDocument();
});

test('annotates increases and decreases in team size without claiming a cause', () => {
	const first = snapshot(1, Array.from({ length: 3 }, () => employee(0.2, 0.5, 0.6)));
	const second = snapshot(2, Array.from({ length: 5 }, () => employee(0.3, 0.6, 0.7)));
	const current = snapshot(3, Array.from({ length: 4 }, () => employee(0.4, 0.7, 0.8)));
	render(<ChakraProvider><EmployeeStatusChart state={current} turns={[turn(1, first), turn(2, second)]} /></ChakraProvider>);
	expect(screen.getByText('Team increased from 3 to 5')).toBeInTheDocument();
	expect(screen.getByText('Team decreased from 5 to 4')).toBeInTheDocument();
});

test('provides complete weekly point details', () => {
	render(<ChakraProvider><EmployeeStatusChart state={snapshot(4, [employee(0.25, 0.75, 0.5)])} /></ChakraProvider>);
	expect(screen.getByRole('button', { name: 'Week 4. Team size 1. Average stress 25.0%. Average motivation 75.0%. Average familiarity 50.0%.' })).toHaveTextContent('Latest');
});

test('weekly details are keyboard accessible', async () => {
	const user = userEvent.setup();
	render(<ChakraProvider><EmployeeStatusChart state={snapshot(2, [employee(0.3, 0.7, 0.8)])} turns={[turn(1, snapshot(1, [employee(0.2, 0.6, 0.7)]))]} /></ChakraProvider>);
	await user.tab();
	expect(screen.getByRole('button', { name: /Week 1\. Team size 1/ })).toHaveFocus();
	await user.tab();
	expect(screen.getByRole('button', { name: /Week 2\. Team size 1/ })).toHaveFocus();
});

test('keeps current-workforce averages usable when metric values are missing', () => {
	const trend = selectEmployeeStatusTrend(snapshot(1, [{ stress: undefined, motivation: 0.6, familiarity: null }]));
	expect(trend.current).toMatchObject({ employeeCount: 1, stress: 0, motivation: 0.6, familiarity: 0 });
});
