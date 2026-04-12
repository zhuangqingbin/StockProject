import React, { useEffect, useState } from 'react';
import ReactEChartsCore from 'echarts-for-react';
import dayjs from 'dayjs';
import { Activity, ArrowUpRight, Radar, Sparkles } from 'lucide-react';
import { researchApi, stockApi } from '../../utils/api';

function formatNumber(value, digits = 3) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : '--';
}

function formatPercent(value, digits = 1) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? `${(numeric * 100).toFixed(digits)}%` : '--';
}

function buildPriceOption(payload, stockLabel) {
  const seriesData = payload?.data || [];
  if (!seriesData.length) {
    return {};
  }
  const indicators = payload?.indicators || {};
  const dates = seriesData.map((item) => item.date);
  const closes = seriesData.map((item) => item.close);
  const pctChg = seriesData.map((item) => item.pct_chg || 0);

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: [
      { left: 50, right: 18, top: 28, height: '58%' },
      { left: 50, right: 18, top: '74%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: false, axisLabel: { color: '#94a3b8' }, axisLine: { lineStyle: { color: '#1e293b' } } },
      { type: 'category', data: dates, gridIndex: 1, axisLabel: { color: '#64748b', fontSize: 10 }, axisLine: { lineStyle: { color: '#1e293b' } } },
    ],
    yAxis: [
      { type: 'value', scale: true, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b40' } } },
      { type: 'value', gridIndex: 1, axisLabel: { color: '#64748b', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      {
        name: stockLabel || 'Close',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: closes,
        lineStyle: { color: '#22d3ee', width: 2 },
        areaStyle: { color: 'rgba(34, 211, 238, 0.12)' },
      },
      {
        name: 'MA20',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: indicators.MA20 || [],
        lineStyle: { color: '#f59e0b', width: 1.5 },
      },
      {
        name: 'MA60',
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: indicators.MA60 || [],
        lineStyle: { color: '#a855f7', width: 1.5 },
      },
      {
        name: 'PctChg',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: pctChg.map((value) => ({
          value,
          itemStyle: { color: value >= 0 ? '#34d399aa' : '#fb7185aa' },
        })),
      },
    ],
  };
}

function buildFactorHistoryOption(history, factorName) {
  if (!history?.length) {
    return {};
  }
  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 18, top: 28, bottom: 26 },
    xAxis: {
      type: 'category',
      data: history.map((item) => item.trade_date),
      boundaryGap: false,
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#1e293b' } },
    },
    yAxis: [
      { type: 'value', scale: true, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#1e293b40' } } },
      { type: 'value', min: 0, max: 1, axisLabel: { color: '#64748b', formatter: (value) => `${Math.round(value * 100)}%` } },
    ],
    series: [
      {
        name: factorName,
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: history.map((item) => item.factor_value),
        lineStyle: { color: '#38bdf8', width: 2 },
      },
      {
        name: 'Signal Rank',
        type: 'line',
        smooth: true,
        symbol: 'none',
        yAxisIndex: 1,
        data: history.map((item) => item.signal_rank_pct),
        lineStyle: { color: '#f59e0b', width: 1.5 },
        areaStyle: { color: 'rgba(245, 158, 11, 0.1)' },
      },
    ],
  };
}

export default function FactorSignalStudio() {
  const [factorList, setFactorList] = useState({ available: false, latest_trade_date: null, supports_picks: false, rows: [] });
  const [activeFactor, setActiveFactor] = useState('');
  const [factorDetail, setFactorDetail] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockDetail, setStockDetail] = useState(null);
  const [pricePayload, setPricePayload] = useState(null);
  const [loadingFactors, setLoadingFactors] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingStock, setLoadingStock] = useState(false);

  useEffect(() => {
    let mounted = true;
    researchApi.factors(200, false)
      .then((payload) => {
        if (!mounted) return;
        const nextPayload = payload?.rows?.length ? payload : { ...payload, rows: [] };
        setFactorList(nextPayload);
        if (nextPayload.rows?.length) {
          setActiveFactor(nextPayload.rows[0].factor_name);
        }
      })
      .catch(async () => {
        if (!mounted) return;
        const fallback = await researchApi.factors(200, false).catch(() => ({ available: false, rows: [] }));
        if (!mounted) return;
        setFactorList(fallback);
        if (fallback.rows?.length) {
          setActiveFactor(fallback.rows[0].factor_name);
        }
      })
      .finally(() => {
        if (mounted) {
          setLoadingFactors(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!activeFactor) {
      setFactorDetail(null);
      return;
    }
    let mounted = true;
    setLoadingDetail(true);
    researchApi.factorDetail(activeFactor)
      .then((payload) => {
        if (!mounted) return;
        setFactorDetail(payload);
      })
      .finally(() => {
        if (mounted) {
          setLoadingDetail(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [activeFactor]);

  useEffect(() => {
    const picks = factorDetail?.picks || [];
    if (!picks.length) {
      setSelectedStock(null);
      return;
    }
    if (!selectedStock || !picks.some((item) => item.ts_code === selectedStock.ts_code)) {
      setSelectedStock(picks[0]);
    }
  }, [factorDetail, selectedStock]);

  useEffect(() => {
    if (!activeFactor || !selectedStock?.ts_code) {
      setStockDetail(null);
      setPricePayload(null);
      return;
    }
    let mounted = true;
    const endDate = factorDetail?.latest_trade_date ? dayjs(factorDetail.latest_trade_date) : dayjs();
    const startDate = endDate.subtract(12, 'month');
    setLoadingStock(true);
    Promise.all([
      researchApi.factorStock(activeFactor, selectedStock.ts_code, 160),
      stockApi.daily(selectedStock.ts_code, startDate.format('YYYYMMDD'), endDate.format('YYYYMMDD'), 'MA20,MA60'),
    ])
      .then(([stockFactorPayload, stockPricePayload]) => {
        if (!mounted) return;
        setStockDetail(stockFactorPayload);
        setPricePayload(stockPricePayload);
      })
      .finally(() => {
        if (mounted) {
          setLoadingStock(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [activeFactor, factorDetail?.latest_trade_date, selectedStock?.ts_code]);

  if (loadingFactors) {
    return <section className="glass-card p-5 text-sm text-slate-400">正在加载因子信号快照…</section>;
  }

  if (!factorList.available || !factorList.rows?.length) {
    return (
      <section className="glass-card p-5">
        <div className="rounded-2xl border border-dashed border-cyan-400/20 bg-cyan-400/[0.04] p-5 text-sm text-cyan-100">
          还没有检测到已发布的研究快照。先运行 `bash apps/quant_platform/scripts/run.sh research-publish --from-db --start-date 2018-01-01`。
        </div>
      </section>
    );
  }

  const selectedProfile = stockDetail?.stock_profile || selectedStock || {};

  return (
    <section className="glass-card p-5">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">Signal Studio</p>
          <h3 className="mt-1 text-lg font-semibold">因子推荐股票与走势钻取</h3>
          <p className="mt-1 text-sm text-slate-500">
            最新快照日 {factorList.latest_trade_date || '--'} · 候选因子 {factorList.rows.length} 个 · {factorList.supports_picks ? '已启用推荐股票' : '仅有排行摘要'}
          </p>
        </div>
        {factorDetail?.assets?.detail_html ? (
          <a href={factorDetail.assets.detail_html} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs text-cyan-200">
            打开研究详情
            <ArrowUpRight size={12} />
          </a>
        ) : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {factorList.rows.map((factor) => (
              <button
                key={factor.factor_name}
                type="button"
                onClick={() => setActiveFactor(factor.factor_name)}
                className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${factor.factor_name === activeFactor ? 'border-cyan-400/25 bg-cyan-400/12 text-cyan-200' : 'border-white/8 bg-white/[0.03] text-slate-400 hover:text-slate-200'}`}
              >
                {factor.factor_name}
              </button>
            ))}
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Direction</p><p className="mt-1 text-sm text-cyan-200">{factorDetail?.summary?.direction === 'long_low' ? '低值优先' : '高值优先'}</p></div>
            <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">IC IR</p><p className="mt-1 font-mono text-sm text-blue-300">{formatNumber(factorDetail?.summary?.ic_ir, 3)}</p></div>
            <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Coverage</p><p className="mt-1 font-mono text-sm text-emerald-300">{formatPercent(factorDetail?.summary?.coverage, 1)}</p></div>
            <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Tradable Picks</p><p className="mt-1 font-mono text-sm text-amber-300">{factorDetail?.distribution?.tradable_count || 0}</p></div>
          </div>

          <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Sparkles size={16} className="text-cyan-300" />
              推荐股票
            </div>
            {loadingDetail ? (
              <p className="text-sm text-slate-500">正在刷新因子推荐…</p>
            ) : !factorList.supports_picks ? (
              <p className="text-sm text-slate-500">当前只发布了排行摘要，还没有 `full_factor_panel.csv`。运行 `research-publish --from-db` 后这里会自动出现推荐股票。</p>
            ) : !(factorDetail?.picks || []).length ? (
              <p className="text-sm text-slate-500">这个因子当前没有可交易候选，通常是当天截面缺失或交易约束把样本过滤掉了。</p>
            ) : (
              <div className="space-y-2">
                {(factorDetail?.picks || []).slice(0, 8).map((pick) => (
                  <button
                    key={`${pick.ts_code}-${pick.rank}`}
                    type="button"
                    onClick={() => setSelectedStock(pick)}
                    className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition-colors ${selectedStock?.ts_code === pick.ts_code ? 'border-cyan-400/25 bg-cyan-400/[0.08]' : 'border-white/8 bg-[#08111d] hover:border-white/15'}`}
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-100">{pick.stock_name || pick.ts_code}</p>
                      <p className="mt-1 text-xs text-slate-500">{pick.ts_code} · {pick.industry || '未知行业'} · rank #{pick.rank}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-sm text-cyan-200">{formatNumber(pick.signal_score, 2)}</p>
                      <p className="mt-1 text-xs text-slate-500">置信度 {formatPercent(pick.confidence, 0)}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[24px] border border-white/8 bg-[linear-gradient(135deg,rgba(10,14,23,0.92),rgba(17,24,39,0.7))] p-5">
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-lg font-semibold text-cyan-100">{selectedProfile.stock_name || selectedProfile.ts_code || '选择一只股票'}</p>
                <p className="mt-1 text-sm text-slate-500">{selectedProfile.ts_code || '--'} · {selectedProfile.industry || selectedStock?.industry || '未知行业'}</p>
              </div>
              <div className="rounded-full border border-white/8 bg-white/[0.04] px-3 py-1 text-xs text-slate-300">
                {stockDetail?.latest_metrics?.tradable ? '当前可交易' : '当前需人工复核'}
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">最新因子值</p><p className="mt-1 font-mono text-sm text-cyan-200">{formatNumber(stockDetail?.latest_metrics?.factor_value, 3)}</p></div>
              <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Z-Score</p><p className="mt-1 font-mono text-sm text-blue-300">{formatNumber(stockDetail?.latest_metrics?.factor_zscore, 2)}</p></div>
              <div className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3"><p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Signal Rank</p><p className="mt-1 font-mono text-sm text-amber-300">{formatPercent(stockDetail?.latest_metrics?.signal_rank_pct, 0)}</p></div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Activity size={16} className="text-emerald-300" />
              股票走势
            </div>
            {!selectedStock ? (
              <p className="text-sm text-slate-500">选择一只推荐股票后，这里会显示 1 年价格走势和均线。</p>
            ) : loadingStock ? (
              <p className="text-sm text-slate-500">正在加载走势…</p>
            ) : (
              <ReactEChartsCore option={buildPriceOption(pricePayload, selectedProfile.stock_name)} style={{ height: 260 }} notMerge />
            )}
          </div>

          <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Radar size={16} className="text-amber-300" />
              因子历史
            </div>
            {!selectedStock ? (
              <p className="text-sm text-slate-500">选择股票后，这里会显示该股票在当前因子上的历史数值和信号分位。</p>
            ) : loadingStock ? (
              <p className="text-sm text-slate-500">正在加载因子历史…</p>
            ) : (
              <ReactEChartsCore option={buildFactorHistoryOption(stockDetail?.history || [], activeFactor)} style={{ height: 260 }} notMerge />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
