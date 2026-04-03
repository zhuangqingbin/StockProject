import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { BarChart3, TrendingUp, FlaskConical, LayoutDashboard, Grid3X3, GitCompare, Trophy, Database } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import StockChart from './pages/StockChart';
import Backtest from './pages/Backtest';
import Heatmap from './pages/Heatmap';
import Compare from './pages/Compare';
import Ranking from './pages/Ranking';

const navSections = [
  {
    title: '概览',
    items: [
      { path: '/', icon: LayoutDashboard, label: '市场总览' },
      { path: '/heatmap', icon: Grid3X3, label: '板块热力图' },
      { path: '/ranking', icon: Trophy, label: '个股排行' },
    ]
  },
  {
    title: '分析',
    items: [
      { path: '/chart', icon: TrendingUp, label: 'K线分析' },
      { path: '/compare', icon: GitCompare, label: '多股对比' },
    ]
  },
  {
    title: '量化',
    items: [
      { path: '/backtest', icon: FlaskConical, label: '策略回测' },
    ]
  },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen">
        {/* Sidebar */}
        <aside className="w-[220px] flex-shrink-0 border-r border-[#1e2d45] bg-[#0d1321] flex flex-col">
          <div className="p-5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
              <BarChart3 size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">QuantViz</h1>
              <p className="text-[10px] text-slate-500 tracking-widest uppercase">量化可视化平台</p>
            </div>
          </div>

          <nav className="flex-1 px-3 mt-2 space-y-4 overflow-auto">
            {navSections.map((section) => (
              <div key={section.title}>
                <p className="text-[10px] text-slate-600 uppercase tracking-widest px-3 mb-1.5">{section.title}</p>
                <div className="space-y-0.5">
                  {section.items.map(({ path, icon: Icon, label }) => (
                    <NavLink
                      key={path}
                      to={path}
                      end={path === '/'}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                          isActive
                            ? 'bg-blue-500/10 text-blue-400 font-medium'
                            : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                        }`
                      }
                    >
                      <Icon size={18} />
                      {label}
                    </NavLink>
                  ))}
                </div>
              </div>
            ))}
          </nav>

          <div className="p-4 m-3 rounded-lg bg-gradient-to-br from-blue-900/30 to-cyan-900/20 border border-blue-800/30">
            <div className="flex items-center gap-2 mb-1">
              <Database size={12} className="text-blue-400" />
              <p className="text-xs text-blue-300/80">Tushare 5000积分</p>
            </div>
            <p className="text-[10px] text-slate-500">数据自动缓存 · 增量更新</p>
            <p className="text-[10px] text-slate-600 mt-1">6个页面 · 5种策略 · 7+指标</p>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chart" element={<StockChart />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/heatmap" element={<Heatmap />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/ranking" element={<Ranking />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
