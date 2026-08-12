const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || '';

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '');

export class ApiError extends Error {
	constructor(status, body) {
		const detail = getErrorMessage(body);
		super(detail);
		this.name = 'ApiError';
		this.status = status;
		this.body = body;
	}

	getFieldErrors() {
		if (!Array.isArray(this.body?.detail)) return {};
		return this.body.detail.reduce((errors, item) => {
			const field = Array.isArray(item.loc) ? item.loc.filter((part) => part !== 'body').join('.') : '';
			if (field && item.msg) errors[field] = item.msg;
			return errors;
		}, {});
	}
}

function getErrorMessage(body) {
	if (typeof body?.detail === 'string') return body.detail;
	if (Array.isArray(body?.detail) && body.detail[0]?.msg) return body.detail[0].msg;
	return 'Request failed';
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
