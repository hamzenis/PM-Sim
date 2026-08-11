import { ChakraProvider } from '@chakra-ui/react';
import { render, screen, within } from '@testing-library/react';
import React from 'react';
import ProfessorAuthoredTimeline from './ProfessorAuthoredTimeline';

const completeAudit = {
	digestStatus: 'diverged',
	divergences: [{ category: 'definition_digest', record: 'entry', expected: 'good', actual: 'bad' }],
	deliveries: [{
		id: 'delivery', sequenceEntryId: 'entry', checkpoint: 'after_week:1', status: 'completed',
		hiddenFromStudents: true, turnWeekNumber: 1, definitionDigest: 'definition-123',
		definition: { prompt: 'What did you learn?' },
		responses: [
			{ id: 'answer', kind: 'answer', answer: { answer: 'Planning matters' } },
			{ id: 'ack', kind: 'acknowledge', answer: {} },
		],
		effects: [{ id: 'effect', effectIndex: 0, payload: { type: 'show_message', text: 'Well done' }, beforeProjectionDigest: 'projection-before', afterProjectionDigest: 'projection-after' }],
	}],
};

test('shows the complete professor timeline, hidden markers, effects, digests, turns, and divergence', () => {
	render(<ChakraProvider><ProfessorAuthoredTimeline audit={completeAudit} /></ChakraProvider>);
	expect(screen.getByRole('heading', { name: 'Authored-content timeline' })).toBeInTheDocument();
	expect(screen.getByText('Professor only / hidden')).toBeInTheDocument();
	expect(screen.getByText('Associated turn: week 1')).toBeInTheDocument();
	expect(screen.getByText('Authored response')).toBeInTheDocument();
	expect(screen.getByText('Learning interaction acknowledgement')).toBeInTheDocument();
	expect(screen.getByText(/show_message/)).toHaveTextContent('Well done');
	expect(screen.getByText(/Definition\/projection digest status/)).toHaveTextContent('diverged');
	expect(screen.getByText(/Replay divergence detected/)).toBeInTheDocument();
	expect(screen.getByText(/Divergence definition_digest/)).toHaveTextContent('expected good, actual bad');
});

test('never presents authored answers as score contributions', () => {
	const { container } = render(<ChakraProvider><ProfessorAuthoredTimeline audit={{ ...completeAudit, digestStatus: 'verified', divergences: [] }} /></ChakraProvider>);
	const timeline = within(container).getByRole('heading', { name: 'Authored-content timeline' }).parentElement;
	expect(within(timeline).getByText('Authored response')).toBeInTheDocument();
	expect(within(timeline).queryByText(/score contribution/i)).not.toBeInTheDocument();
	expect(within(timeline).queryByText(/^score$/i)).not.toBeInTheDocument();
});
