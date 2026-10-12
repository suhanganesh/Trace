import { Link } from 'react-router-dom';
import { metricColumnKey } from '../../utils/analytics';
import { compactNumber, formatPercent, formatProductId } from '../../utils/formatters';

export default function ProductTable({ products = [], highlightMetric = 'views' }) {
  const highlightKey = metricColumnKey(highlightMetric);

  return (
    <div className="overflow-x-auto rounded-lg border border-trace-border bg-trace-surface">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 bg-zinc-50 text-left text-xs uppercase tracking-wide text-trace-muted">
          <tr className="border-b border-trace-border">
            <th className="px-4 py-2.5 font-medium">Rank</th>
            <th className="px-4 py-2.5 font-medium">Product</th>
            <th className="px-4 py-2.5 text-right font-medium">Views</th>
            <th className="px-4 py-2.5 text-right font-medium">Add to cart</th>
            <th className="px-4 py-2.5 text-right font-medium">Transactions</th>
            <th className="px-4 py-2.5 text-right font-medium">Conversion</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr
              key={product.item_id}
              className="border-b border-trace-border/80 transition-colors hover:bg-zinc-50/80"
            >
              <td className="px-4 py-2.5 tabular-nums text-trace-muted">{product.rank}</td>
              <td className="px-4 py-2.5">
                <Link
                  to={`/products/${product.item_id}`}
                  className="font-medium text-teal-800 hover:underline focus-ring rounded-sm"
                >
                  {formatProductId(product.item_id)}
                </Link>
              </td>
              {['views', 'add_to_cart', 'transactions'].map((column) => (
                <td
                  key={column}
                  className={`px-4 py-2.5 text-right tabular-nums ${
                    column === highlightKey ? 'font-semibold text-trace-text' : 'text-trace-muted'
                  }`}
                >
                  {compactNumber(product[column])}
                </td>
              ))}
              <td className="px-4 py-2.5 text-right tabular-nums text-trace-muted">
                {formatPercent(product.conversion_rate, { fromRatio: true })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
