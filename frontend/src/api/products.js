import { apiRequest } from './client';

export function fetchProducts({ metric = 'views', limit = 10 } = {}, options) {
  return apiRequest('/api/products', {
    ...options,
    params: { metric, limit },
  });
}

export function fetchProduct(itemId, options) {
  return apiRequest(`/api/products/${itemId}`, options);
}
