import { apiRequest } from './client';

export const listAvailableScenarios = () => apiRequest('/api/classes/available-scenarios');

export const listOwnedScenarios = () => apiRequest('/api/scenarios');

export const listScenarioRevisions = (scenarioId) => apiRequest(`/api/scenarios/${scenarioId}`);

export const validateScenario = (definition) =>
	apiRequest('/api/scenarios/validate', {
		method: 'POST',
		body: JSON.stringify(definition),
	});

export const createScenario = (definition) =>
	apiRequest('/api/scenarios', {
		method: 'POST',
		body: JSON.stringify(definition),
	});

export const publishScenarioRevision = (scenarioId, revisionNumber) =>
	apiRequest(`/api/scenarios/${scenarioId}/revisions/${revisionNumber}/publish`, { method: 'POST' });

export const archiveScenario = (scenarioId) => apiRequest(`/api/scenarios/${scenarioId}/archive`, { method: 'POST' });
