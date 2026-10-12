import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CHART_COLORS } from '../../utils/constants';
import { eventLabel } from '../../utils/analytics';
import { compactNumber, formatPercent } from '../../utils/formatters';

const COLORS = {
  view: CHART_COLORS.view,
  addtocart: CHART_COLORS.addtocart,
  transaction: CHART_COLORS.transaction,
};

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-md border border-trace-border bg-trace-surface px-3 py-2 text-xs shadow-trace">
      <p className="font-medium text-trace-text">{row.label}</p>
      <p className="mt-1 tabular-nums text-trace-muted">
        {compactNumber(row.count)} ({formatPercent(row.percentage)})
      </p>
    </div>
  );
}

export default function EventDistribution({ items = [] }) {
  const data = items.map((item) => ({
    ...item,
    label: eventLabel(item.event),
  }));

  if (!data.length) return null;

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tickFormatter={(v) => compactNumber(v)} />
          <YAxis type="category" dataKey="label" width={92} tick={{ fontSize: 12 }} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(15, 118, 110, 0.06)' }} />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={22}>
            {data.map((entry) => (
              <Cell key={entry.event} fill={COLORS[entry.event] || CHART_COLORS.accent} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
