import { useOutletContext } from 'react-router-dom';
import { fetchDatasetInfo } from '../api/dataset';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import SectionHeader from '../components/analytics/SectionHeader';
import Badge from '../components/ui/Badge';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { EVENT_LABELS } from '../utils/constants';
import { compactNumber, formatDateRange } from '../utils/formatters';

const PIPELINE = [
  'Raw CSV',
  'Processing',
  'MongoDB',
  'FastAPI',
  'Trace',
];

export default function Dataset() {
  const { refreshToken } = useOutletContext();
  const { data, error, loading, reload } = useApi(
    (options) => fetchDatasetInfo(options),
    [refreshToken],
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-56 w-full" />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  return (
    <div className="max-w-5xl">
      <PageHeader
        title="Dataset"
        subtitle="RetailRocket event and catalog data used by Trace."
        meta={
          <>
            <Badge tone="accent">{data.dataset_name}</Badge>
            <Badge tone={data.database_status === 'connected' ? 'success' : 'warning'}>
              Database {data.database_status}
            </Badge>
          </>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ['Date range', formatDateRange(data.date_range?.start, data.date_range?.end)],
          ['Events', compactNumber(data.processed_event_count)],
          ['Visitors', compactNumber(data.unique_visitors)],
          ['Products', compactNumber(data.unique_products)],
          ['Property records', compactNumber(data.item_property_count)],
          ['Categories', compactNumber(data.category_count)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-trace-border bg-trace-surface p-4">
            <p className="text-xs uppercase tracking-wide text-trace-muted">{label}</p>
            <p className="mt-2 text-lg font-semibold tabular-nums text-trace-text">{value}</p>
          </div>
        ))}
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-trace-border bg-trace-surface p-5">
          <SectionHeader title="Events" description="Primary behavioral fact table in MongoDB." />
          <p className="text-sm text-trace-muted">
            {compactNumber(data.processed_event_count)} processed event records with types:
          </p>
          <ul className="mt-3 space-y-2 text-sm">
            {Object.entries(data.event_counts || {}).map(([event, count]) => (
              <li key={event} className="flex justify-between gap-3 border-b border-trace-border/70 py-2">
                <span>{EVENT_LABELS[event] || event}</span>
                <span className="tabular-nums font-medium">{compactNumber(count)}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border border-trace-border bg-trace-surface p-5">
          <SectionHeader title="Schema overview" />
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="font-medium text-trace-text">events</dt>
              <dd className="text-trace-muted">timestamp, visitorid, event, itemid, transactionid, date/time facets</dd>
            </div>
            <div>
              <dt className="font-medium text-trace-text">item_properties</dt>
              <dd className="text-trace-muted">timestamped EAV rows (itemid, property, value)</dd>
            </div>
            <div>
              <dt className="font-medium text-trace-text">category_tree</dt>
              <dd className="text-trace-muted">categoryid, parentid hierarchy</dd>
            </div>
          </dl>
        </section>
      </div>

      <section className="mt-8 rounded-lg border border-trace-border bg-trace-surface p-5">
        <SectionHeader title="Data pipeline" description="Big Data flow from CSV to Trace dashboard." />
        <div className="flex flex-wrap items-center gap-2 text-sm font-medium text-trace-text">
          {PIPELINE.map((step, index) => (
            <span key={step} className="inline-flex items-center gap-2">
              <span className="rounded-md border border-trace-border bg-zinc-50 px-3 py-1.5">{step}</span>
              {index < PIPELINE.length - 1 ? <span className="text-trace-muted">↓</span> : null}
            </span>
          ))}
        </div>
        <div className="mt-6 text-xs text-trace-muted">
          <p>Processing timestamp: {data.processing_information?.processing_timestamp_utc || '—'}</p>
          <p className="mt-1">
            Duplicate rows removed during processing:{' '}
            {data.processing_information?.duplicate_rows_removed ?? '—'}
          </p>
        </div>
      </section>
    </div>
  );
}
