import { apiRequest } from './client';

export function fetchFunnel(options) {
  return apiRequest('/api/funnel', options);
}
