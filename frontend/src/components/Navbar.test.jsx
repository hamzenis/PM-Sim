import { ChakraProvider } from '@chakra-ui/react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../context/AuthProvider';
import theme from '../theme';
import Navbar from './Navbar';

function renderNavbar({ role = 'professor', route = '/scenarios', logout = vi.fn() } = {}) {
	const currentUser = { username: role === 'professor' ? 'professor' : 'student-one', role };
	return {
		logout,
		user: userEvent.setup(),
		...render(
			<ChakraProvider theme={theme}>
				<MemoryRouter initialEntries={[route]}>
					<AuthContext.Provider value={{ currentUser, logout }}>
						<Navbar />
					</AuthContext.Provider>
				</MemoryRouter>
			</ChakraProvider>
		),
	};
}

test('shows professor navigation and marks the active route', () => {
	const { container } = renderNavbar({ route: '/classes/123/results/456' });
	const primary = container.querySelector('nav[aria-label="Primary navigation"]');

	expect(primary.querySelector('a[href="/scenarios"]')).toBeInTheDocument();
	expect(primary.querySelector('a[href="/classes"]')).toHaveAttribute('aria-current', 'page');
	expect(primary.querySelector('a[href="/audit"]')).toBeInTheDocument();
});

test('shows student navigation without professor-only destinations', () => {
	const { container } = renderNavbar({ role: 'student' });
	const primary = container.querySelector('nav[aria-label="Primary navigation"]');

	expect(primary.querySelector('a[href="/scenarios"]')).toHaveAttribute('aria-current', 'page');
	expect(primary.querySelector('a[href="/help"]')).toBeInTheDocument();
	expect(primary.querySelector('a[href="/classes"]')).not.toBeInTheDocument();
	expect(primary.querySelector('a[href="/audit"]')).not.toBeInTheDocument();
});

test('opens the mobile navigation and closes it after choosing a link', async () => {
	const { user } = renderNavbar({ role: 'student' });
	const openButton = screen.getByRole('button', { name: 'Open navigation menu' });

	await user.click(openButton);
	const mobileNavigation = await screen.findByRole('navigation', { name: 'Mobile navigation' });
	expect(within(mobileNavigation).getByRole('link', { name: 'Help' })).toBeInTheDocument();
	await user.click(within(mobileNavigation).getByRole('link', { name: 'Help' }));
	await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
});

test('opens and closes the account menu from the keyboard and restores focus', async () => {
	const { user } = renderNavbar();
	const menuButton = screen.getByRole('button', { name: 'Account menu for professor' });

	menuButton.focus();
	await user.keyboard('{Enter}');
	const changePassword = await screen.findByRole('menuitem', { name: 'Change password' });
	await waitFor(() => expect(changePassword).toHaveFocus());
	await user.keyboard('{Escape}');
	await waitFor(() => expect(screen.queryByRole('menu')).not.toBeInTheDocument());
	expect(menuButton).toHaveFocus();
});

test('calls logout from the account menu', async () => {
	const logout = vi.fn().mockResolvedValue(undefined);
	const { user } = renderNavbar({ logout });

	await user.click(screen.getByRole('button', { name: 'Account menu for professor' }));
	await user.click(await screen.findByRole('menuitem', { name: 'Logout' }));

	await waitFor(() => expect(logout).toHaveBeenCalledOnce());
});
