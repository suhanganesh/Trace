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
import { metricColumnKey } from '../../utils/analytics';
import { compactNumber, formatProductId } from '../../utils/formatters';

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-md border border-trace-border bg-trace-surface px-3 py-2 text-xs shadow-trace">
      <p className="font-medium text-trace-text">{row.name}</p>
      <p className="mt-1 tabular-nums text-trace-muted">{compactNumber(row.value)}</p>
    </div>
  );
}

export default function ProductRankChart({ products = [], metric = 'views' }) {
  const key = metricColumnKey(metric);
  const data = products
    .slice()
    .reverse()
    .map((product) => ({
      name: formatProductId(product.item_id),
      value: product[key],
    }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tickFormatter={(v) => compactNumber(v)} />
          <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(15, 118, 110, 0.06)' }} />
          <Bar dataKey="value" fill={CHART_COLORS.accent} radius={[0, 4, 4, 0]} barSize={16} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
