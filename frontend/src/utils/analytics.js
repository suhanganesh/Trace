import { EVENT_LABELS } from './constants';

export function eventLabel(eventKey) {
  return EVENT_LABELS[eventKey] || eventKey;
}

export function metricField(metric) {
  if (metric === 'addtocart') return 'add_to_cart';
  return metric;
}

export function metricColumnKey(metric) {
  return metricField(metric);
}
