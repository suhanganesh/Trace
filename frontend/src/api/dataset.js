import { apiRequest } from './client';

export function fetchDatasetInfo(options) {
  return apiRequest('/api/dataset-info', options);
}
