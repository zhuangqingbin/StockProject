import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

api.interceptors.response.use(
  (res) => {
    if (res.data && res.data.code === 0) return res.data.data;
    return Promise.reject(new Error(res.data?.message || 'Request failed'));
  },
  (err) => Promise.reject(err)
);

export default api;

// === Stock API ===
export const stockApi = {
  search: (keyword) => api.get('/stocks/search', { params: { keyword } }),
  daily: (tsCode, startDate, endDate, indicators = '') =>
    api.get(`/stocks/daily/${tsCode}`, { params: { start_date: startDate, end_date: endDate, indicators } }),
  marketOverview: () => api.get('/stocks/market/overview'),
};

// === Market API ===
export const marketApi = {
  heatmap: (tradeDate = '') => api.get('/market/heatmap', { params: { trade_date: tradeDate } }),
  topStocks: (sortBy = 'pct_chg', direction = 'desc', limit = 20, tradeDate = '') =>
    api.get('/market/top-stocks', { params: { sort_by: sortBy, direction, limit, trade_date: tradeDate } }),
  compare: (codes, startDate, endDate) =>
    api.get('/market/compare', { params: { codes, start_date: startDate, end_date: endDate } }),
  moneyflow: (tsCode, startDate, endDate) =>
    api.get(`/market/moneyflow/${tsCode}`, { params: { start_date: startDate, end_date: endDate } }),
  toplist: (tradeDate) => api.get('/market/toplist', { params: { trade_date: tradeDate } }),
  statistics: () => api.get('/market/statistics'),
};

// === Strategy API ===
export const strategyApi = {
  list: () => api.get('/strategy/list'),
  backtest: (params) => api.post('/strategy/backtest', params),
  compare: (params) => api.post('/strategy/compare', params),
};
