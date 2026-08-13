import { ChakraProvider } from '@chakra-ui/react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { ApiError } from '../api/client';
import { AuthContext } from '../context/AuthProvider';
import theme from '../theme';
import Login from './Login';

function renderLogin(login = vi.fn().mockResolvedValue({ username: 'student' })) {
	return {
		login,
		user: userEvent.setup(),
		...render(
			<ChakraProvider theme={theme}>
				<MemoryRouter>
					<AuthContext.Provider value={{ login }}>
						<Login />
					</AuthContext.Provider>
				</MemoryRouter>
			</ChakraProvider>
		),
	};
}

async function completeForm(user) {
	await user.type(screen.getByLabelText(/^Username/), 'student');
	await user.type(screen.getByLabelText(/^Password/), 'student-password');
	await user.click(screen.getByRole('checkbox', { name: /privacy policy/i }));
}

test('uses visible labels and authentication autocomplete values', () => {
	renderLogin();
	expect(screen.getByLabelText(/^Username/)).toHaveAttribute('autocomplete', 'username');
	expect(screen.getByLabelText(/^Password/)).toHaveAttribute('autocomplete', 'current-password');
});

test('submits the semantic form with Enter', async () => {
	const { user, login } = renderLogin();
	await completeForm(user);
	await user.type(screen.getByLabelText(/^Password/), '{Enter}');
	expect(login).toHaveBeenCalledWith('student', 'student-password');
});

test('requires privacy-policy acceptance before login', async () => {
	const { user, login } = renderLogin();
	await user.type(screen.getByLabelText(/^Username/), 'student');
	await user.type(screen.getByLabelText(/^Password/), 'student-password');
	expect(screen.getByRole('button', { name: 'Log in' })).toBeDisabled();
	await user.type(screen.getByLabelText(/^Password/), '{Enter}');
	expect(login).not.toHaveBeenCalled();
});

test('shows and focuses the wrong-credentials error', async () => {
	const { user } = renderLogin(vi.fn().mockRejectedValue(new ApiError(401, { detail: 'invalid' })));
	await completeForm(user);
	await user.click(screen.getByRole('button', { name: 'Log in' }));
	const alert = await screen.findByRole('alert');
	expect(alert).toHaveTextContent('username or password is incorrect');
	await waitFor(() => expect(alert).toHaveFocus());
});

test('shows an actionable network error', async () => {
	vi.spyOn(console, 'error').mockImplementation(() => {});
	const { user } = renderLogin(vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
	await completeForm(user);
	await user.click(screen.getByRole('button', { name: 'Log in' }));
	expect(await screen.findByRole('alert')).toHaveTextContent('Check your connection and try again');
});

test('shows a busy state and prevents duplicate submissions', async () => {
	let resolveLogin;
	const pendingLogin = new Promise((resolve) => { resolveLogin = resolve; });
	const login = vi.fn(() => pendingLogin);
	const { user } = renderLogin(login);
	await completeForm(user);
	const button = screen.getByRole('button', { name: 'Log in' });
	await user.dblClick(button);
	expect(login).toHaveBeenCalledOnce();
	expect(screen.getByRole('button', { name: /Logging in/ })).toBeDisabled();
	resolveLogin({ username: 'student' });
	await waitFor(() => expect(screen.getByRole('button', { name: 'Log in' })).toBeEnabled());
});

test('password visibility control is named and keyboard accessible', async () => {
	const { user } = renderLogin();
	const password = screen.getByLabelText(/^Password/);
	const toggle = screen.getByRole('button', { name: 'Show password' });
	toggle.focus();
	await user.keyboard('{Enter}');
	expect(password).toHaveAttribute('type', 'text');
	expect(screen.getByRole('button', { name: 'Hide password' })).toHaveFocus();
});
