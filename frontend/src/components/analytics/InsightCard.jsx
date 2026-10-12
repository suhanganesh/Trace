export default function InsightCard({ title, value, description }) {
  return (
    <div className="rounded-lg border border-trace-border bg-trace-surface px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-wide text-trace-muted">{title}</p>
      <p className="mt-2 text-lg font-semibold tabular-nums text-trace-text">{value}</p>
      {description ? <p className="mt-2 text-sm leading-relaxed text-trace-muted">{description}</p> : null}
    </div>
  );
}
