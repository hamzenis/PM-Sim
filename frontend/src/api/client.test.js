import { ApiError, apiRequest } from './client';

afterEach(() => {
	jest.restoreAllMocks();
});

test('sends browser credentials and parses JSON', async () => {
	jest.spyOn(global, 'fetch').mockResolvedValue({
		ok: true,
		status: 200,
		json: async () => ({ id: 'user-1' }),
	});

	await expect(apiRequest('/api/auth/me')).resolves.toEqual({ id: 'user-1' });
	expect(fetch).toHaveBeenCalledWith('/api/auth/me', expect.objectContaining({ credentials: 'include' }));
});

test('returns undefined for an empty response', async () => {
	jest.spyOn(global, 'fetch').mockResolvedValue({ ok: true, status: 204 });

	await expect(apiRequest('/api/auth/logout', { method: 'POST' })).resolves.toBeUndefined();
});

test('exposes status and backend details for failed requests', async () => {
	jest.spyOn(global, 'fetch').mockResolvedValue({
		ok: false,
		status: 401,
		json: async () => ({ detail: 'invalid credentials' }),
	});

	const error = await apiRequest('/api/auth/login').catch((reason) => reason);
	expect(error).toBeInstanceOf(ApiError);
	expect(error).toEqual(expect.objectContaining({ name: 'ApiError', status: 401, message: 'invalid credentials' }));
});
