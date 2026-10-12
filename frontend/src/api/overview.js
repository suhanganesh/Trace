import { apiRequest } from './client';

export function fetchOverview(options) {
  return apiRequest('/api/overview', options);
}
