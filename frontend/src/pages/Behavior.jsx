import { useOutletContext } from 'react-router-dom';
import { fetchBehavior } from '../api/behavior';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import SectionHeader from '../components/analytics/SectionHeader';
import MetricCard from '../components/analytics/MetricCard';
import BehaviorBuckets from '../components/analytics/BehaviorBuckets';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { compactNumber, formatPercent, formatVisitorId } from '../utils/formatters';

export default function Behavior() {
  const { refreshToken } = useOutletContext();
  const { data, error, loading, reload } = useApi(
    (options) => fetchBehavior(options),
    [refreshToken],
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-3 sm:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  const { summary, activity_distribution, top_visitors, engagement_metrics } = data;
  const addToCartRate = summary.total_visitors
    ? summary.visitors_with_add_to_cart / summary.total_visitors
    : 0;
  const txRate = summary.total_visitors
    ? summary.visitors_with_transaction / summary.total_visitors
    : 0;

  return (
    <div>
      <PageHeader
        title="Visitor Behavior"
        subtitle="How users browse, engage, and convert across the event stream."
      />

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Total visitors" value={summary.total_visitors} />
        <MetricCard label="Events per visitor" value={summary.avg_events_per_visitor} />
        <MetricCard label="Views per visitor" value={summary.avg_views_per_visitor} />
        <MetricCard label="Repeat visitors" value={summary.repeat_visitors} />
      </section>

      <section className="mt-3 grid gap-3 sm:grid-cols-2">
        <MetricCard label="Add-to-cart rate" value={addToCartRate} percent fromRatio />
        <MetricCard label="Transaction rate" value={txRate} percent fromRatio />
      </section>

      <section className="mt-8 rounded-lg border border-trace-border bg-trace-surface p-5">
        <SectionHeader
          title="Visitor activity distribution"
          description="How many events each visitor generated."
        />
        <BehaviorBuckets buckets={activity_distribution} />
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-trace-border bg-trace-surface p-5 lg:col-span-1">
          <SectionHeader title="Engagement patterns" />
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-trace-muted">Single-event visitors</dt>
              <dd className="tabular-nums font-medium">
                {compactNumber(engagement_metrics.single_event_visitors)}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-trace-muted">Multi-event visitors</dt>
              <dd className="tabular-nums font-medium">
                {compactNumber(engagement_metrics.multi_event_visitors)}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-trace-muted">Visitors with purchase</dt>
              <dd className="tabular-nums font-medium">
                {formatPercent(engagement_metrics.pct_visitors_with_purchase, { fromRatio: false })}
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border border-trace-border bg-trace-surface p-5 lg:col-span-2">
          <SectionHeader title="Top active visitors" description="Anonymous visitor IDs only." />
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-trace-border text-left text-xs uppercase tracking-wide text-trace-muted">
                <tr>
                  <th className="py-2 pr-4 font-medium">Visitor</th>
                  <th className="py-2 pr-4 text-right font-medium">Events</th>
                  <th className="py-2 pr-4 text-right font-medium">Views</th>
                  <th className="py-2 pr-4 text-right font-medium">Add to cart</th>
                  <th className="py-2 text-right font-medium">Transactions</th>
                </tr>
              </thead>
              <tbody>
                {top_visitors.map((visitor) => (
                  <tr key={visitor.visitor_id} className="border-b border-trace-border/70">
                    <td className="py-2 pr-4 font-medium">{formatVisitorId(visitor.visitor_id)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{compactNumber(visitor.total_events)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{compactNumber(visitor.views)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{compactNumber(visitor.add_to_cart)}</td>
                    <td className="py-2 text-right tabular-nums">{compactNumber(visitor.transactions)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
