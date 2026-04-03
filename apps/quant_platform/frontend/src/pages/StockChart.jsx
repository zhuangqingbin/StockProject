import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactEChartsCore from 'echarts-for-react';
import { Search, Settings2, X } from 'lucide-react';
import { stockApi } from '../utils/api';
import dayjs from 'dayjs';

const INDICATOR_OPTIONS = [
  { key: 'MA5', label: 'MA5', color: '#f59e0b' },
  { key: 'MA10', label: 'MA10', color: '#3b82f6' },
  { key: 'MA20', label: 'MA20', color: '#a855f7' },
  { key: 'MA60', label: 'MA60', color: '#22c55e' },
  { key: 'EMA12', label: 'EMA12', color: '#06b6d4' },
  { key: 'EMA26', label: 'EMA26', color: '#f43f5e' },
  { key: 'BOLL', label: '布林带', color: '#8b5cf6' },
  { key: 'MACD', label: 'MACD', color: null },
  { key: 'KDJ', label: 'KDJ', color: null },
  { key: 'RSI', label: 'RSI', color: null },
  { key: 'VOL_MA', label: '成交量均线', color: null },
];

function buildChartOption(data, indicators, stockName) {
  if (!data || data.length === 0) return {};

  const dates = data.map(d => d.date);
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
  const volumes = data.map(d => d.volume);

  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];
  let gridIndex = 0;

  // Main K-line grid
  grids.push({ left: 60, right: 30, top: 60, height: '45%' });
  xAxes.push({ type: 'category', data: dates, gridIndex, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#1e2d45' } } });
  yAxes.push({ gridIndex, scale: true, splitLine: { lineStyle: { color: '#1e2d4520' } }, axisLine: { lineStyle: { color: '#1e2d45' } }, axisLabel: { color: '#94a3b8' } });

  series.push({
    name: stockName || 'K线',
    type: 'candlestick',
    data: ohlc,
    xAxisIndex: gridIndex,
    yAxisIndex: gridIndex,
    itemStyle: {
      color: '#ef4444',
      color0: '#22c55e',
      borderColor: '#ef4444',
      borderColor0: '#22c55e',
    },
  });

  // Overlay indicators on main chart
  const overlayKeys = ['MA5','MA10','MA20','MA60','EMA12','EMA26','BOLL_MID','BOLL_UP','BOLL_DN'];
  const colorMap = {
    MA5: '#f59e0b', MA10: '#3b82f6', MA20: '#a855f7', MA60: '#22c55e',
    EMA12: '#06b6d4', EMA26: '#f43f5e',
    BOLL_MID: '#8b5cf6', BOLL_UP: '#8b5cf680', BOLL_DN: '#8b5cf680'
  };

  if (indicators) {
    for (const key of Object.keys(indicators)) {
      if (overlayKeys.includes(key)) {
        series.push({
          name: key,
          type: 'line',
          data: indicators[key],
          xAxisIndex: 0,
          yAxisIndex: 0,
          lineStyle: { width: 1, color: colorMap[key] || '#94a3b8' },
          symbol: 'none',
          smooth: true,
        });
      }
    }
  }

  gridIndex++;

  // Volume grid
  const volTop = '60%';
  grids.push({ left: 60, right: 30, top: volTop, height: '12%' });
  xAxes.push({ type: 'category', data: dates, gridIndex, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#1e2d45' } } });
  yAxes.push({ gridIndex, scale: true, splitLine: { show: false }, axisLabel: { show: false } });

  series.push({
    name: '成交量',
    type: 'bar',
    data: data.map((d, i) => ({
      value: d.volume,
      itemStyle: { color: d.close >= d.open ? '#ef444480' : '#22c55e80' },
    })),
    xAxisIndex: gridIndex,
    yAxisIndex: gridIndex,
  });

  // VOL_MA overlay
  if (indicators?.VOL_MA5) {
    series.push({ name: 'VOL_MA5', type: 'line', data: indicators.VOL_MA5, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' });
  }
  if (indicators?.VOL_MA10) {
    series.push({ name: 'VOL_MA10', type: 'line', data: indicators.VOL_MA10, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' });
  }

  gridIndex++;

  // Sub-indicator grids (MACD, KDJ, RSI)
  if (indicators?.DIF) {
    grids.push({ left: 60, right: 30, top: '76%', height: '10%' });
    xAxes.push({ type: 'category', data: dates, gridIndex, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#1e2d45' } } });
    yAxes.push({ gridIndex, scale: true, splitLine: { show: false }, axisLabel: { color: '#94a3b8', fontSize: 10 } });

    series.push(
      { name: 'DIF', type: 'line', data: indicators.DIF, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
      { name: 'DEA', type: 'line', data: indicators.DEA, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
      {
        name: 'MACD', type: 'bar', data: indicators.MACD?.map(v => ({
          value: v, itemStyle: { color: v >= 0 ? '#ef4444' : '#22c55e' }
        })),
        xAxisIndex: gridIndex, yAxisIndex: gridIndex,
      }
    );
    gridIndex++;
  }

  if (indicators?.K) {
    const top = indicators?.DIF ? '88%' : '76%';
    grids.push({ left: 60, right: 30, top, height: '10%' });
    xAxes.push({ type: 'category', data: dates, gridIndex, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#1e2d45' } } });
    yAxes.push({ gridIndex, scale: true, splitLine: { show: false }, axisLabel: { color: '#94a3b8', fontSize: 10 } });

    series.push(
      { name: 'K', type: 'line', data: indicators.K, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' },
      { name: 'D', type: 'line', data: indicators.D, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' },
      { name: 'J', type: 'line', data: indicators.J, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#a855f7' }, symbol: 'none' }
    );
    gridIndex++;
  }

  if (indicators?.RSI14) {
    const top = (indicators?.DIF && indicators?.K) ? '100%' : (indicators?.DIF || indicators?.K) ? '88%' : '76%';
    // only add if there's room
    if (parseFloat(top) < 95) {
      grids.push({ left: 60, right: 30, top, height: '10%' });
      xAxes.push({ type: 'category', data: dates, gridIndex, axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 0 }, axisLine: { lineStyle: { color: '#1e2d45' } } });
      yAxes.push({ gridIndex, scale: true, splitLine: { show: false }, axisLabel: { color: '#94a3b8', fontSize: 10 } });

      series.push(
        { name: 'RSI14', type: 'line', data: indicators.RSI14, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none' }
      );
      if (indicators.RSI6) {
        series.push({ name: 'RSI6', type: 'line', data: indicators.RSI6, xAxisIndex: gridIndex, yAxisIndex: gridIndex, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none' });
      }
    }
  }

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { color: '#94a3b830' } },
      backgroundColor: '#111827ee',
      borderColor: '#1e2d45',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
    },
    legend: { show: false },
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    series,
    dataZoom: [
      { type: 'inside', xAxisIndex: xAxes.map((_, i) => i), start: Math.max(0, 100 - 200 / dates.length * 100), end: 100 },
      { type: 'slider', xAxisIndex: xAxes.map((_, i) => i), bottom: 5, height: 20, borderColor: '#1e2d45', backgroundColor: '#0a0e17', fillerColor: '#3b82f620', textStyle: { color: '#94a3b8', fontSize: 10 } },
    ],
  };
}


export default function StockChart() {
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [selectedIndicators, setSelectedIndicators] = useState(['MA5', 'MA20', 'MACD']);
  const [dateRange, setDateRange] = useState({
    start: dayjs().subtract(1, 'year').format('YYYYMMDD'),
    end: dayjs().format('YYYYMMDD'),
  });
  const [loading, setLoading] = useState(false);
  const [showSearch, setShowSearch] = useState(true);
  const searchTimeout = useRef(null);

  const handleSearch = useCallback((text) => {
    setSearchText(text);
    clearTimeout(searchTimeout.current);
    if (text.length < 1) { setSearchResults([]); return; }
    searchTimeout.current = setTimeout(async () => {
      try {
        const results = await stockApi.search(text);
        setSearchResults(results || []);
      } catch { setSearchResults([]); }
    }, 300);
  }, []);

  const selectStock = (stock) => {
    setSelectedStock(stock);
    setShowSearch(false);
    setSearchText('');
    setSearchResults([]);
    loadData(stock.ts_code);
  };

  const loadData = async (tsCode) => {
    setLoading(true);
    try {
      const indStr = selectedIndicators.join(',');
      const result = await stockApi.daily(tsCode, dateRange.start, dateRange.end, indStr);
      setChartData(result?.data || []);
      setIndicators(result?.indicators || {});
    } catch (err) {
      console.error('加载数据失败:', err);
    }
    setLoading(false);
  };

  const toggleIndicator = (key) => {
    setSelectedIndicators(prev =>
      prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]
    );
  };

  useEffect(() => {
    if (selectedStock) loadData(selectedStock.ts_code);
  }, [selectedIndicators, dateRange]);

  const chartOption = buildChartOption(chartData, indicators, selectedStock?.name);

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <div className="flex items-center gap-2 bg-[#111827] border border-[#1e2d45] rounded-lg px-3 py-2 w-[280px]">
              <Search size={16} className="text-slate-500" />
              <input
                className="bg-transparent border-0 p-0 text-sm flex-1 outline-none placeholder-slate-600"
                placeholder="搜索股票代码或名称..."
                value={searchText}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => setShowSearch(true)}
              />
            </div>
            {showSearch && searchResults.length > 0 && (
              <div className="absolute top-full left-0 mt-1 w-full bg-[#111827] border border-[#1e2d45] rounded-lg shadow-2xl z-50 max-h-[300px] overflow-auto">
                {searchResults.map(s => (
                  <div
                    key={s.ts_code}
                    className="px-3 py-2 hover:bg-blue-500/10 cursor-pointer flex items-center justify-between text-sm transition-colors"
                    onClick={() => selectStock(s)}
                  >
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs text-slate-500 font-mono">{s.ts_code}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {selectedStock && (
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold">{selectedStock.name}</span>
              <span className="text-sm text-slate-500 font-mono">{selectedStock.ts_code}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400">{selectedStock.industry}</span>
            </div>
          )}
        </div>

        {/* Date Range */}
        <div className="flex items-center gap-2 text-sm">
          {[
            { label: '3月', months: 3 },
            { label: '6月', months: 6 },
            { label: '1年', months: 12 },
            { label: '3年', months: 36 },
          ].map(({ label, months }) => (
            <button
              key={months}
              className={`px-3 py-1 rounded-md transition-colors ${
                dateRange.start === dayjs().subtract(months, 'month').format('YYYYMMDD')
                  ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'
              }`}
              onClick={() => {
                setDateRange({
                  start: dayjs().subtract(months, 'month').format('YYYYMMDD'),
                  end: dayjs().format('YYYYMMDD'),
                });
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Indicator Toggles */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Settings2 size={14} className="text-slate-500" />
        {INDICATOR_OPTIONS.map(({ key, label, color }) => (
          <button
            key={key}
            onClick={() => toggleIndicator(key)}
            className={`px-2.5 py-1 rounded-md text-xs transition-all ${
              selectedIndicators.includes(key)
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
          >
            {color && selectedIndicators.includes(key) && (
              <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: color }} />
            )}
            {label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="flex-1 glass-card p-4 min-h-0">
        {loading ? (
          <div className="h-full flex items-center justify-center text-slate-500">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mr-3" />
            加载中...
          </div>
        ) : !selectedStock ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <Search size={48} className="mb-4 opacity-30" />
            <p className="text-lg">搜索股票开始分析</p>
            <p className="text-sm mt-1">支持股票代码、名称搜索</p>
          </div>
        ) : chartData && chartData.length > 0 ? (
          <ReactEChartsCore
            option={chartOption}
            style={{ height: '100%', width: '100%' }}
            notMerge={true}
          />
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500">暂无数据</div>
        )}
      </div>
    </div>
  );
}
