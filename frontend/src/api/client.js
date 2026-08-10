const configuredBaseUrl = process.env.REACT_APP_API_BASE_URL || '';

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '');

export class ApiError extends Error {
	constructor(status, body) {
		const detail = typeof body?.detail === 'string' ? body.detail : 'Request failed';
		super(detail);
		this.name = 'ApiError';
		this.status = status;
		this.body = body;
	}
}

export async function apiRequest(path, options = {}) {
	const headers = new Headers(options.headers);
	headers.set('Accept', 'application/json');
	if (options.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}

	const response = await fetch(`${API_BASE_URL}${path}`, {
		...options,
		credentials: 'include',
		headers,
	});

	if (!response.ok) {
		const body = await response.json().catch(() => ({ detail: response.statusText }));
		if (response.status === 401 && path !== '/api/auth/login') {
			window.dispatchEvent(new Event('pm-sim-session-expired'));
		}
		throw new ApiError(response.status, body);
	}
	if (response.status === 204) return undefined;
	return response.json();
}
