import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { SubmissionReadiness, submissionReadiness } from './SimulationV2';

const pool = (easy = 0, medium = 0, hard = 0) => ({ easy, medium, hard });

test('defines readiness as integration-tested tasks divided by all project tasks', () => {
	const state = {
		tasks_todo: pool(2, 1),
		tasks_completed: pool(3, 2),
		tasks_integration_tested: pool(1, 1),
	};

	expect(submissionReadiness(state)).toEqual({
		integrationTestedTasks: 2,
		totalProjectTasks: 8,
		percentage: 25,
	});
});

test('shows the non-overlapping readiness ratio without blocking early submission', () => {
	render(
		<ChakraProvider>
			<SubmissionReadiness
				state={{
					tasks_todo: pool(2),
					tasks_completed: pool(8),
					tasks_integration_tested: pool(7),
				}}
			/>
		</ChakraProvider>
	);

	expect(screen.getByText('7 of 10 tasks integration tested (70%)')).toBeInTheDocument();
	expect(screen.getByRole('progressbar', { name: 'Submission readiness: 7 of 10 tasks integration tested' })).toBeInTheDocument();
	expect(screen.getByText(/you may submit now/i)).toBeInTheDocument();
});
