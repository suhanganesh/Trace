import { apiRequest } from './client';

export function fetchReport(options) {
  return apiRequest('/api/report', options);
}
