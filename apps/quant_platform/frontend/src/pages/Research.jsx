import React, { useEffect, useState } from 'react';
import {
  ArrowUpRight,
  BookOpen,
  Layers3,
  LineChart,
  ShieldCheck,
  Sigma,
  Workflow,
} from 'lucide-react';
import { researchApi } from '../utils/api';
import FactorSignalStudio from './research/FactorSignalStudio';

const NOTEBOOK_DESCRIPTIONS = {
  '01_data_exploration': '看主表、缺失率和日频覆盖，先确认数据基座是否可信。',
  '02_single_factor_analysis': '对单因子跑 IC、分层和覆盖率诊断，判断是否值得继续。',
  '03_factor_screening': '批量排行、看 FDR/覆盖率/稳定性，再筛出有效因子。',
  '04_composite_factor': '对比等权、IC 加权、PCA、ML 组合方法和权重分布。',
  '05_strategy_backtest': '把组合因子送进组合回测，检查 NAV、回撤和换手。',
};

const FALLBACK_OVERVIEW = {
  goal: '基于 tushare_database 构建 A 股次日开盘收益预测因子，并将有效因子转成可回测组合策略。',
  target_formula: 'overnight_return = (T+1 open - T close) / T close',
  catalog: {
    factor_module_count: 15,
    analyzer_module_count: 4,
    strategy_module_count: 5,
    notebook_count: 5,
    notebooks: [
      { name: '01_data_exploration.ipynb', stem: '01_data_exploration' },
      { name: '02_single_factor_analysis.ipynb', stem: '02_single_factor_analysis' },
      { name: '03_factor_screening.ipynb', stem: '03_factor_screening' },
      { name: '04_composite_factor.ipynb', stem: '04_composite_factor' },
      { name: '05_strategy_backtest.ipynb', stem: '05_strategy_backtest' },
    ],
  },
  commands: [
    { name: 'research-notebook', description: '启动 Jupyter Lab，浏览研究模板 notebook', command: 'bash apps/quant_platform/scripts/run.sh research-notebook' },
    { name: 'research-single', description: '对单个因子执行 IC 与分层回测', command: 'bash apps/quant_platform/scripts/run.sh research-single --factor pct_chg' },
    { name: 'research-factor', description: '生成多因子排行榜、相关性和研究报告', command: 'bash apps/quant_platform/scripts/run.sh research-factor --panel-csv /path/to/panel.csv --factor pct_chg --factor net_mf_rate' },
    { name: 'research-backtest', description: '对组合因子执行策略回测', command: 'bash apps/quant_platform/scripts/run.sh research-backtest --panel-csv /path/to/panel.csv --factor alpha_1 --factor alpha_2' },
  ],
  sample_splits: [
    { name: '训练集', start_date: '2018-01-01', end_date: '2023-12-31', purpose: '因子挖掘、IC 分析、参数调优' },
    { name: '验证集', start_date: '2024-01-01', end_date: '2025-06-30', purpose: '因子筛选、组合方法选择' },
    { name: '测试集', start_date: '2025-07-01', end_date: '至今', purpose: '样本外最终评估，仅用于最终报告' },
  ],
  outputs: {
    status: 'empty',
    latest_ranking: { available: false, rows: [], overview_html: null },
    split_factor_summary: { available: false, rows: [], overview_html: null },
    qualified_factor_summary: { available: false, rows: [], overview_html: null },
    factor_reports: [],
    strategy_runs: [],
    strategy_comparison: { available: false, rows: [], overview_html: null, sharpe_plot: null },
    artifact_counts: { ic_reports: 0, backtest_results: 0 },
  },
};

const statusLabel = {
  loading: '连接中',
  connected: '已连接',
  fallback: '演示视图',
};

function MetricCard({ icon: Icon, label, value, hint, tone = 'cyan' }) {
  const toneClasses = {
    cyan: 'from-cyan-400/20 to-blue-500/10 text-cyan-300',
    amber: 'from-amber-400/20 to-orange-500/10 text-amber-300',
    emerald: 'from-emerald-400/20 to-teal-500/10 text-emerald-300',
    violet: 'from-violet-400/20 to-fuchsia-500/10 text-violet-300',
  };

  return (
    <div className="glass-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-gradient-to-br ${toneClasses[tone]}`}>
          <Icon size={16} />
        </div>
      </div>
      <p className="text-3xl font-bold tracking-tight">{value}</p>
      <p className="mt-2 text-xs text-slate-500">{hint}</p>
    </div>
  );
}

