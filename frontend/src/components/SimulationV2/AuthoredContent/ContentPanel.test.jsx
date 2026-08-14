import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import ContentPanel from './ContentPanel';

const event = (id, content = {}) => ({
	sequence_entry_id: id,
	sequence_ordinal: id === 's_budget_review' ? 1 : 2,
	kind: 'event',
	status: 'completed',
	required: false,
	visible: true,
	...content,
});

const renderPanel = (props) => render(<ChakraProvider><ContentPanel runId="run-1" version={4} {...props} /></ChakraProvider>);

test('does not render an event delivery without student-visible content', () => {
	renderPanel({ deliveries: [event('empty-event')] });

	expect(screen.queryByText('Read and respond')).not.toBeInTheDocument();
});

test('renders each accumulated show_message once without an Optional badge', () => {
	renderPanel({
		deliveries: [event('s_budget_review')],
		presentation: { messages: ['Week 4 sponsor notice', 'Week 4 sponsor notice'] },
	});

	expect(screen.getByText('Week 4 sponsor notice')).toBeInTheDocument();
	expect(screen.getAllByText('Week 4 sponsor notice')).toHaveLength(1);
	expect(screen.queryByText('Optional')).not.toBeInTheDocument();
});

test('shows the associated presentation message while a flag-only delivery creates no card', () => {
	renderPanel({
		deliveries: [event('s_budget_review'), event('s_handover_ready')],
		presentation: {
			messages: ['Week 4 sponsor notice: contingency consumed.'],
			flags: { handover_review_ready: true },
		},
	});

	expect(screen.getByText('Week 4 sponsor notice: contingency consumed.')).toBeVisible();
	expect(document.querySelector('#content-entry-s_budget_review')).not.toBeInTheDocument();
	expect(document.querySelector('#content-entry-s_handover_ready')).not.toBeInTheDocument();
});
