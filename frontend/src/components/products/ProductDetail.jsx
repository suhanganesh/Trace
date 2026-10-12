import MetricCard from '../analytics/MetricCard';
import ProductPropertyList from './ProductPropertyList';
import SectionHeader from '../analytics/SectionHeader';

export default function ProductDetailView({ product }) {
  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Views" value={product.views} />
        <MetricCard label="Add to cart" value={product.add_to_cart} />
        <MetricCard label="Transactions" value={product.transactions} />
        <MetricCard
          label="Conversion"
          value={product.conversion_rate}
          percent
          fromRatio
          hint="transactions / views"
        />
      </div>

      <section>
        <SectionHeader
          title="Latest properties"
          description="Most recent catalog attributes available for this product."
        />
        <ProductPropertyList properties={product.properties} />
      </section>
    </div>
  );
}
