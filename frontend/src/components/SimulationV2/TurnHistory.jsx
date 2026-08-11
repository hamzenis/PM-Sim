import { Box, Heading, Stack, Text } from '@chakra-ui/react';
import React from 'react';

const readableKind = (kind = '') => kind.replaceAll('_', ' ');
const hiddenEventKinds = new Set(['bugs_created', 'incorrect_specifications_created']);

const plural = (count, singular, pluralForm = `${singular}s`) => (count === 1 ? singular : pluralForm);
const number = (value) => (typeof value === 'number' && Number.isFinite(value) ? value : 0);

const poolCopy = (values = {}, action, noun = 'task') => {
	const difficulties = ['easy', 'medium', 'hard']
		.filter((difficulty) => number(values[difficulty]) > 0)
		.map((difficulty) => `${number(values[difficulty])} ${difficulty}`);
	const total = typeof values.total === 'number'
		? number(values.total)
		: ['easy', 'medium', 'hard'].reduce((sum, difficulty) => sum + number(values[difficulty]), 0);
	const breakdown = difficulties.length > 0 ? ` (${difficulties.join(', ')})` : '';
	return `${total} ${plural(total, noun)} ${action}${breakdown}.`;
};

const fallbackPayload = (values = {}) => Object.entries(values)
	.map(([name, value]) => `${readableKind(name)}: ${readableKind(String(value))}`)
	.join(', ');

export const eventCopy = ({ kind = '', values = {} }) => {
	switch (kind) {
		case 'tasks_completed': return poolCopy(values, 'completed');
		case 'tasks_unit_tested': return poolCopy(values, 'unit tested');
		case 'bugs_discovered': return poolCopy(values, 'discovered', 'bug');
		case 'bugs_fixed': return poolCopy(values, 'fixed', 'bug');
		case 'tasks_integration_tested': return poolCopy(values, 'integration tested');
		case 'tasks_returned_to_backlog': return poolCopy(values, 'returned to the backlog for more work');
		case 'staffing_changed': {
			const hired = number(values.hired);
			const dismissed = number(values.dismissed);
			return `Team updated: ${hired} ${plural(hired, 'hire')}, ${dismissed} ${plural(dismissed, 'dismissal')}; ${number(values.team_size)} employees total.`;
		}
		case 'employee_dynamics_updated':
			return `Team schedule: ${number(values.overtime_hours_per_employee)} overtime, ${number(values.meeting_hours_per_employee)} meeting, and ${number(values.training_hours_per_employee)} training hours per employee.`;
		case 'staff_cost_charged': return `Staff cost charged: ${number(values.amount).toLocaleString()}.`;
		case 'week_completed': return `Week ${number(values.week)} completed (${number(values.working_days)} working ${plural(number(values.working_days), 'day')}).`;
		case 'simulation_finished': return `Simulation finished: ${readableKind(String(values.outcome || 'outcome unavailable'))}.`;
		default: {
			const payload = fallbackPayload(values);
			return `${readableKind(kind) || 'Event'}${payload ? ` — ${payload}` : ''}.`;
		}
	}
};

const TurnHistory = ({ turns }) => {
	if (turns.length === 0) return null;
	return (
		<Box bg="white" borderRadius="2xl" p={7} mt={6}>
			<Heading size="md" mb={4}>Turn history</Heading>
			<Stack spacing={4}>
				{turns.map(({ week_number: weekNumber, decision, events = [], resulting_state: resultingState }) => {
					const visibleEvents = events.filter((event) => !hiddenEventKinds.has(event.kind));
					return (
						<Box key={weekNumber} borderWidth="1px" borderRadius="md" p={4} data-state-week={resultingState?.week}>
							<Heading size="sm" mb={2}>Week {weekNumber}</Heading>
							<Text fontWeight="semibold">
								Allocation: {Object.entries(decision.allocation || {}).map(([name, value]) => `${readableKind(name)} ${value}%`).join(', ')}
							</Text>
							<Text mb={2}>Hires: {decision.hires?.length || 0}; dismissals: {decision.dismiss_employee_ids?.length || 0}; overtime: {decision.overtime_hours_per_employee || 0} hours</Text>
							{visibleEvents.length === 0
								? <Text>No visible events.</Text>
								: visibleEvents.map((event, index) => <Text key={`${event.kind}-${index}`}>• {eventCopy(event)}</Text>)}
						</Box>
					);
				})}
			</Stack>
		</Box>
	);
};

export default TurnHistory;
