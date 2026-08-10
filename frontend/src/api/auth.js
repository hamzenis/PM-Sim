import { apiRequest } from './client';

export const getCurrentUser = () => apiRequest('/api/auth/me');

export const login = (username, password) =>
	apiRequest('/api/auth/login', {
		method: 'POST',
		body: JSON.stringify({ username, password }),
	});

export const logout = () => apiRequest('/api/auth/logout', { method: 'POST' });

export const changePassword = (currentPassword, newPassword) =>
	apiRequest('/api/auth/password', {
		method: 'PUT',
		body: JSON.stringify({
			current_password: currentPassword,
			new_password: newPassword,
		}),
	});
