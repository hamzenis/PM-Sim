import { apiRequest } from './client';

export const listAuditEntries = (limit = 50, offset = 0) => apiRequest(`/api/audit?limit=${limit}&offset=${offset}`);
