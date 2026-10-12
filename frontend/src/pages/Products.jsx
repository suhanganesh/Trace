import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { fetchProducts } from '../api/products';
import { fetchReport } from '../api/report';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import SectionHeader from '../components/analytics/SectionHeader';
import ProductTable from '../components/analytics/ProductTable';
import ProductRankChart from '../components/analytics/ProductRankChart';
import Select from '../components/ui/Select';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { LIMIT_OPTIONS, METRIC_OPTIONS } from '../utils/constants';
import { compactNumber, formatPercent, formatProductId } from '../utils/formatters';

export default function Products() {
  const { refreshToken } = useOutletContext();
  const [metric, setMetric] = useState('views');
  const [limit, setLimit] = useState(25);

  const { data, error, loading, reload } = useApi(
    (options) => fetchProducts({ metric, limit }, options),
    [refreshToken, metric, limit],
  );

  const reportQuery = useApi(
    (options) => fetchReport(options),
    [refreshToken],
  );

  const opportunities =
    reportQuery.data?.product_performance?.high_view_low_conversion?.products || [];
  const oppMethodology =
    reportQuery.data?.product_performance?.high_view_low_conversion?.methodology;

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  return (
    <div>
      <PageHeader
        title="Product Analytics"
        subtitle="Identify products that attract attention, generate intent, and convert."
        actions={
          <div className="flex flex-wrap gap-3">
            <Select label="Metric" value={metric} onChange={(e) => setMetric(e.target.value)}>
              {METRIC_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
            <Select label="Limit" value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
              {LIMIT_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <section>
          <SectionHeader
            title="Top products"
            description={`Ranked by ${METRIC_OPTIONS.find((m) => m.value === metric)?.label.toLowerCase()}.`}
          />
          {loading ? <Skeleton className="h-72" /> : <ProductRankChart products={data.products} metric={metric} />}
        </section>
        <section>
          <SectionHeader title="Ranking table" description="Product conversion = transactions / views." />
          {loading ? <Skeleton className="h-72" /> : (
            <ProductTable products={data.products} highlightMetric={metric} />
          )}
        </section>
      </div>

      <section className="mt-10">
        <SectionHeader
          title="High attention, low conversion"
          description="Products receiving substantial attention but relatively few purchases."
          hint={oppMethodology}
        />
        {reportQuery.loading ? (
          <Skeleton className="h-40" />
        ) : opportunities.length ? (
          <div className="overflow-x-auto rounded-lg border border-trace-border bg-trace-surface">
            <table className="min-w-full text-sm">
              <thead className="border-b border-trace-border bg-zinc-50 text-left text-xs uppercase tracking-wide text-trace-muted">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Product</th>
                  <th className="px-4 py-2.5 text-right font-medium">Views</th>
                  <th className="px-4 py-2.5 text-right font-medium">Transactions</th>
                  <th className="px-4 py-2.5 text-right font-medium">Conversion</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((item) => (
                  <tr key={item.item_id} className="border-b border-trace-border/80">
                    <td className="px-4 py-2.5">{formatProductId(item.item_id)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{compactNumber(item.views)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {compactNumber(item.transactions)}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {formatPercent(item.conversion_rate, { fromRatio: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-trace-muted">No opportunity cohort returned by the API.</p>
        )}
      </section>
    </div>
  );
}
