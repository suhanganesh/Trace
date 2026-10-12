import { apiRequest } from './client';

export function fetchBehavior(options) {
  return apiRequest('/api/behavior', options);
}
