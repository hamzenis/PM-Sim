import { Button, ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { EmptyState, PageLoadingState, RequestError } from './FeedbackStates';

const renderState = (state) => render(<ChakraProvider>{state}</ChakraProvider>);

test('loading state exposes its activity and readable label', () => {
	renderState(<PageLoadingState label="Loading class results…" />);
	expect(screen.getByRole('status')).toHaveTextContent('Loading class results…');
});

test('empty state explains the situation and can offer a next action', () => {
	renderState(
		<EmptyState
			title="No classes yet"
			description="Create a class to begin adding students."
			action={<Button>Create class</Button>}
		/>
	);
	expect(screen.getByRole('heading', { name: 'No classes yet' })).toBeInTheDocument();
	expect(screen.getByText(/create a class to begin/i)).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'Create class' })).toBeInTheDocument();
});

test('request error is announced and keeps a concise operation-specific message', () => {
	renderState(<RequestError title="Couldn’t load scenarios" message="Check your connection and try again." />);
	expect(screen.getByRole('alert')).toHaveTextContent('Couldn’t load scenarios');
	expect(screen.getByRole('alert')).toHaveTextContent('Check your connection and try again.');
});
