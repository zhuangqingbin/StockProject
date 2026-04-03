import React, { useState, useEffect } from 'react';
import ReactEChartsCore from 'echarts-for-react';
import { FlaskConical, Play, RefreshCcw, TrendingUp, TrendingDown, Target, AlertTriangle } from 'lucide-react';
import { stockApi, strategyApi } from '../utils/api';
import dayjs from 'dayjs';

function StatCard({ label, value, suffix = '', icon: Icon, color = 'blue', positive }) {
  const colorClasses = {
    blue: 'text-blue-400 bg-blue-500/10',
    green: 'text-green-400 bg-green-500/10',
    red: 'text-red-400 bg-red-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
  };

  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-500">{label}</span>
        {Icon && <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${colorClasses[color]}`}><Icon size={14} /></div>}
      </div>
      <p className={`text-xl font-bold font-mono ${positive === true ? 'text-red-400' : positive === false ? 'text-green-400' : 'text-slate-200'}`}>
        {value}{suffix}
      </p>
    </div>
  );
}


export default function Backtest() {
  const [strategies, setStrategies] = useState([]);
  const [form, setForm] = useState({
    ts_code: '',
    stock_name: '',
    start_date: dayjs().subtract(2, 'year').format('YYYYMMDD'),
    end_date: dayjs().format('YYYYMMDD'),
    strategy: 'dual_ma',
    params: {},
    initial_capital: 1000000,
  });
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    strategyApi.list().then(setStrategies).catch(() => {
      // Fallback strategies
      setStrategies([
        { key: 'dual_ma', name: '双均线策略', description: '短期均线上穿长期均线买入，下穿卖出', params: { short_period: { label: '短期均线', default: 5, min: 2, max: 60 }, long_period: { label: '长期均线', default: 20, min: 5, max: 250 } } },
        { key: 'macd', name: 'MACD策略', description: 'MACD金叉买入，死叉卖出', params: { fast_period: { label: '快线周期', default: 12, min: 5, max: 30 }, slow_period: { label: '慢线周期', default: 26, min: 10, max: 60 }, signal_period: { label: '信号线周期', default: 9, min: 5, max: 20 } } },
        { key: 'bollinger', name: '布林带策略', description: '价格触及下轨买入，触及上轨卖出', params: { period: { label: '周期', default: 20, min: 10, max: 60 }, std_dev: { label: '标准差倍数', default: 2, min: 1, max: 3 } } },
        { key: 'turtle', name: '海龟交易法', description: '突破N日高点买入，跌破M日低点卖出', params: { entry_period: { label: '入场周期', default: 20, min: 10, max: 60 }, exit_period: { label: '出场周期', default: 10, min: 5, max: 30 } } },
        { key: 'rsi', name: 'RSI策略', description: 'RSI超卖买入，超买卖出', params: { period: { label: 'RSI周期', default: 14, min: 5, max: 30 }, overbought: { label: '超买线', default: 70, min: 60, max: 90 }, oversold: { label: '超卖线', default: 30, min: 10, max: 40 } } },
      ]);
    });
  }, []);

  const currentStrategy = strategies.find(s => s.key === form.strategy);

  useEffect(() => {
    if (currentStrategy?.params) {
      const defaults = {};
      for (const [k, v] of Object.entries(currentStrategy.params)) {
        defaults[k] = v.default;
      }
      setForm(prev => ({ ...prev, params: defaults }));
    }
  }, [form.strategy, strategies]);

  const handleStockSearch = async (text) => {
    setSearchText(text);
    if (text.length < 1) { setSearchResults([]); return; }
    try {
      const results = await stockApi.search(text);
      setSearchResults(results || []);
    } catch { setSearchResults([]); }
  };

  const runBacktest = async () => {
    if (!form.ts_code) { setError('请先选择股票'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await strategyApi.backtest({
        ts_code: form.ts_code,
        start_date: form.start_date,
        end_date: form.end_date,
        strategy: form.strategy,
        params: form.params,
        initial_capital: form.initial_capital,
      });
      setResult(res);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || '回测失败');
    }
    setLoading(false);
  };

  const equityChartOption = result ? {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111827ee',
      borderColor: '#1e2d45',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
    },
    legend: { data: ['策略净值', '基准(持有不动)'], textStyle: { color: '#94a3b8', fontSize: 11 }, top: 10 },
    grid: { left: 60, right: 30, top: 50, bottom: 30 },
    xAxis: {
      type: 'category',
      data: result.equity_curve.map(e => e.date),
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      axisLine: { lineStyle: { color: '#1e2d45' } },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: '#94a3b8', fontSize: 10, formatter: v => (v / 10000).toFixed(0) + '万' },
      splitLine: { lineStyle: { color: '#1e2d4520' } },
    },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: result.equity_curve.map(e => e.equity),
        lineStyle: { width: 2, color: '#3b82f6' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#3b82f630' }, { offset: 1, color: '#3b82f605' }] } },
        symbol: 'none',
        smooth: true,
      },
      {
        name: '基准(持有不动)',
        type: 'line',
        data: (() => {
          const curve = result.equity_curve;
          if (!curve.length) return [];
          const firstPrice = curve[0].benchmark_close;
          const initCap = result.initial_capital;
          return curve.map(e => (e.benchmark_close / firstPrice) * initCap);
        })(),
        lineStyle: { width: 1, color: '#94a3b850', type: 'dashed' },
        symbol: 'none',
        smooth: true,
      },
    ],
  } : {};

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <FlaskConical size={24} className="text-cyan-400" />
        <div>
          <h2 className="text-2xl font-bold">策略回测</h2>
          <p className="text-sm text-slate-500">选择策略 · 配置参数 · 查看回测报告</p>
        </div>
      </div>

      <div className="grid grid-cols-[340px_1fr] gap-6">
        {/* Left: Config Panel */}
        <div className="space-y-4">
          {/* Stock Selection */}
          <div className="glass-card p-4">
            <label className="text-xs text-slate-500 mb-2 block">选择股票</label>
            <div className="relative">
              <input
                className="w-full text-sm"
                placeholder="搜索代码或名称..."
                value={form.stock_name || searchText}
                onChange={e => { handleStockSearch(e.target.value); setForm(f => ({ ...f, stock_name: '', ts_code: '' })); }}
              />
              {searchResults.length > 0 && !form.ts_code && (
                <div className="absolute top-full left-0 mt-1 w-full bg-[#111827] border border-[#1e2d45] rounded-lg shadow-2xl z-50 max-h-[200px] overflow-auto">
                  {searchResults.map(s => (
                    <div
                      key={s.ts_code}
                      className="px-3 py-2 hover:bg-blue-500/10 cursor-pointer flex justify-between text-sm"
                      onClick={() => { setForm(f => ({ ...f, ts_code: s.ts_code, stock_name: `${s.name} ${s.ts_code}` })); setSearchResults([]); }}
                    >
                      <span>{s.name}</span>
                      <span className="text-xs text-slate-500 font-mono">{s.ts_code}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Date Range */}
          <div className="glass-card p-4">
            <label className="text-xs text-slate-500 mb-2 block">回测区间</label>
            <div className="grid grid-cols-2 gap-2">
              <input type="text" className="text-sm" placeholder="开始日期" value={form.start_date}
                onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} />
              <input type="text" className="text-sm" placeholder="结束日期" value={form.end_date}
                onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} />
            </div>
            <div className="flex gap-2 mt-2">
              {[{ l: '1年', m: 12 }, { l: '2年', m: 24 }, { l: '3年', m: 36 }, { l: '5年', m: 60 }].map(({ l, m }) => (
                <button key={m} className="text-xs px-2 py-1 rounded bg-white/5 text-slate-400 hover:text-white transition-colors"
                  onClick={() => setForm(f => ({ ...f, start_date: dayjs().subtract(m, 'month').format('YYYYMMDD') }))}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy Selection */}
          <div className="glass-card p-4">
            <label className="text-xs text-slate-500 mb-2 block">选择策略</label>
            <div className="space-y-1.5">
              {strategies.map(s => (
                <div
                  key={s.key}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    form.strategy === s.key ? 'bg-blue-500/15 border border-blue-500/30' : 'hover:bg-white/5 border border-transparent'
                  }`}
                  onClick={() => setForm(f => ({ ...f, strategy: s.key }))}
                >
                  <p className="text-sm font-medium">{s.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{s.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Strategy Params */}
          {currentStrategy?.params && (
            <div className="glass-card p-4">
              <label className="text-xs text-slate-500 mb-2 block">策略参数</label>
              <div className="space-y-3">
                {Object.entries(currentStrategy.params).map(([key, config]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">{config.label}</span>
                      <span className="text-blue-400 font-mono">{form.params[key] ?? config.default}</span>
                    </div>
                    <input
                      type="range"
                      min={config.min} max={config.max} step={1}
                      value={form.params[key] ?? config.default}
                      onChange={e => setForm(f => ({ ...f, params: { ...f.params, [key]: Number(e.target.value) } }))}
                      className="w-full h-1.5 bg-[#1e2d45] rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Capital */}
          <div className="glass-card p-4">
            <label className="text-xs text-slate-500 mb-2 block">初始资金</label>
            <select className="w-full text-sm" value={form.initial_capital}
              onChange={e => setForm(f => ({ ...f, initial_capital: Number(e.target.value) }))}>
              <option value={100000}>10万</option>
              <option value={500000}>50万</option>
              <option value={1000000}>100万</option>
              <option value={5000000}>500万</option>
            </select>
          </div>

          {/* Run Button */}
          <button
            onClick={runBacktest}
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? (
              <><div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> 回测中...</>
            ) : (
              <><Play size={16} /> 开始回测</>
            )}
          </button>

          {error && <p className="text-xs text-red-400 bg-red-500/10 rounded-lg p-3">{error}</p>}
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div className="space-y-4 animate-in">
              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-3">
                <StatCard label="总收益率" value={`${result.total_return > 0 ? '+' : ''}${result.total_return}`} suffix="%" icon={TrendingUp} color="blue" positive={result.total_return > 0} />
                <StatCard label="年化收益" value={`${result.annual_return > 0 ? '+' : ''}${result.annual_return}`} suffix="%" icon={TrendingUp} color="green" positive={result.annual_return > 0} />
                <StatCard label="夏普比率" value={result.sharpe_ratio} icon={Target} color="purple" />
                <StatCard label="最大回撤" value={`-${result.max_drawdown}`} suffix="%" icon={AlertTriangle} color="red" positive={false} />
              </div>
              <div className="grid grid-cols-4 gap-3">
                <StatCard label="最终资金" value={(result.final_capital / 10000).toFixed(2)} suffix="万" icon={TrendingUp} color="amber" />
                <StatCard label="交易次数" value={result.trade_count} icon={RefreshCcw} color="blue" />
                <StatCard label="胜率" value={result.win_rate} suffix="%" icon={Target} color="green" />
                <StatCard label="盈亏比" value={result.profit_loss_ratio} icon={Target} color="purple" />
              </div>

              {/* Equity Curve */}
              <div className="glass-card p-4">
                <h3 className="text-sm font-medium text-slate-400 mb-3">净值曲线 vs 基准</h3>
                <ReactEChartsCore option={equityChartOption} style={{ height: 350 }} notMerge />
              </div>

              {/* Trade Log */}
              {result.trades && result.trades.length > 0 && (
                <div className="glass-card p-4">
                  <h3 className="text-sm font-medium text-slate-400 mb-3">交易记录（共 {result.trades.length} 笔）</h3>
                  <div className="max-h-[300px] overflow-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-slate-500 border-b border-[#1e2d45]">
                          <th className="text-left py-2">日期</th>
                          <th className="text-left py-2">操作</th>
                          <th className="text-right py-2">价格</th>
                          <th className="text-right py-2">数量</th>
                          <th className="text-right py-2">金额</th>
                          <th className="text-right py-2">手续费</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.trades.map((t, i) => (
                          <tr key={i} className="border-b border-[#1e2d4530] hover:bg-white/5">
                            <td className="py-2 font-mono text-xs">{t.date}</td>
                            <td className="py-2">
                              <span className={`text-xs px-2 py-0.5 rounded ${t.action === 'BUY' ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'}`}>
                                {t.action === 'BUY' ? '买入' : '卖出'}
                              </span>
                            </td>
                            <td className="py-2 text-right font-mono">{t.price.toFixed(2)}</td>
                            <td className="py-2 text-right font-mono">{t.shares}</td>
                            <td className="py-2 text-right font-mono">{(t.amount / 10000).toFixed(2)}万</td>
                            <td className="py-2 text-right font-mono text-slate-500">{t.commission.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-[600px] glass-card flex flex-col items-center justify-center text-slate-500">
              <FlaskConical size={56} className="mb-4 opacity-20" />
              <p className="text-lg">配置策略参数后开始回测</p>
              <p className="text-sm mt-2 text-slate-600">选择股票 → 选择策略 → 调整参数 → 开始回测</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
