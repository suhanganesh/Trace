export default function EmptyState({ title = 'No data available', description }) {
  return (
    <div className="rounded-lg border border-dashed border-trace-border bg-zinc-50/50 px-6 py-10 text-center">
      <p className="text-sm font-medium text-trace-text">{title}</p>
      {description ? <p className="mt-1 text-sm text-trace-muted">{description}</p> : null}
    </div>
  );
}
