import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import React from 'react';
import HelpContent, { SimulationHelpSections } from './HelpContent';

test('documents the v2 simulation behavior and metrics', () => {
	render(<ChakraProvider><HelpContent /></ChakraProvider>);

	expect(screen.getByRole('heading', { name: 'Simulation v2 help' })).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Dashboard at a glance' })).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Visible and undiscovered bugs' })).toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'How scoring works' })).toBeInTheDocument();
	expect(screen.getByLabelText('Task lifecycle diagram')).toBeInTheDocument();
});

test('renders reusable sections without the page introduction', () => {
	render(<ChakraProvider><SimulationHelpSections /></ChakraProvider>);

	expect(screen.queryByRole('heading', { name: 'Simulation v2 help' })).not.toBeInTheDocument();
	expect(screen.getByRole('heading', { name: 'Weekly decisions and processing order' })).toBeInTheDocument();
	expect(screen.queryByText(/professor workflow/i)).not.toBeInTheDocument();
});
