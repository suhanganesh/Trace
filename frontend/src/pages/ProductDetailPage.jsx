import { Link, useParams } from 'react-router-dom';
import { fetchProduct } from '../api/products';
import { useApi } from '../hooks/useApi';
import PageHeader from '../components/layout/PageHeader';
import ProductDetailView from '../components/products/ProductDetail';
import ErrorState from '../components/ui/ErrorState';
import Skeleton from '../components/ui/Skeleton';
import { formatProductId } from '../utils/formatters';
import { ArrowLeft } from 'lucide-react';

export default function ProductDetailPage() {
  const { itemId } = useParams();
  const numericId = Number(itemId);

  const { data, error, loading, reload } = useApi(
    (options) => fetchProduct(numericId, options),
    [itemId],
    { enabled: Number.isFinite(numericId) && numericId > 0 },
  );

  if (!Number.isFinite(numericId) || numericId <= 0) {
    return <ErrorState title="Invalid product ID." message="Use a positive numeric product identifier." />;
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        title={error.status === 404 ? 'Product not found.' : 'Unable to load this analysis.'}
        message={error.message}
        onRetry={reload}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title={formatProductId(data.item_id)}
        subtitle="Event-level engagement and latest catalog properties from MongoDB."
        actions={
          <Link
            to="/products"
            className="inline-flex items-center gap-2 rounded-md border border-trace-border bg-trace-surface px-3 py-1.5 text-sm font-medium text-trace-text transition-colors hover:bg-zinc-50 focus-ring"
          >
            <ArrowLeft size={16} />
            Back to Products
          </Link>
        }
      />
      <ProductDetailView product={data} />
    </div>
  );
}
