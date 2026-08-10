import { apiRequest } from './client';
import { listAvailableScenarios, listOwnedScenarios } from './scenarios';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps student and professor scenario lists', async () => {
	apiRequest.mockResolvedValue([]);

	await listAvailableScenarios();
	await listOwnedScenarios();

	expect(apiRequest.mock.calls).toEqual([['/api/classes/available-scenarios'], ['/api/scenarios']]);
});
