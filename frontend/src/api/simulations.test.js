import { apiRequest } from './client';
import {
	completeSimulationTurn,
	getSimulationRun,
	listSimulationRuns,
	startSimulationRun,
	submitSimulationRun,
} from './simulations';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps the backend v2 simulation lifecycle', async () => {
	apiRequest.mockResolvedValue({});
	const decision = { expected_version: 1, allocation: {} };

	await listSimulationRuns();
	await getSimulationRun('run-1');
	await startSimulationRun('revision-1', 42);
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
