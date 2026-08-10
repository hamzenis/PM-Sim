import { apiRequest } from './client';

export const listAvailableScenarios = () => apiRequest('/api/classes/available-scenarios');

export const listOwnedScenarios = () => apiRequest('/api/scenarios');

export const listScenarioRevisions = (scenarioId) => apiRequest(`/api/scenarios/${scenarioId}`);
