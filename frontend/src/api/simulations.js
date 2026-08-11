import { apiRequest } from './client';

export const listSimulationRuns = () => apiRequest('/api/simulations');

export const getSimulationRun = (runId) => apiRequest(`/api/simulations/${runId}`);

export const startSimulationRun = (scenarioRevisionId, seed, classId) =>
	apiRequest('/api/simulations', {
		method: 'POST',
		body: JSON.stringify({ scenario_revision_id: scenarioRevisionId, seed, class_id: classId }),
	});

export const listSimulationTurns = (runId) => apiRequest(`/api/simulations/${runId}/turns`);

export const completeSimulationTurn = (runId, decision, idempotencyKey) =>
	apiRequest(`/api/simulations/${runId}/turns`, {
		method: 'POST',
		headers: { 'Idempotency-Key': idempotencyKey },
		body: JSON.stringify(decision),
	});

export const submitSimulationRun = (runId, expectedVersion) =>
	apiRequest(`/api/simulations/${runId}/submit`, {
		method: 'POST',
		body: JSON.stringify({ expected_version: expectedVersion }),
	});
