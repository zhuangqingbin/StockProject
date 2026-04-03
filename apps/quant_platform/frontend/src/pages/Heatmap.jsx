import React, { useState, useEffect } from 'react';
import { Grid3X3, ArrowUp, ArrowDown, Flame } from 'lucide-react';
import { marketApi } from '../utils/api';

const DEMO_SECTORS = [
  { industry: '银行', stock_count: 42, avg_pct_chg: 1.85, up_count: 38, down_count: 4, total_amount: 186.5 },
  { industry: '白酒', stock_count: 20, avg_pct_chg: 1.23, up_count: 16, down_count: 4, total_amount: 342.1 },
  { industry: '医药', stock_count: 285, avg_pct_chg: 0.67, up_count: 178, down_count: 107, total_amount: 456.3 },
  { industry: '半导体', stock_count: 120, avg_pct_chg: 2.34, up_count: 105, down_count: 15, total_amount: 892.1 },
  { industry: '新能源', stock_count: 95, avg_pct_chg: -0.45, up_count: 32, down_count: 63, total_amount: 567.2 },
  { industry: '房地产', stock_count: 102, avg_pct_chg: -1.23, up_count: 28, down_count: 74, total_amount: 234.5 },
  { industry: '汽车', stock_count: 85, avg_pct_chg: 0.89, up_count: 62, down_count: 23, total_amount: 345.6 },
  { industry: '软件', stock_count: 198, avg_pct_chg: 1.56, up_count: 145, down_count: 53, total_amount: 678.9 },
  { industry: '食品', stock_count: 76, avg_pct_chg: 0.34, up_count: 48, down_count: 28, total_amount: 123.4 },
  { industry: '钢铁', stock_count: 38, avg_pct_chg: -0.78, up_count: 12, down_count: 26, total_amount: 89.5 },
  { industry: '电力', stock_count: 65, avg_pct_chg: 0.56, up_count: 42, down_count: 23, total_amount: 234.1 },
  { industry: '证券', stock_count: 45, avg_pct_chg: 1.12, up_count: 38, down_count: 7, total_amount: 456.7 },
  { industry: '传媒', stock_count: 88, avg_pct_chg: 2.67, up_count: 78, down_count: 10, total_amount: 345.2 },
  { industry: '化工', stock_count: 156, avg_pct_chg: -0.12, up_count: 72, down_count: 84, total_amount: 234.8 },
  { industry: '建筑', stock_count: 72, avg_pct_chg: 0.23, up_count: 38, down_count: 34, total_amount: 156.3 },
  { industry: '机械', stock_count: 134, avg_pct_chg: 0.78, up_count: 86, down_count: 48, total_amount: 267.4 },
  { industry: '航运', stock_count: 22, avg_pct_chg: -1.56, up_count: 5, down_count: 17, total_amount: 45.6 },
  { industry: '旅游', stock_count: 35, avg_pct_chg: 1.89, up_count: 30, down_count: 5, total_amount: 78.9 },
  { industry: '家电', stock_count: 48, avg_pct_chg: 0.45, up_count: 30, down_count: 18, total_amount: 189.2 },
  { industry: '纺织', stock_count: 42, avg_pct_chg: -0.34, up_count: 18, down_count: 24, total_amount: 56.7 },
];

function getHeatColor(pctChg) {
  if (pctChg >= 3) return { bg: '#dc2626', text: '#fff' };
  if (pctChg >= 2) return { bg: '#ef4444', text: '#fff' };
  if (pctChg >= 1) return { bg: '#f87171', text: '#fff' };
  if (pctChg >= 0.5) return { bg: '#fca5a5', text: '#991b1b' };
  if (pctChg >= 0) return { bg: '#fecaca', text: '#991b1b' };
  if (pctChg >= -0.5) return { bg: '#bbf7d0', text: '#14532d' };
  if (pctChg >= -1) return { bg: '#86efac', text: '#14532d' };
  if (pctChg >= -2) return { bg: '#4ade80', text: '#fff' };
  if (pctChg >= -3) return { bg: '#22c55e', text: '#fff' };
  return { bg: '#16a34a', text: '#fff' };
}

function HeatBlock({ sector, maxAmount }) {
  const colors = getHeatColor(sector.avg_pct_chg);
  const sizeRatio = Math.max(0.6, Math.min(1, (sector.total_amount || 50) / (maxAmount || 500)));
  
  return (
    <div
      className="rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.03] hover:shadow-lg relative overflow-hidden"
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
        minHeight: `${80 + sizeRatio * 40}px`,
      }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="font-bold text-sm">{sector.industry}</p>
          <p className="text-xs mt-0.5 opacity-80">{sector.stock_count}只</p>
        </div>
        <p className="text-lg font-bold font-mono">
          {sector.avg_pct_chg > 0 ? '+' : ''}{sector.avg_pct_chg}%
        </p>
      </div>
      <div className="flex items-center gap-3 mt-2 text-xs opacity-75">
        <span className="flex items-center gap-0.5"><ArrowUp size={10} />{sector.up_count}</span>
        <span className="flex items-center gap-0.5"><ArrowDown size={10} />{sector.down_count}</span>
        {sector.total_amount > 0 && <span>{sector.total_amount}亿</span>}
      </div>
    </div>
  );
}


