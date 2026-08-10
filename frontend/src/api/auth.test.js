import { changePassword, getCurrentUser, login, logout } from './auth';
import { apiRequest } from './client';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps the backend v2 authentication endpoints', async () => {
	apiRequest.mockResolvedValue({ id: 'user-1' });

	await getCurrentUser();
	await login('student', 'student-password');
	await logout();
	await changePassword('old-password', 'new-password');

	expect(apiRequest.mock.calls).toEqual([
		['/api/auth/me'],
		[
			'/api/auth/login',
			{ method: 'POST', body: JSON.stringify({ username: 'student', password: 'student-password' }) },
		],
		['/api/auth/logout', { method: 'POST' }],
		[
			'/api/auth/password',
			{
				method: 'PUT',
				body: JSON.stringify({
					current_password: 'old-password',
					new_password: 'new-password',
				}),
			},
		],
	]);
});
