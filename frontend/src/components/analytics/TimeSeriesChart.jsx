import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CHART_COLORS } from '../../utils/constants';
import { compactNumber } from '../../utils/formatters';

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-trace-border bg-trace-surface px-3 py-2 text-xs shadow-trace">
      <p className="font-medium text-trace-text">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="mt-1 tabular-nums text-trace-muted">
          {entry.name}: {compactNumber(entry.value)}
        </p>
      ))}
    </div>
  );
}

export default function TimeSeriesChart({ series = [], showEvents = ['views', 'addtocart', 'transactions'] }) {
  const data = series.map((point) => ({
    ...point,
    label: point.timestamp,
  }));

  if (!data.length) return null;

  const config = {
    views: { stroke: CHART_COLORS.view, fill: CHART_COLORS.view, name: 'Views' },
    addtocart: { stroke: CHART_COLORS.addtocart, fill: CHART_COLORS.addtocart, name: 'Add to cart' },
    transactions: {
      stroke: CHART_COLORS.transaction,
      fill: CHART_COLORS.transaction,
      name: 'Transactions',
    },
    total_events: { stroke: CHART_COLORS.muted, fill: CHART_COLORS.muted, name: 'Total events' },
  };

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            minTickGap={24}
            tick={{ fontSize: 11 }}
            tickFormatter={(value) =>
              value.length > 10 ? value.slice(0, 10) : value
            }
          />
          <YAxis tickFormatter={(v) => compactNumber(v)} width={48} />
          <Tooltip content={<ChartTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {showEvents.map((key) =>
            config[key] ? (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                name={config[key].name}
                stroke={config[key].stroke}
                fill={config[key].fill}
                fillOpacity={0.12}
                strokeWidth={2}
                dot={false}
              />
            ) : null,
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