export default function Heatmap() {
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState('');
  const [sortBy, setSortBy] = useState('avg_pct_chg');

  useEffect(() => {
    marketApi.heatmap()
      .then(data => {
        setSectors(data.sectors || []);
        setDate(data.date || '');
        setLoading(false);
      })
      .catch(() => {
        setSectors(DEMO_SECTORS);
        setDate('演示数据');
        setLoading(false);
      });
  }, []);

  const sorted = [...sectors].sort((a, b) => {
    if (sortBy === 'avg_pct_chg') return b.avg_pct_chg - a.avg_pct_chg;
    if (sortBy === 'total_amount') return b.total_amount - a.total_amount;
    if (sortBy === 'stock_count') return b.stock_count - a.stock_count;
    return 0;
  });

  const maxAmount = Math.max(...sectors.map(s => s.total_amount || 0), 1);

  const upSectors = sectors.filter(s => s.avg_pct_chg > 0).length;
  const downSectors = sectors.filter(s => s.avg_pct_chg < 0).length;
  const avgChg = sectors.length > 0 
    ? (sectors.reduce((sum, s) => sum + s.avg_pct_chg, 0) / sectors.length).toFixed(2) 
    : 0;

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Grid3X3 size={24} className="text-amber-400" />
          <div>
            <h2 className="text-2xl font-bold">板块热力图</h2>
            <p className="text-sm text-slate-500">{date ? `数据日期: ${date}` : '加载中...'}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Summary */}
          <div className="flex items-center gap-3 text-sm">
            <span className="text-red-400 font-medium">{upSectors}个板块上涨</span>
            <span className="text-slate-500">|</span>
            <span className="text-green-400 font-medium">{downSectors}个板块下跌</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">均涨 <span className={`font-mono ${avgChg >= 0 ? 'text-red-400' : 'text-green-400'}`}>{avgChg}%</span></span>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-1 text-xs">
            {[
              { key: 'avg_pct_chg', label: '涨跌幅' },
              { key: 'total_amount', label: '成交额' },
              { key: 'stock_count', label: '股票数' },
            ].map(({ key, label }) => (
              <button
                key={key}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  sortBy === key ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300'
                }`}
                onClick={() => setSortBy(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Color Legend */}
      <div className="flex items-center gap-1 mb-4 text-xs text-slate-500">
        <Flame size={12} />
        <span>涨跌幅颜色:</span>
        <div className="flex items-center gap-0.5 ml-1">
          {[
            { label: '>3%', color: '#dc2626' },
            { label: '2%', color: '#ef4444' },
            { label: '1%', color: '#f87171' },
            { label: '0', color: '#fecaca' },
            { label: '-1%', color: '#86efac' },
            { label: '-2%', color: '#4ade80' },
            { label: '<-3%', color: '#16a34a' },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1">
              <div className="w-5 h-3 rounded-sm" style={{ backgroundColor: color }} />
              <span className="text-[10px]">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Heatmap Grid */}
      {loading ? (
        <div className="grid grid-cols-5 gap-3">
          {Array(20).fill(0).map((_, i) => (
            <div key={i} className="h-[100px] rounded-lg bg-[#111827] animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {sorted.map((sector, i) => (
            <HeatBlock key={sector.industry} sector={sector} maxAmount={maxAmount} />
          ))}
        </div>
      )}

      {/* Top Gainers / Losers Summary */}
      <div className="grid grid-cols-2 gap-4 mt-6">
        <div className="glass-card p-4">
          <h3 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
            <ArrowUp size={14} /> 领涨板块 TOP 5
          </h3>
          <div className="space-y-2">
            {sorted.slice(0, 5).map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-4">{i + 1}</span>
                  <span>{s.industry}</span>
                </div>
                <span className="text-red-400 font-mono">+{s.avg_pct_chg}%</span>
              </div>
            ))}
          </div>
        </div>
        <div className="glass-card p-4">
          <h3 className="text-sm font-medium text-green-400 mb-3 flex items-center gap-2">
            <ArrowDown size={14} /> 领跌板块 TOP 5
          </h3>
          <div className="space-y-2">
            {[...sorted].reverse().slice(0, 5).map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 w-4">{i + 1}</span>
                  <span>{s.industry}</span>
                </div>
                <span className="text-green-400 font-mono">{s.avg_pct_chg}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
