import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import { stockApi } from '../utils/api';

function MiniChart({ data, color }) {
  if (!data || data.length === 0) return null;
  const values = data.map(d => d.close);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 120, h = 40;
  const points = values.map((v, i) =>
    `${(i / (values.length - 1)) * w},${h - ((v - min) / range) * h}`
  ).join(' ');

  return (
    <svg width={w} height={h} className="opacity-60">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

function IndexCard({ item, delay }) {
  const isUp = item.pct_chg >= 0;
  const color = isUp ? '#ef4444' : '#22c55e';

  return (
    <div
      className="glass-card p-5 animate-in"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-sm text-slate-400">{item.name}</p>
          <p className="text-2xl font-bold font-mono mt-1" style={{ color }}>
            {item.close?.toFixed(2)}
          </p>
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${isUp ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
          {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {isUp ? '+' : ''}{item.pct_chg?.toFixed(2)}%
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500">
          <span>涨跌 {isUp ? '+' : ''}{item.change?.toFixed(2)}</span>
          <span className="ml-3">成交额 {(item.amount / 10000).toFixed(0)}亿</span>
        </div>
        <MiniChart data={item.history} color={color} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    stockApi.marketOverview()
      .then(data => { setOverview(data); setLoading(false); })
      .catch(err => {
        setError('无法加载市场数据，请确保后端已启动');
        setLoading(false);
      });
  }, []);

  // Demo data for when API isn't available
  const demoData = {
    indices: [
      { code: '000001.SH', name: '上证指数', close: 3267.89, change: 23.45, pct_chg: 0.72, volume: 345600, amount: 45780000, history: Array.from({length: 20}, (_, i) => ({ close: 3200 + Math.random() * 100 })) },
      { code: '399001.SZ', name: '深证成指', close: 10856.34, change: -45.67, pct_chg: -0.42, volume: 456700, amount: 56780000, history: Array.from({length: 20}, (_, i) => ({ close: 10800 + Math.random() * 200 })) },
      { code: '399006.SZ', name: '创业板指', close: 2156.78, change: 12.34, pct_chg: 0.58, volume: 234500, amount: 34560000, history: Array.from({length: 20}, (_, i) => ({ close: 2100 + Math.random() * 100 })) },
      { code: '000688.SH', name: '科创50', close: 987.65, change: -5.43, pct_chg: -0.55, volume: 123400, amount: 12340000, history: Array.from({length: 20}, (_, i) => ({ close: 970 + Math.random() * 30 })) },
    ]
  };

  const data = overview || (error ? demoData : null);

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold">市场总览</h2>
          <p className="text-sm text-slate-500 mt-1">实时指数 · 数据来源 Tushare</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className={`w-2 h-2 rounded-full ${error ? 'bg-yellow-500' : 'bg-green-500 pulse-dot'}`} />
          {error ? '使用演示数据' : '数据已连接'}
        </div>
      </div>

      {/* Index Cards */}
      {loading ? (
        <div className="grid grid-cols-2 gap-4">
          {[1,2,3,4].map(i => (
            <div key={i} className="glass-card p-5 h-[130px] animate-pulse" />
          ))}
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.indices.map((item, i) => (
            <IndexCard key={item.code} item={item} delay={i * 80} />
          ))}
        </div>
      ) : null}

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-3 gap-4">
        <a href="/chart" className="glass-card p-5 hover:border-blue-500/50 transition-all group cursor-pointer">
          <Activity size={20} className="text-blue-400 mb-3 group-hover:scale-110 transition-transform" />
          <h3 className="font-medium text-sm">K线分析</h3>
          <p className="text-xs text-slate-500 mt-1">技术指标 · MA / MACD / KDJ / BOLL</p>
        </a>
        <a href="/backtest" className="glass-card p-5 hover:border-blue-500/50 transition-all group cursor-pointer">
          <BarChart3 size={20} className="text-cyan-400 mb-3 group-hover:scale-110 transition-transform" />
          <h3 className="font-medium text-sm">策略回测</h3>
          <p className="text-xs text-slate-500 mt-1">5种内置策略 · 完整回测报告</p>
        </a>
        <div className="glass-card p-5 opacity-50">
          <TrendingUp size={20} className="text-amber-400 mb-3" />
          <h3 className="font-medium text-sm">实盘监控</h3>
          <p className="text-xs text-slate-500 mt-1">即将上线</p>
        </div>
      </div>

      {/* Platform Stats */}
      <div className="mt-8 glass-card p-6">
        <h3 className="text-sm font-medium text-slate-400 mb-4">平台能力</h3>
        <div className="grid grid-cols-4 gap-6">
          {[
            { label: '覆盖股票', value: '5000+', sub: 'A股全覆盖' },
            { label: '技术指标', value: '7+', sub: 'MA/EMA/MACD/KDJ/RSI/BOLL' },
            { label: '量化策略', value: '5', sub: '双均线/MACD/布林带/海龟/RSI' },
            { label: '数据积分', value: '5000', sub: 'Tushare Pro' },
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <p className="text-2xl font-bold text-blue-400 font-mono">{stat.value}</p>
              <p className="text-sm text-slate-300 mt-1">{stat.label}</p>
              <p className="text-xs text-slate-500">{stat.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
