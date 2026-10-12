import { compactNumber, formatPercent } from '../../utils/formatters';

export default function FunnelChart({ stages = [] }) {
  if (!stages.length) return null;
  const maxCount = Math.max(...stages.map((stage) => stage.count), 1);

  return (
    <div className="space-y-3">
      {stages.map((stage, index) => {
        const width = `${Math.max((stage.count / maxCount) * 100, 8)}%`;
        return (
          <div key={stage.stage}>
            <div className="mb-1 flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium text-trace-text">{stage.stage}</span>
              <span className="tabular-nums text-trace-muted">
                {compactNumber(stage.count)} · {formatPercent(stage.percentage)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-zinc-100">
              <div
                className="h-2 rounded-full bg-trace-accent transition-all"
                style={{ width }}
                aria-hidden="true"
              />
            </div>
            {stage.dropoff_from_previous != null && index > 0 ? (
              <p className="mt-1 text-xs text-trace-muted">
                Drop-off from previous stage: {formatPercent(stage.dropoff_from_previous)}
              </p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
