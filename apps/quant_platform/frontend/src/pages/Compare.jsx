import React, { useState, useRef, useCallback } from 'react';
import ReactEChartsCore from 'echarts-for-react';
import { GitCompare, Plus, X, Search, TrendingUp, TrendingDown } from 'lucide-react';
import { stockApi, marketApi } from '../utils/api';
import dayjs from 'dayjs';

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#a855f7', '#06b6d4'];

export default function Compare() {
  const [stocks, setStocks] = useState([]);  // [{ ts_code, name }]
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [compareData, setCompareData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange] = useState({
    start: dayjs().subtract(1, 'year').format('YYYYMMDD'),
    end: dayjs().format('YYYYMMDD'),
  });
  const searchTimeout = useRef(null);

  const handleSearch = useCallback((text) => {
    setSearchText(text);
    clearTimeout(searchTimeout.current);
    if (text.length < 1) { setSearchResults([]); return; }
    searchTimeout.current = setTimeout(async () => {
      try {
        const results = await stockApi.search(text);
        setSearchResults(results?.filter(r => !stocks.find(s => s.ts_code === r.ts_code)) || []);
      } catch { setSearchResults([]); }
    }, 300);
  }, [stocks]);

  const addStock = (stock) => {
    if (stocks.length >= 6) return;
    if (stocks.find(s => s.ts_code === stock.ts_code)) return;
    setStocks(prev => [...prev, { ts_code: stock.ts_code, name: stock.name }]);
    setSearchText('');
    setSearchResults([]);
  };

  const removeStock = (tsCode) => {
    setStocks(prev => prev.filter(s => s.ts_code !== tsCode));
    setCompareData(prev => {
      if (!prev) return prev;
      const next = { ...prev };
      delete next[tsCode];
      return Object.keys(next).length > 0 ? next : null;
    });
  };

  const runCompare = async () => {
    if (stocks.length < 2) return;
    setLoading(true);
    try {
      const codes = stocks.map(s => s.ts_code).join(',');
      const data = await marketApi.compare(codes, dateRange.start, dateRange.end);
      setCompareData(data);
    } catch (err) {
      console.error('对比失败:', err);
    }
    setLoading(false);
  };

  // Build chart
  const chartOption = compareData ? (() => {
    const entries = Object.entries(compareData);
    if (entries.length === 0) return {};
    
    const allDates = entries[0][1].data.map(d => d.date);
    
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#111827ee',
        borderColor: '#1e2d45',
        textStyle: { color: '#e2e8f0', fontSize: 12 },
        formatter: (params) => {
          let html = `<div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">${params[0].axisValue}</div>`;
          params.forEach(p => {
            html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
              <span style="width:8px;height:8px;border-radius:50%;background:${p.color};"></span>
              <span>${p.seriesName}</span>
              <span style="margin-left:auto;font-weight:600;">${p.value?.toFixed(2)}</span>
            </div>`;
          });
          return html;
        }
      },
      legend: {
        data: entries.map(([_, info]) => info.name),
        textStyle: { color: '#94a3b8', fontSize: 11 },
        top: 5,
      },
      grid: { left: 50, right: 30, top: 40, bottom: 30 },
      xAxis: {
        type: 'category',
        data: allDates,
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        axisLine: { lineStyle: { color: '#1e2d45' } },
      },
      yAxis: {
        type: 'value',
        name: '归一化(%)',
        nameTextStyle: { color: '#94a3b8', fontSize: 10 },
        axisLabel: { color: '#94a3b8', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1e2d4520' } },
      },
      series: entries.map(([code, info], i) => ({
        name: info.name,
        type: 'line',
        data: info.data.map(d => d.close),
        lineStyle: { width: 2, color: COLORS[i % COLORS.length] },
        symbol: 'none',
        smooth: true,
      })),
    };
  })() : {};

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <GitCompare size={24} className="text-purple-400" />
        <div>
          <h2 className="text-2xl font-bold">多股对比</h2>
          <p className="text-sm text-slate-500">选择2-6只股票，归一化走势对比</p>
        </div>
      </div>

      {/* Stock Selection Bar */}
      <div className="glass-card p-4 mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          {/* Selected stocks */}
          {stocks.map((s, i) => (
            <div
              key={s.ts_code}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm"
              style={{
                borderColor: COLORS[i % COLORS.length] + '60',
                backgroundColor: COLORS[i % COLORS.length] + '15',
              }}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              <span className="font-medium">{s.name}</span>
              <span className="text-xs text-slate-500 font-mono">{s.ts_code}</span>
              <button onClick={() => removeStock(s.ts_code)} className="text-slate-500 hover:text-white ml-1">
                <X size={14} />
              </button>
            </div>
          ))}

          {/* Search to add */}
          {stocks.length < 6 && (
            <div className="relative">
              <div className="flex items-center gap-2 bg-[#0a0e17] border border-[#1e2d45] rounded-lg px-3 py-1.5 w-[220px]">
                <Plus size={14} className="text-slate-500" />
                <input
                  className="bg-transparent border-0 p-0 text-sm flex-1 outline-none placeholder-slate-600"
                  placeholder="添加股票..."
                  value={searchText}
                  onChange={(e) => handleSearch(e.target.value)}
                />
              </div>
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-[280px] bg-[#111827] border border-[#1e2d45] rounded-lg shadow-2xl z-50 max-h-[200px] overflow-auto">
                  {searchResults.slice(0, 10).map(s => (
                    <div
                      key={s.ts_code}
                      className="px-3 py-2 hover:bg-blue-500/10 cursor-pointer flex justify-between text-sm"
                      onClick={() => addStock(s)}
                    >
                      <span>{s.name}</span>
                      <span className="text-xs text-slate-500 font-mono">{s.ts_code}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Compare button */}
          <button
            onClick={runCompare}
            disabled={stocks.length < 2 || loading}
            className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-500 text-white text-sm font-medium disabled:opacity-30 hover:opacity-90 transition-opacity ml-auto"
          >
            {loading ? '对比中...' : '开始对比'}
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="glass-card p-4" style={{ minHeight: 450 }}>
        {compareData ? (
          <>
            <ReactEChartsCore option={chartOption} style={{ height: 400 }} notMerge />
            
            {/* Returns summary */}
            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-[#1e2d45]">
              <span className="text-xs text-slate-500">区间收益率:</span>
              {Object.entries(compareData).map(([code, info], i) => (
                <div key={code} className="flex items-center gap-2 text-sm">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-slate-400">{info.name}</span>
                  <span className={`font-mono font-medium ${info.total_return >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {info.total_return >= 0 ? '+' : ''}{info.total_return}%
                  </span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="h-[400px] flex flex-col items-center justify-center text-slate-500">
            <GitCompare size={48} className="mb-4 opacity-20" />
            <p>选择至少2只股票开始对比</p>
            <p className="text-sm text-slate-600 mt-1">走势将归一化到同一起点(100)</p>
          </div>
        )}
      </div>
    </div>
  );
}
