import { apiRequest } from './client';
import {
	archiveScenario,
	createScenario,
	listAvailableScenarios,
	listOwnedScenarios,
	publishScenarioRevision,
	validateScenario,
} from './scenarios';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps student and professor scenario lists', async () => {
	apiRequest.mockResolvedValue([]);

	await listAvailableScenarios();
	await listOwnedScenarios();

	expect(apiRequest.mock.calls).toEqual([['/api/classes/available-scenarios'], ['/api/scenarios']]);
});

test('maps the professor scenario lifecycle', async () => {
	apiRequest.mockResolvedValue({});
	const definition = {
		schema_version: 1,
		name: 'Example',
		authored_content: { fragments: [], questions: [], events: [], sequence: [] },
	};
	await validateScenario(definition);
	await createScenario(definition);
	await publishScenarioRevision('scenario-1', 2);
	await archiveScenario('scenario-1');
	expect(apiRequest.mock.calls).toEqual([
		['/api/scenarios/validate', { method: 'POST', body: JSON.stringify(definition) }],
		['/api/scenarios', { method: 'POST', body: JSON.stringify(definition) }],
		['/api/scenarios/scenario-1/revisions/2/publish', { method: 'POST' }],
		['/api/scenarios/scenario-1/archive', { method: 'POST' }],
	]);
});
