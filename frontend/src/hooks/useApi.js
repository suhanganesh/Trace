import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../api/client';

export function useApi(fetcher, deps = [], { enabled = true } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(Boolean(enabled));
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    const controller = new AbortController();
    try {
      const result = await fetcherRef.current({ signal: controller.signal });
      setData(result);
    } catch (err) {
      if (err?.name === 'AbortError') return;
      setError(
        err instanceof ApiError
          ? err
          : new ApiError('Unable to load this analysis.'),
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [enabled, ...deps]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    const run = async () => {
      if (!enabled) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const result = await fetcherRef.current({ signal: controller.signal });
        if (!cancelled) setData(result);
      } catch (err) {
        if (cancelled || err?.name === 'AbortError') return;
        setError(
          err instanceof ApiError
            ? err
            : new ApiError('Unable to load this analysis.'),
        );
        setData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    run();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [enabled, ...deps]);

  return { data, error, loading, reload };
}
