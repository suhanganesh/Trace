import { useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { fetchTimeSeries } from '../api/timeSeries';
import { fetchReport } from '../api/report';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import SectionHeader from '../components/analytics/SectionHeader';
import TimeSeriesChart from '../components/analytics/TimeSeriesChart';
import Select from '../components/ui/Select';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { compactNumber } from '../utils/formatters';

export default function TimeAnalysis() {
  const { refreshToken } = useOutletContext();
  const [granularity, setGranularity] = useState('daily');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const { data, error, loading, reload } = useApi(
    (options) =>
      fetchTimeSeries(
        {
          granularity,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        },
        options,
      ),
    [refreshToken, granularity, startDate, endDate],
  );

  const reportQuery = useApi((options) => fetchReport(options), [refreshToken]);

  const hourlyPattern = useMemo(() => {
    if (granularity !== 'hourly' || !data?.series?.length) return [];
    const buckets = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      total: 0,
    }));
    data.series.forEach((point) => {
      const match = String(point.timestamp).match(/T(\d{2}):/);
      const hour = match ? Number(match[1]) : null;
      if (hour != null && buckets[hour]) {
        buckets[hour].total += point.total_events;
      }
    });
    return buckets;
  }, [data, granularity]);

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  const peaks = reportQuery.data?.time_trends;

  return (
    <div>
      <PageHeader
        title="Time Analysis"
        subtitle="Understand when activity and conversions occur."
        actions={
          <div className="flex flex-wrap items-end gap-3">
            <Select
              label="Granularity"
              value={granularity}
              onChange={(e) => setGranularity(e.target.value)}
            >
              <option value="daily">Daily</option>
              <option value="hourly">Hourly</option>
            </Select>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-xs font-medium text-trace-muted">Start date</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="focus-ring rounded-md border border-trace-border bg-trace-surface px-2.5 py-1.5 text-sm"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              <span className="text-xs font-medium text-trace-muted">End date</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="focus-ring rounded-md border border-trace-border bg-trace-surface px-2.5 py-1.5 text-sm"
              />
            </label>
          </div>
        }
      />

      <section className="rounded-lg border border-trace-border bg-trace-surface p-5">
        <SectionHeader
          title="Event volume over time"
          description="Filtered server-side via MongoDB aggregation."
        />
        {loading ? <Skeleton className="h-72" /> : <TimeSeriesChart series={data?.series || []} />}
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-trace-border bg-trace-surface p-4">
          <p className="text-xs uppercase tracking-wide text-trace-muted">Busiest day</p>
          <p className="mt-2 text-sm font-medium">
            {peaks?.peak_activity_day?.date || '—'}
          </p>
          <p className="mt-1 tabular-nums text-xs text-trace-muted">
            {compactNumber(peaks?.peak_activity_day?.events)} events
          </p>
        </div>
        <div className="rounded-lg border border-trace-border bg-trace-surface p-4">
          <p className="text-xs uppercase tracking-wide text-trace-muted">Highest transaction day</p>
          <p className="mt-2 text-sm font-medium">
            {peaks?.peak_transaction_day?.date || '—'}
          </p>
          <p className="mt-1 tabular-nums text-xs text-trace-muted">
            {compactNumber(peaks?.peak_transaction_day?.transactions)} transaction events
          </p>
        </div>
        <div className="rounded-lg border border-trace-border bg-trace-surface p-4">
          <p className="text-xs uppercase tracking-wide text-trace-muted">Peak hour (UTC)</p>
          <p className="mt-2 text-sm font-medium">
            {peaks?.peak_activity_hour_utc?.hour != null
              ? `${String(peaks.peak_activity_hour_utc.hour).padStart(2, '0')}:00`
              : '—'}
          </p>
          <p className="mt-1 tabular-nums text-xs text-trace-muted">
            {compactNumber(peaks?.peak_activity_hour_utc?.events)} events
          </p>
        </div>
      </section>

      {granularity === 'hourly' && hourlyPattern.length ? (
        <section className="mt-8 rounded-lg border border-trace-border bg-trace-surface p-5">
          <SectionHeader
            title="Hourly pattern in selected range"
            description="Aggregated from the hourly series returned by the API."
          />
          <div className="grid grid-cols-12 gap-1">
            {hourlyPattern.map((bucket) => {
              const max = Math.max(...hourlyPattern.map((b) => b.total), 1);
              const intensity = bucket.total / max;
              return (
                <div key={bucket.hour} className="flex flex-col items-center gap-1">
                  <div
                    className="w-full rounded-sm bg-teal-700/90"
                    style={{ height: `${Math.max(intensity * 64, 4)}px` }}
                    title={`${bucket.hour}:00 — ${compactNumber(bucket.total)} events`}
                  />
                  <span className="text-[10px] tabular-nums text-trace-muted">{bucket.hour}</span>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}
    </div>
  );
}
