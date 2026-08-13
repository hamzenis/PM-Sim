import { ChakraProvider } from '@chakra-ui/react';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ProfessorAuthoredTimeline from './ProfessorAuthoredTimeline';

const completeAudit = {
	digestStatus: 'diverged', divergences: [{ category: 'definition_digest', record: 'entry-uuid', expected: 'good-digest', actual: 'bad-digest' }],
	deliveries: [{ id: 'delivery-uuid', checkpoint: 'after_week', status: 'completed', deliveredAt: '2026-01-02T15:00:00Z', hiddenFromStudents: true, turnWeekNumber: 1, definitionDigest: 'definition-digest', definition: { prompt: 'What did you learn?' }, responses: [{ id: 'answer-uuid', kind: 'answer', answer: { answer: 'Planning matters' } }], effects: [{ id: 'effect-uuid', effectIndex: 0, payload: { text: 'Well done' }, beforeProjectionDigest: 'before-digest', afterProjectionDigest: 'after-digest' }] }],
	effects: [{ id: 'effect-uuid', beforeProjectionDigest: 'before-digest', afterProjectionDigest: 'after-digest' }],
};

test('presents readable teaching content while technical identifiers are collapsed', () => {
	render(<ChakraProvider><ProfessorAuthoredTimeline audit={completeAudit} /></ChakraProvider>);
	expect(screen.getByRole('heading', { name: 'Teaching-content timeline' })).toBeInTheDocument();
	expect(screen.getByText('Student response')).toBeInTheDocument();
	expect(screen.getByText('Answer: Planning matters')).toBeInTheDocument();
	expect(screen.getByText(/Replay divergence detected/)).toBeVisible();
	const details = screen.getByText('Technical details').closest('details');
	expect(details).not.toHaveAttribute('open');
	screen.getAllByText(/delivery-uuid/).forEach((node) => expect(node).not.toBeVisible());
	screen.getAllByText(/definition-digest/).forEach((node) => expect(node).not.toBeVisible());
	fireEvent.click(screen.getByText('Technical details'));
	expect(details).toHaveAttribute('open');
	expect(screen.getAllByText(/delivery-uuid/).find((node) => node.matches('code'))).toBeVisible();
});
