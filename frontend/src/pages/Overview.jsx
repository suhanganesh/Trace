import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { fetchOverview } from '../api/overview';
import { fetchFunnel } from '../api/funnel';
import { fetchTimeSeries } from '../api/timeSeries';
import { fetchReport } from '../api/report';
import { fetchDatasetInfo } from '../api/dataset';
import { ApiError } from '../api/client';
import PageHeader from '../components/layout/PageHeader';
import MetricCard from '../components/analytics/MetricCard';
import SectionHeader from '../components/analytics/SectionHeader';
import EventDistribution from '../components/analytics/EventDistribution';
import FunnelChart from '../components/analytics/FunnelChart';
import TimeSeriesChart from '../components/analytics/TimeSeriesChart';
import InsightCard from '../components/analytics/InsightCard';
import Badge from '../components/ui/Badge';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { APP_TAGLINE } from '../utils/constants';
import { compactNumber, formatDateRange, formatPercent } from '../utils/formatters';

export default function Overview() {
  const { refreshToken } = useOutletContext();
  const [state, setState] = useState({
    loading: true,
    error: null,
    overview: null,
    funnel: null,
    series: null,
    report: null,
    dataset: null,
  });

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function load() {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const [overview, funnel, series, report, dataset] = await Promise.all([
          fetchOverview({ signal: controller.signal }),
          fetchFunnel({ signal: controller.signal }),
          fetchTimeSeries({ granularity: 'daily' }, { signal: controller.signal }),
          fetchReport({ signal: controller.signal }),
          fetchDatasetInfo({ signal: controller.signal }),
        ]);
        if (!cancelled) {
          setState({
            loading: false,
            error: null,
            overview,
            funnel,
            series,
            report,
            dataset,
          });
        }
      } catch (err) {
        if (cancelled || err?.name === 'AbortError') return;
        setState({
          loading: false,
          error:
            err instanceof ApiError
              ? err
              : new ApiError('Unable to load this analysis.'),
          overview: null,
          funnel: null,
          series: null,
          report: null,
          dataset: null,
        });
      }
    }

    load();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [refreshToken]);

  const { loading, error, overview, funnel, series, report, dataset } = state;

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-3 lg:grid-cols-5">
          <Skeleton className="h-28 lg:col-span-2" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState message={error.message} onRetry={() => window.location.reload()} />
    );
  }

  const findings = (report?.key_findings || []).slice(0, 4);

  return (
    <div>
      <PageHeader
        title="E-commerce Intelligence"
        subtitle={APP_TAGLINE}
        meta={
          <>
            <Badge tone="neutral">
              {formatDateRange(overview.date_range.start, overview.date_range.end)}
            </Badge>
            <Badge tone="accent">{compactNumber(overview.total_events)} events</Badge>
            <Badge tone="neutral">{compactNumber(overview.unique_visitors)} visitors</Badge>
          </>
        }
      />

      <section className="grid gap-3 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <MetricCard
            label="Events analyzed"
            value={overview.total_events}
            emphasize
            hint="Processed RetailRocket event records in MongoDB"
          />
        </div>
        <MetricCard label="Unique visitors" value={overview.unique_visitors} />
        <MetricCard label="Unique products" value={overview.unique_products} />
        <MetricCard label="Transactions" value={overview.total_transactions} />
      </section>

      <section className="mt-3 max-w-sm">
        <MetricCard
          label="Visitor conversion"
          value={overview.visitor_conversion_rate}
          percent
          fromRatio
          hint="Unique visitors with ≥1 transaction / all unique visitors"
        />
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <section className="rounded-lg border border-trace-border bg-trace-surface p-5">
          <SectionHeader
            title="Event activity"
            description="Distribution of view, add-to-cart, and transaction events."
          />
          <EventDistribution items={overview.event_distribution} />
        </section>

        <section className="rounded-lg border border-trace-border bg-trace-surface p-5">
          <SectionHeader
            title="Conversion funnel"
            description="Unique visitors by stage — not a strict sequential path."
            hint={funnel.methodology}
          />
          <p className="mb-4 text-xs text-trace-muted">Unique visitors by stage</p>
          <FunnelChart stages={funnel.stages} />
        </section>
      </div>

      <section className="mt-8 rounded-lg border border-trace-border bg-trace-surface p-5">
        <SectionHeader
          title="Activity over time"
          description="Daily event volume from MongoDB time-series aggregation."
        />
        <TimeSeriesChart series={series.series} showEvents={['views', 'addtocart', 'transactions']} />
      </section>

      <section className="mt-8">
        <SectionHeader title="Key observations" description="Derived from /api/report calculations." />
        <div className="grid gap-4 md:grid-cols-2">
          {findings.map((finding) => (
            <InsightCard
              key={`${finding.metric}-${finding.value}`}
              title={finding.metric.replaceAll('_', ' ')}
              value={finding.value}
              description={finding.interpretation}
            />
          ))}
        </div>
      </section>

      <section className="mt-8 rounded-lg border border-trace-border bg-trace-surface p-5">
        <SectionHeader title="Dataset scale" description="Catalog and event footprint powering Trace." />
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Events</dt>
            <dd className="mt-1 tabular-nums text-lg font-semibold">
              {compactNumber(dataset.processed_event_count)}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Visitors</dt>
            <dd className="mt-1 tabular-nums text-lg font-semibold">
              {compactNumber(dataset.unique_visitors)}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Products</dt>
            <dd className="mt-1 tabular-nums text-lg font-semibold">
              {compactNumber(dataset.unique_products)}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Property records</dt>
            <dd className="mt-1 tabular-nums text-lg font-semibold">
              {compactNumber(dataset.item_property_count)}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Categories</dt>
            <dd className="mt-1 tabular-nums text-lg font-semibold">
              {compactNumber(dataset.category_count)}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-trace-muted">Date range</dt>
            <dd className="mt-1 text-sm font-medium">
              {formatDateRange(dataset.date_range?.start, dataset.date_range?.end)}
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-trace-muted">
          Visitor conversion on this page:{' '}
          {formatPercent(overview.visitor_conversion_rate, { fromRatio: true })}
        </p>
      </section>
    </div>
  );
}
