const DEFAULT_BASE = 'http://127.0.0.1:8000';

export function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE;
}

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function apiRequest(path, { params, signal } = {}) {
  const url = new URL(`${getApiBaseUrl()}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  let response;
  try {
    response = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    });
  } catch {
    throw new ApiError(
      'Trace API is unavailable. Check that MongoDB and the Trace API are running.',
      { status: 0, code: 'network_error' },
    );
  }

  let payload = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    payload = await response.json();
  }

  if (!response.ok) {
    const detail =
      payload?.detail ||
      (response.status === 503
        ? 'Trace analytics are temporarily unavailable.'
        : 'Unable to load this analysis.');
    throw new ApiError(detail, { status: response.status, code: payload?.error_code });
  }

  return payload;
}
