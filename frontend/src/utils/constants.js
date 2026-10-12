export const APP_NAME = 'TRACE';
export const APP_TAGLINE = 'E-commerce intelligence from large-scale event data.';

export const NAV_ITEMS = [
  { to: '/overview', label: 'Overview', icon: 'LayoutDashboard' },
  { to: '/behavior', label: 'Behavior', icon: 'Users' },
  { to: '/products', label: 'Products', icon: 'Package' },
  { to: '/time-analysis', label: 'Time Analysis', icon: 'Clock' },
  { to: '/report', label: 'Analytics Report', icon: 'FileBarChart' },
  { to: '/dataset', label: 'Dataset', icon: 'Database' },
];

export const EVENT_LABELS = {
  view: 'View',
  addtocart: 'Add to cart',
  transaction: 'Transaction',
};

export const METRIC_OPTIONS = [
  { value: 'views', label: 'Views' },
  { value: 'addtocart', label: 'Add to cart' },
  { value: 'transactions', label: 'Transactions' },
];

export const LIMIT_OPTIONS = [10, 25, 50, 100];

export const CHART_COLORS = {
  view: '#0f766e',
  addtocart: '#0369a1',
  transaction: '#a16207',
  accent: '#0f766e',
  muted: '#a1a1aa',
  grid: '#e4e4e7',
};
