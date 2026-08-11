import { apiRequest } from './client';
import {
	acknowledgeContentEntry,
	answerContentEntry,
	completeSimulationTurn,
	getSimulationRun,
	listSimulationRuns,
	listSimulationTurns,
	startSimulationRun,
	submitSimulationRun,
} from './simulations';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps the backend v2 simulation lifecycle', async () => {
	const persistedState = { week: 1, remaining_budget: 900 };
	apiRequest.mockResolvedValueOnce([])
		.mockResolvedValueOnce({})
		.mockResolvedValueOnce({})
		.mockResolvedValueOnce([{ week_number: 1, resulting_state: persistedState }])
		.mockResolvedValue({});
	const decision = { expected_version: 1, allocation: {} };

	await listSimulationRuns();
	await getSimulationRun('run-1');
	await startSimulationRun('revision-1', 42);
	expect(await listSimulationTurns('run-1')).toEqual([{ week_number: 1, resulting_state: persistedState }]);
	await completeSimulationTurn('run-1', decision, 'request-1');
	await submitSimulationRun('run-1', 2);

	expect(apiRequest.mock.calls).toEqual([
		['/api/simulations'],
		['/api/simulations/run-1'],
		[
			'/api/simulations',
			{
				method: 'POST',
				body: JSON.stringify({ scenario_revision_id: 'revision-1', seed: 42 }),
			},
		],
		['/api/simulations/run-1/turns'],
		[
			'/api/simulations/run-1/turns',
			{
				method: 'POST',
				headers: { 'Idempotency-Key': 'request-1' },
				body: JSON.stringify(decision),
			},
		],
		['/api/simulations/run-1/submit', { method: 'POST', body: JSON.stringify({ expected_version: 2 }) }],
	]);
});

test('maps authored content answers and acknowledgements with concurrency and idempotency fields', async () => {
	const mapped = { id: 'run-1', version: 4, deliveries: [] };
	apiRequest.mockResolvedValue(mapped);

	expect(await answerContentEntry('run-1', 'question/1', ['a'], 2, 'answer-key')).toBe(mapped);
	expect(await acknowledgeContentEntry('run-1', 'fragment-1', 3, 'ack-key')).toBe(mapped);
	expect(apiRequest.mock.calls).toEqual([
		['/api/simulations/run-1/content/question/1/answer', {
			method: 'POST',
			headers: { 'Idempotency-Key': 'answer-key' },
			body: JSON.stringify({ expected_version: 2, answer: ['a'] }),
		}],
		['/api/simulations/run-1/content/fragment-1/acknowledge', {
			method: 'POST',
			headers: { 'Idempotency-Key': 'ack-key' },
			body: JSON.stringify({ expected_version: 3 }),
		}],
	]);
});

test('makes identical retries and propagates HTTP 409 errors', async () => {
	const conflict = Object.assign(new Error('version changed'), { status: 409 });
	apiRequest.mockResolvedValueOnce({ version: 2 }).mockResolvedValueOnce({ version: 2 }).mockRejectedValueOnce(conflict);
	await answerContentEntry('run-1', 'q1', true, 1, 'stable-key');
	await answerContentEntry('run-1', 'q1', true, 1, 'stable-key');
	await expect(acknowledgeContentEntry('run-1', 'f1', 1, 'conflict-key')).rejects.toBe(conflict);
	expect(apiRequest.mock.calls[0]).toEqual(apiRequest.mock.calls[1]);
});