function LinkChip({ href, label, tone = 'cyan' }) {
  const toneClasses = {
    cyan: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/15',
    amber: 'border-amber-400/20 bg-amber-400/10 text-amber-200 hover:bg-amber-400/15',
    emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-200 hover:bg-emerald-400/15',
    slate: 'border-white/8 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]',
  };

  return (
    <a
      href={href || '#'}
      target="_blank"
      rel="noreferrer"
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1.5 text-xs transition-colors ${href ? toneClasses[tone] : 'pointer-events-none border-white/8 text-slate-600'}`}
    >
      {label}
      <ArrowUpRight size={12} />
    </a>
  );
}

function SectionTitle({ eyebrow, title, hint, action }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">{eyebrow}</p>
        <h3 className="mt-1 text-lg font-semibold">{title}</h3>
        {hint ? <p className="mt-1 text-sm text-slate-500">{hint}</p> : null}
      </div>
      {action}
    </div>
  );
}

function formatNotebookTitle(stem = '') {
  return stem
    .replace(/^\d+_/, '')
    .split('_')
    .filter(Boolean)
    .map((item) => item[0].toUpperCase() + item.slice(1))
    .join(' ');
}

function formatNumber(value, digits = 3) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return '--';
  }
  return numeric.toFixed(digits);
}

function formatPercent(value, digits = 1) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return '--';
  }
  return `${(numeric * 100).toFixed(digits)}%`;
}

function SummaryRow({ label, value, accent = 'text-slate-200' }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-[#08111d] px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className={`mt-1 font-mono text-sm ${accent}`}>{value}</p>
    </div>
  );
}

export default function Research() {
  const [overview, setOverview] = useState(FALLBACK_OVERVIEW);
  const [apiState, setApiState] = useState('loading');
  const [error, setError] = useState('');
  const [activeFactor, setActiveFactor] = useState('');

  useEffect(() => {
    let mounted = true;
    researchApi.overview()
      .then((data) => {
        if (!mounted) {
          return;
        }
        setOverview(data);
        setApiState('connected');
      })
      .catch(() => {
        if (!mounted) {
          return;
        }
        setOverview(FALLBACK_OVERVIEW);
        setApiState('fallback');
        setError('研究 API 暂不可用，当前展示的是本地框架概览。');
      });
    return () => {
      mounted = false;
    };
  }, []);

  const ranking = overview.outputs?.latest_ranking || { rows: [] };
  const splitSummary = overview.outputs?.split_factor_summary || { rows: [] };
  const qualifiedSummary = overview.outputs?.qualified_factor_summary || { rows: [] };
  const factorReports = overview.outputs?.factor_reports || [];
  const strategyRuns = overview.outputs?.strategy_runs || [];
  const strategyComparison = overview.outputs?.strategy_comparison || { rows: [] };
  const notebooks = overview.catalog?.notebooks || [];
  const rankingRows = ranking.rows || [];
  const qualifiedRows = qualifiedSummary.rows || [];
  const strategyRows = strategyComparison.rows || [];

  useEffect(() => {
    if (!factorReports.length) {
      setActiveFactor('');
      return;
    }
    if (!factorReports.some((report) => report.factor_name === activeFactor)) {
      setActiveFactor(factorReports[0].factor_name);
    }
  }, [factorReports, activeFactor]);

  const activeReport = factorReports.find((report) => report.factor_name === activeFactor) || factorReports[0];
  const topQualifiedCount = qualifiedSummary.row_count || qualifiedRows.length || 0;
  const publishedFactorCount = ranking.row_count || rankingRows.length || 0;

  return (
    <div className="mx-auto max-w-[1520px] p-6">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/20 to-blue-500/20">
            <Sigma size={22} className="text-cyan-300" />
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">因子研究 Atlas</h2>
            <p className="mt-1 text-sm text-slate-500">从因子排名到组合回测，把离线研究产物直接拉到平台页面。</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className={`rounded-full border px-3 py-1.5 ${apiState === 'connected' ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : apiState === 'loading' ? 'border-blue-500/30 bg-blue-500/10 text-blue-300' : 'border-amber-500/30 bg-amber-500/10 text-amber-300'}`}>
            {statusLabel[apiState]}
          </span>
          <span className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1.5 text-slate-400">
            输出状态: {overview.outputs?.status === 'ready' ? '已生成报告' : '待生成'}
          </span>
        </div>
      </div>

      <div className="mb-6 grid gap-4 xl:grid-cols-[1.35fr,0.95fr]">
        <section className="glass-card relative overflow-hidden p-6 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.20),transparent_32%),radial-gradient(circle_at_80%_30%,rgba(59,130,246,0.16),transparent_24%),linear-gradient(135deg,rgba(8,16,31,0.96),rgba(17,24,39,0.82))]">
          <div className="absolute right-[-40px] top-[-20px] h-40 w-40 rounded-full border border-cyan-400/10 bg-cyan-400/5 blur-2xl" />
          <div className="relative">
            <div className="mb-4 inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.32em] text-cyan-300/70">
              <Workflow size={13} />
              Research Control Surface
            </div>
            <p className="max-w-3xl leading-7 text-slate-300">{overview.goal}</p>
            <div className="mt-5 inline-flex rounded-2xl border border-cyan-400/20 bg-[#07111f]/80 px-4 py-3 font-mono text-sm text-cyan-100 shadow-[0_0_30px_rgba(34,211,238,0.08)]">
              {overview.target_formula}
            </div>
            <div className="mt-6 flex flex-wrap gap-2">
              <LinkChip href={ranking.overview_html} label="因子排行 HTML" />
              <LinkChip href={qualifiedSummary.overview_html} label="Qualified Factors" tone="emerald" />
              <LinkChip href={strategyComparison.overview_html} label="策略对比 HTML" tone="amber" />
            </div>
            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {(overview.sample_splits || []).map((split) => (
                <div key={split.name} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-sm font-semibold">{split.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{split.start_date} ~ {split.end_date}</p>
                  <p className="mt-3 text-xs leading-5 text-slate-400">{split.purpose}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid gap-4 sm:grid-cols-2">
          <MetricCard icon={Layers3} label="Factor Modules" value={overview.catalog?.factor_module_count || 0} hint="这是构建模块数，不是当前已发布因子数" tone="cyan" />
          <MetricCard icon={Sigma} label="Published Factors" value={publishedFactorCount} hint="当前 research snapshot 里实际可浏览的因子数" tone="violet" />
          <MetricCard icon={ShieldCheck} label="Qualified Factors" value={topQualifiedCount} hint="通过训练/验证门槛的候选因子数" tone="emerald" />
          <MetricCard icon={LineChart} label="Strategy Runs" value={strategyComparison.row_count || strategyRows.length || strategyRuns.length || 0} hint="组合回测和策略对比资产已接入页面" tone="amber" />
          <MetricCard icon={BookOpen} label="Notebook Templates" value={overview.catalog?.notebook_count || 0} hint="5 本研究工作簿已补成可运行模板" tone="cyan" />
        </div>
      </div>

      <div className="grid gap-4 2xl:grid-cols-[1.2fr,0.8fr]">
        <div className="space-y-4">
          <section className="glass-card p-5">
            <SectionTitle
              eyebrow="Ranking Deck"
              title="因子排行榜"
              hint="顶部展示最新的排名样本，直接看 IC IR、覆盖率和滚动稳定性。"
              action={<LinkChip href={ranking.overview_html} label="打开完整排行" />}
            />
            {rankingRows.length > 0 ? (
              <div className="overflow-hidden rounded-2xl border border-white/8">
                <table className="w-full text-sm">
                  <thead className="bg-white/[0.04] text-slate-400">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Factor</th>
                      <th className="px-4 py-3 text-right font-medium">IC IR</th>
                      <th className="px-4 py-3 text-right font-medium">Coverage</th>
                      <th className="px-4 py-3 text-right font-medium">Rolling 1Y</th>
                      <th className="px-4 py-3 text-right font-medium">胜率</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankingRows.slice(0, 8).map((row) => (
                      <tr key={row.factor_name} className="border-t border-white/6">
                        <td className="px-4 py-3 font-mono text-cyan-200">{row.factor_name}</td>
                        <td className="px-4 py-3 text-right font-mono text-blue-300">{formatNumber(row.ic_ir, 3)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatPercent(row.coverage, 1)}</td>
                        <td className="px-4 py-3 text-right font-mono">{formatPercent(row.rolling_1y_valid_ratio, 1)}</td>
                        <td className="px-4 py-3 text-right font-mono text-slate-400">{formatPercent(row.positive_rate, 1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-cyan-400/20 bg-cyan-400/[0.04] p-5">
                <p className="text-sm text-cyan-100">还没有检测到 `factor_ranking.csv`。先运行 `research-factor`，这里会自动联动显示排行和 HTML 总览。</p>
              </div>
            )}
          </section>

          <div className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
            <section className="glass-card p-5">
              <SectionTitle
                eyebrow="Gate"
                title="Qualified Factors"
                hint="训练/验证一致性、覆盖率和滚动稳定性通过后的因子样本。"
                action={<LinkChip href={qualifiedSummary.overview_html} label="查看完整筛选结果" tone="emerald" />}
              />
              {qualifiedRows.length > 0 ? (
                <div className="space-y-3">
                  {qualifiedRows.slice(0, 5).map((row) => (
                    <div key={row.factor_name} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-mono text-sm text-emerald-200">{row.factor_name}</p>
                          <p className="mt-1 text-xs text-slate-500">
                            train ICIR {formatNumber(row.train_ic_ir, 2)} · validation ICIR {formatNumber(row.validation_ic_ir, 2)}
                          </p>
                        </div>
                        <span className={`rounded-full px-2.5 py-1 text-[11px] ${row.passes_research_gate ? 'bg-emerald-400/10 text-emerald-300' : 'bg-white/[0.05] text-slate-500'}`}>
                          {row.passes_research_gate ? 'pass' : 'review'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-sm text-slate-500">
                  `qualified_factor_summary.csv` 生成后，这里会自动显示通过研究门槛的因子。
                </div>
              )}
            </section>

            <section className="glass-card p-5">
              <SectionTitle
                eyebrow="Report Inspector"
                title="单因子详情"
                hint="直接跳转到 detail HTML 或查看 IC / 分层 / 相关性静态资产。"
              />
              {factorReports.length > 0 && activeReport ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {factorReports.slice(0, 6).map((report) => (
                      <button
                        key={report.factor_name}
                        type="button"
                        onClick={() => setActiveFactor(report.factor_name)}
                        className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${report.factor_name === activeReport.factor_name ? 'border-cyan-400/25 bg-cyan-400/12 text-cyan-200' : 'border-white/8 bg-white/[0.03] text-slate-400 hover:text-slate-200'}`}
                      >
                        {report.factor_name}
                      </button>
                    ))}
                  </div>

                  <div className="rounded-[24px] border border-white/8 bg-[linear-gradient(135deg,rgba(10,14,23,0.92),rgba(17,24,39,0.7))] p-5">
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <p className="font-mono text-lg text-cyan-200">{activeReport.factor_name}</p>
                        <p className="mt-1 text-sm text-slate-500">更新时间 {activeReport.updated_at || '--'}</p>
                      </div>
                      <LinkChip href={activeReport.assets?.detail_html} label="打开详情页" />
                    </div>
                    <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                      <SummaryRow label="IC IR" value={formatNumber(activeReport.summary?.ic_ir, 3)} accent="text-blue-300" />
                      <SummaryRow label="胜率" value={formatPercent(activeReport.summary?.positive_rate, 1)} accent="text-cyan-300" />
                      <SummaryRow label="Coverage" value={formatPercent(activeReport.summary?.coverage, 1)} accent="text-emerald-300" />
                      <SummaryRow label="Long Short" value={formatNumber(activeReport.summary?.long_short_mean, 4)} accent="text-amber-300" />
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <LinkChip href={activeReport.assets?.ic_plot} label="IC 图" />
                      <LinkChip href={activeReport.assets?.layered_plot} label="分层图" tone="amber" />
                      <LinkChip href={activeReport.assets?.correlation_heatmap} label="相关性" tone="slate" />
                      <LinkChip href={activeReport.assets?.ic_series_csv} label="IC CSV" tone="emerald" />
                      <LinkChip href={activeReport.assets?.group_returns_csv} label="Group CSV" tone="emerald" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4 text-sm text-slate-500">
                  因子详情报告会从 `research/output/ic_reports/*_detail.html` 自动接入，无需再改前端。
                </div>
              )}
            </section>
          </div>

          <section className="glass-card p-5">
            <SectionTitle
              eyebrow="Strategy Lens"
              title="组合回测与策略对比"
              hint="同时展示策略比较表和单次 backtest 产物，方便把研究结论收口到组合层。"
              action={<LinkChip href={strategyComparison.overview_html} label="打开策略对比" tone="amber" />}
            />
            <div className="grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold">Strategy Comparison</p>
                  <LinkChip href={strategyComparison.sharpe_plot} label="Sharpe 图" tone="amber" />
                </div>
                {strategyRows.length > 0 ? (
                  <div className="space-y-3">
                    {strategyRows.slice(0, 5).map((row, index) => (
                      <div key={`${row.strategy_name}-${index}`} className="rounded-2xl border border-white/8 bg-[#08111d] px-4 py-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-amber-100">{row.strategy_name || row.method || `strategy_${index + 1}`}</p>
                            <p className="mt-1 text-xs text-slate-500">
                              Sharpe {formatNumber(row.sharpe_ratio, 2)} · Annual {formatPercent(row.annual_return, 1)}
                            </p>
                          </div>
                          <p className="font-mono text-sm text-amber-300">{formatNumber(row.final_nav, 2)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">`strategy_comparison.csv` 生成后，这里会显示方法间对比。</p>
                )}
              </div>

              <div className="space-y-3">
                {strategyRuns.length > 0 ? (
                  strategyRuns.slice(0, 3).map((run) => (
                    <div key={run.name} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold">{run.name}</p>
                          <p className="mt-1 text-xs text-slate-500">{run.updated_at || '--'}</p>
                        </div>
                        <LinkChip href={run.asset_url} label="JSON" tone="emerald" />
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <SummaryRow label="Final NAV" value={formatNumber(run.summary?.final_nav, 3)} accent="text-emerald-300" />
                        <SummaryRow label="Annual" value={formatPercent(run.summary?.annual_return, 1)} accent="text-cyan-300" />
                        <SummaryRow label="Sharpe" value={formatNumber(run.summary?.sharpe_ratio, 2)} accent="text-amber-300" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-emerald-400/20 bg-emerald-400/[0.04] p-4 text-sm text-slate-400">
                    组合回测结果会从 `research/output/backtest_results/*.json` 自动读取。
                  </div>
                )}
              </div>
            </div>
          </section>

          <FactorSignalStudio />
        </div>

        <div className="space-y-4">
          <section className="glass-card p-5">
            <SectionTitle eyebrow="Runway" title="执行入口" hint="命令保持原样，页面只负责把结果接起来。" />
            <div className="space-y-3">
              {(overview.commands || []).map((item) => (
                <div key={item.name} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold">{item.name}</p>
                    <a href="/backtest" className="text-xs text-slate-500 hover:text-slate-300">
                      联动回测
                    </a>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{item.description}</p>
                  <code className="mt-3 block break-all rounded-xl bg-[#08111d] px-3 py-2 text-[11px] text-cyan-100">{item.command}</code>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-card p-5">
            <SectionTitle eyebrow="Notebook Route" title="研究工作簿" hint="按从左到右的研究顺序补齐：探索、单因子、筛选、组合、回测。" />
            <div className="space-y-2">
              {notebooks.map((item, index) => (
                <div key={item.name} className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-violet-400/10 text-xs text-violet-300">
                      {index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{formatNotebookTitle(item.stem)}</p>
                      <p className="mt-1 text-xs text-slate-500">{NOTEBOOK_DESCRIPTIONS[item.stem] || item.name}</p>
                      <p className="mt-2 font-mono text-[11px] text-slate-400">{item.name}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="glass-card p-5">
            <SectionTitle eyebrow="Split View" title="样本切分检查" hint="快速看 train/validation/test 报告产物是否已经落地。" />
            <div className="space-y-3">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold">Split Summary</p>
                  <LinkChip href={splitSummary.overview_html} label="HTML" tone="slate" />
                </div>
                <p className="text-xs text-slate-500">
                  {splitSummary.available ? `已生成 ${splitSummary.row_count} 行 split summary，可直接查看 train/validation/test 合并结果。` : '尚未生成 split factor summary。'}
                </p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold">Qualified Summary</p>
                  <LinkChip href={qualifiedSummary.overview_html} label="HTML" tone="emerald" />
                </div>
                <p className="text-xs text-slate-500">
                  {qualifiedSummary.available ? `当前共有 ${topQualifiedCount} 个通过门槛的因子。` : '尚未生成 qualified factor summary。'}
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>

      {error ? <div className="mt-4 text-xs text-amber-300">{error}</div> : null}
    </div>
  );
}
