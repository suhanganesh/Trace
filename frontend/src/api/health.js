import { apiRequest } from './client';

export function fetchHealth(options) {
  return apiRequest('/api/health', options);
}
