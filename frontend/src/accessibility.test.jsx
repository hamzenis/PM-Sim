import axe from 'axe-core';
import { ChakraProvider } from '@chakra-ui/react';
import { render } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from './context/AuthProvider';
import Login from './pages/Login';
import theme from './theme';

const violationSummary = (violations) => violations
	.map(({ id, impact, nodes }) => `${id} (${impact}): ${nodes.map((node) => node.target.join(' ')).join(', ')}`)
	.join('\n');

test('representative public authentication page has no axe violations', async () => {
	const { container } = render(
		<ChakraProvider theme={theme}>
			<MemoryRouter>
				<AuthContext.Provider value={{ login: vi.fn() }}>
					<Login />
				</AuthContext.Provider>
			</MemoryRouter>
		</ChakraProvider>,
	);

	const results = await axe.run(container);
	expect(violationSummary(results.violations)).toBe('');
});
