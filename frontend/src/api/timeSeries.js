import { apiRequest } from './client';

export function fetchTimeSeries(
  { granularity = 'daily', start_date, end_date } = {},
  options,
) {
  return apiRequest('/api/time-series', {
    ...options,
    params: { granularity, start_date, end_date },
  });
}
