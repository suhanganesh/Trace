import EmptyState from '../ui/EmptyState';

export default function ProductPropertyList({ properties = {} }) {
  const entries = Object.entries(properties);
  if (!entries.length) {
    return <EmptyState title="No property metadata available." />;
  }

  return (
    <dl className="divide-y divide-trace-border rounded-lg border border-trace-border bg-trace-surface">
      {entries.map(([key, meta]) => (
        <div key={key} className="grid gap-1 px-4 py-3 sm:grid-cols-3">
          <dt className="text-sm font-medium text-trace-text">{key}</dt>
          <dd className="sm:col-span-2 text-sm text-trace-muted">
            <span className="font-mono text-trace-text">{meta?.value ?? '—'}</span>
            {meta?.recorded_at ? (
              <span className="mt-1 block text-xs">Recorded {meta.recorded_at}</span>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}
