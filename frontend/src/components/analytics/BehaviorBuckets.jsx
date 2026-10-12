import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CHART_COLORS } from '../../utils/constants';
import { compactNumber } from '../../utils/formatters';

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-md border border-trace-border bg-trace-surface px-3 py-2 text-xs shadow-trace">
      <p className="font-medium text-trace-text">{row.label}</p>
      <p className="mt-1 tabular-nums text-trace-muted">
        {compactNumber(row.visitor_count)} visitors
      </p>
    </div>
  );
}

export default function BehaviorBuckets({ buckets = [] }) {
  const data = buckets.map((bucket) => ({
    label: bucket.label,
    visitor_count: bucket.visitor_count,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={56} />
          <YAxis tickFormatter={(v) => compactNumber(v)} width={48} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(15, 118, 110, 0.06)' }} />
          <Bar dataKey="visitor_count" fill={CHART_COLORS.accent} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
