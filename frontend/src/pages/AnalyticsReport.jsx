import { useOutletContext } from 'react-router-dom';
import { fetchReport } from '../api/report';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import SectionHeader from '../components/analytics/SectionHeader';
import FindingCard from '../components/analytics/FindingCard';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { compactNumber, formatDateRange, formatPercent } from '../utils/formatters';
import { formatProductId } from '../utils/formatters';

function ReportSection({ title, children }) {
  return (
    <section className="border-b border-trace-border pb-8">
      <SectionHeader title={title} />
      <div className="space-y-3 text-sm leading-relaxed text-trace-muted">{children}</div>
    </section>
  );
}

export default function AnalyticsReport() {
  const { refreshToken } = useOutletContext();
  const { data, error, loading, reload } = useApi(
    (options) => fetchReport(options),
    [refreshToken],
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error.message} onRetry={reload} />;
  }

  const { dataset_summary, engagement, conversion, product_performance, time_trends, key_findings } =
    data;

  return (
    <div className="max-w-5xl">
      <PageHeader
        title="Analytics Report"
        subtitle="A concise interpretation of Trace's e-commerce event data."
      />

      <div className="space-y-8">
        <ReportSection title="Executive summary">
          <p>
            Trace analyzed{' '}
            <strong className="text-trace-text">{compactNumber(dataset_summary.total_events)}</strong>{' '}
            events from{' '}
            <strong className="text-trace-text">{compactNumber(dataset_summary.unique_visitors)}</strong>{' '}
            visitors across{' '}
            <strong className="text-trace-text">{compactNumber(dataset_summary.unique_products)}</strong>{' '}
            products between{' '}
            {formatDateRange(dataset_summary.date_range?.start, dataset_summary.date_range?.end)}.
          </p>
        </ReportSection>

        <ReportSection title="Dataset scale">
          <ul className="list-disc space-y-2 pl-5">
            <li>Total events: {compactNumber(dataset_summary.total_events)}</li>
            <li>Unique visitors: {compactNumber(dataset_summary.unique_visitors)}</li>
            <li>Unique products: {compactNumber(dataset_summary.unique_products)}</li>
            <li>Daily series points: {compactNumber(time_trends.daily_series_points)}</li>
          </ul>
        </ReportSection>

        <ReportSection title="Engagement">
          <p>
            Views: {compactNumber(engagement.total_views)} · Add to cart:{' '}
            {compactNumber(engagement.total_add_to_cart)} · Transactions:{' '}
            {compactNumber(engagement.total_transactions)}
          </p>
          <p>Average events per visitor: {engagement.avg_events_per_visitor}</p>
        </ReportSection>

        <ReportSection title="Conversion">
          <p>
            Visitor conversion rate:{' '}
            {formatPercent(conversion.visitor_conversion_rate, { fromRatio: true })}
          </p>
          <p className="text-xs">{conversion.funnel?.methodology}</p>
        </ReportSection>

        <ReportSection title="Product performance">
          {product_performance.top_viewed?.[0] ? (
            <p>
              Top viewed: {formatProductId(product_performance.top_viewed[0].item_id)} (
              {compactNumber(product_performance.top_viewed[0].views)} views)
            </p>
          ) : null}
          {product_performance.top_purchased?.[0] ? (
            <p>
              Top purchased: {formatProductId(product_performance.top_purchased[0].item_id)} (
              {compactNumber(product_performance.top_purchased[0].transactions)} transaction events)
            </p>
          ) : null}
          {product_performance.high_view_low_conversion?.products?.length ? (
            <p>
              {product_performance.high_view_low_conversion.products.length} products flagged in
              the high-attention / low-conversion cohort.
            </p>
          ) : null}
        </ReportSection>

        <ReportSection title="Time trends">
          <p>
            Peak activity day: {time_trends.peak_activity_day?.date || '—'} (
            {compactNumber(time_trends.peak_activity_day?.events)} events)
          </p>
          <p>
            Peak transaction day: {time_trends.peak_transaction_day?.date || '—'} (
            {compactNumber(time_trends.peak_transaction_day?.transactions)} transaction events)
          </p>
          <p>
            Peak hour (UTC):{' '}
            {time_trends.peak_activity_hour_utc?.hour != null
              ? `${String(time_trends.peak_activity_hour_utc.hour).padStart(2, '0')}:00`
              : '—'}
          </p>
        </ReportSection>

        <section>
          <SectionHeader title="Key findings" />
          <div className="grid gap-4">
            {key_findings.map((finding) => (
              <FindingCard
                key={`${finding.metric}-${finding.value}`}
                category={finding.metric.replaceAll('_', ' ')}
                title={finding.interpretation}
                value={finding.value}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
