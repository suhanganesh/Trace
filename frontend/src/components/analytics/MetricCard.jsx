import { compactNumber, formatPercent } from '../../utils/formatters';

export default function MetricCard({
  label,
  value,
  hint,
  emphasize = false,
  percent = false,
  fromRatio = false,
}) {
  const display = percent
    ? formatPercent(value, { fromRatio })
    : compactNumber(value);

  return (
    <div
      className={`rounded-lg border border-trace-border bg-trace-surface px-4 py-3 ${
        emphasize ? 'lg:px-6 lg:py-5' : ''
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-trace-muted">{label}</p>
      <p
        className={`tabular-nums font-semibold tracking-tight text-trace-text ${
          emphasize ? 'mt-2 text-4xl' : 'mt-1 text-2xl'
        }`}
      >
        {display}
      </p>
      {hint ? <p className="mt-1 text-xs text-trace-muted">{hint}</p> : null}
    </div>
  );
}
