import { apiRequest } from './client';
import { listAuditEntries } from './audit';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

test('maps audit pagination to query parameters', async () => {
	apiRequest.mockResolvedValue([]);
	await listAuditEntries(25, 50);
	expect(apiRequest).toHaveBeenCalledWith('/api/audit?limit=25&offset=50');
});
