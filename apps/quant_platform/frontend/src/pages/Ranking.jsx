import React, { useState, useEffect } from 'react';
import { Trophy, ArrowUpDown, TrendingUp, TrendingDown, BarChart3, DollarSign } from 'lucide-react';
import { marketApi } from '../utils/api';

const DEMO_STOCKS = {
  gainers: Array.from({ length: 20 }, (_, i) => ({
    ts_code: `00${1000 + i}.SZ`, name: `涨停股${i + 1}`, industry: '科技',
    close: (20 + Math.random() * 80).toFixed(2), pct_chg: (10 - i * 0.4).toFixed(2),
    volume: Math.floor(Math.random() * 500000), amount: Math.floor(Math.random() * 5000000),
  })),
  losers: Array.from({ length: 20 }, (_, i) => ({
    ts_code: `60${1000 + i}.SH`, name: `跌停股${i + 1}`, industry: '地产',
    close: (10 + Math.random() * 30).toFixed(2), pct_chg: (-10 + i * 0.4).toFixed(2),
    volume: Math.floor(Math.random() * 300000), amount: Math.floor(Math.random() * 3000000),
  })),
  volume: Array.from({ length: 20 }, (_, i) => ({
    ts_code: `00${2000 + i}.SZ`, name: `成交王${i + 1}`, industry: '金融',
    close: (15 + Math.random() * 50).toFixed(2), pct_chg: (Math.random() * 6 - 3).toFixed(2),
    volume: Math.floor(5000000 - i * 200000), amount: Math.floor(50000000 - i * 2000000),
  })),
};

const TABS = [
  { key: 'gainers', label: '涨幅榜', icon: TrendingUp, sortBy: 'pct_chg', direction: 'desc', color: 'red' },
  { key: 'losers', label: '跌幅榜', icon: TrendingDown, sortBy: 'pct_chg', direction: 'asc', color: 'green' },
  { key: 'volume', label: '成交额榜', icon: DollarSign, sortBy: 'amount', direction: 'desc', color: 'amber' },
];

export default function Ranking() {
  const [activeTab, setActiveTab] = useState('gainers');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      const result = {};
      try {
        for (const tab of TABS) {
          const res = await marketApi.topStocks(tab.sortBy, tab.direction, 30);
          result[tab.key] = res?.stocks || [];
        }
        setData(result);
      } catch {
        setData(DEMO_STOCKS);
      }
      setLoading(false);
    };
    loadAll();
  }, []);

  const currentTab = TABS.find(t => t.key === activeTab);
  const stocks = data[activeTab] || [];

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Trophy size={24} className="text-amber-400" />
        <div>
          <h2 className="text-2xl font-bold">个股排行</h2>
          <p className="text-sm text-slate-500">实时涨跌幅、成交额排行榜</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mb-6">
        {TABS.map(({ key, label, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === key
                ? `bg-${color}-500/15 text-${color}-400 border border-${color}-500/30`
                : 'text-slate-500 hover:text-slate-300 border border-transparent'
            }`}
            style={activeTab === key ? {
              backgroundColor: color === 'red' ? '#ef444415' : color === 'green' ? '#22c55e15' : '#f59e0b15',
              color: color === 'red' ? '#f87171' : color === 'green' ? '#4ade80' : '#fbbf24',
              borderColor: color === 'red' ? '#ef444430' : color === 'green' ? '#22c55e30' : '#f59e0b30',
            } : {}}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
            加载中...
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-500 bg-[#0d1321]">
                <th className="text-left py-3 px-4 w-12">#</th>
                <th className="text-left py-3 px-4">代码</th>
                <th className="text-left py-3 px-4">名称</th>
                <th className="text-left py-3 px-4">行业</th>
                <th className="text-right py-3 px-4">最新价</th>
                <th className="text-right py-3 px-4">涨跌幅</th>
                <th className="text-right py-3 px-4">成交量</th>
                <th className="text-right py-3 px-4">成交额</th>
                <th className="text-right py-3 px-4 w-[160px]">涨跌条</th>
              </tr>
            </thead>
            <tbody>
              {stocks.map((s, i) => {
                const pct = parseFloat(s.pct_chg) || 0;
                const isUp = pct >= 0;
                const barWidth = Math.min(100, Math.abs(pct) * 10);

                return (
                  <tr key={s.ts_code} className="border-t border-[#1e2d4530] hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-500 font-mono text-xs">{i + 1}</td>
                    <td className="py-3 px-4 font-mono text-xs text-blue-400">{s.ts_code}</td>
                    <td className="py-3 px-4 font-medium">{s.name}</td>
                    <td className="py-3 px-4 text-slate-500 text-xs">{s.industry || '-'}</td>
                    <td className="py-3 px-4 text-right font-mono">{parseFloat(s.close)?.toFixed(2)}</td>
                    <td className={`py-3 px-4 text-right font-mono font-medium ${isUp ? 'text-red-400' : 'text-green-400'}`}>
                      {isUp ? '+' : ''}{pct.toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400 text-xs">
                      {s.volume ? (s.volume / 10000).toFixed(0) + '万' : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400 text-xs">
                      {s.amount ? (s.amount / 100000000).toFixed(2) + '亿' : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1">
                        {!isUp && <div className="h-2 rounded-full" style={{ width: `${barWidth}%`, backgroundColor: '#22c55e', minWidth: 2 }} />}
                        <div className="w-px h-3 bg-slate-600" />
                        {isUp && <div className="h-2 rounded-full" style={{ width: `${barWidth}%`, backgroundColor: '#ef4444', minWidth: 2 }} />}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
