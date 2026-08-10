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

test('preserves field errors from FastAPI validation responses', async () => {
	jest.spyOn(global, 'fetch').mockResolvedValue({
		ok: false,
		status: 422,
		json: async () => ({
			detail: [{ loc: ['body', 'students', 0, 'password'], msg: 'String should have at least 10 characters' }],
		}),
	});

	const error = await apiRequest('/api/classes/class-1/students/import').catch((reason) => reason);

	expect(error.message).toBe('String should have at least 10 characters');
	expect(error.getFieldErrors()).toEqual({
		'students.0.password': 'String should have at least 10 characters',
	});
});
