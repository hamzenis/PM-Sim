import { ChakraProvider } from '@chakra-ui/react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthProvider';
import Navbar from './Navbar';

function renderNavbar(logout = vi.fn()) {
	return {
		logout,
		user: userEvent.setup(),
		...render(
			<ChakraProvider>
				<MemoryRouter>
					<AuthContext.Provider value={{ currentUser: { username: 'professor', role: 'professor' }, logout }}>
						<Navbar />
					</AuthContext.Provider>
				</MemoryRouter>
			</ChakraProvider>
		),
	};
}

test('opens and closes the account menu from the keyboard and restores focus', async () => {
	const { user } = renderNavbar();
	const menuButton = screen.getByRole('button', { name: 'Account menu' });

	menuButton.focus();
	expect(menuButton).toHaveFocus();
	await user.keyboard('{Enter}');

	const changePassword = await screen.findByRole('menuitem', { name: 'Change password' });
	await waitFor(() => expect(changePassword).toHaveFocus());

	await user.keyboard('{Escape}');
	await waitFor(() => expect(screen.queryByRole('menu')).not.toBeInTheDocument());
	expect(menuButton).toHaveFocus();
});

test('calls logout from the account menu', async () => {
	const logout = vi.fn().mockResolvedValue(undefined);
	const { user } = renderNavbar(logout);

	await user.click(screen.getByRole('button', { name: 'Account menu' }));
	await user.click(await screen.findByRole('menuitem', { name: 'Logout' }));

	await waitFor(() => expect(logout).toHaveBeenCalledOnce());
});
