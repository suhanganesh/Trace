export function compactNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—';
  }
  const num = Number(value);
  const abs = Math.abs(num);
  if (abs >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')}M`;
  }
  if (abs >= 1_000) {
    return `${(num / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
  }
  return num.toLocaleString('en-US');
}

export function formatInteger(value) {
  if (value === null || value === undefined) return '—';
  return Number(value).toLocaleString('en-US');
}

export function formatPercent(value, { fromRatio = false } = {}) {
  if (value === null || value === undefined) return '—';
  const pct = fromRatio ? Number(value) * 100 : Number(value);
  return `${pct.toFixed(2).replace(/\.00$/, '')}%`;
}

export function formatDate(isoDate) {
  if (!isoDate) return '—';
  const date = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(date.getTime())) return isoDate;
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function formatDateRange(start, end) {
  if (!start || !end) return '—';
  return `${formatDate(start)} — ${formatDate(end)}`;
}

export function formatShortDate(isoDate) {
  if (!isoDate) return '—';
  return isoDate;
}

export function formatVisitorId(id) {
  return `#${Number(id).toLocaleString('en-US')}`;
}

export function formatProductId(id) {
  return `Product #${Number(id).toLocaleString('en-US')}`;
}
