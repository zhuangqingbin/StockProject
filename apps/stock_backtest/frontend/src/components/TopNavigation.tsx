import { NavLink } from "react-router-dom";

import { appRoutes } from "../lib/routeModules";
import { MetricBadge } from "./MetricBadge";

export const TopNavigation = () => (
  <header className="masthead">
    <div className="masthead__rail">
      <div>
        <p className="masthead__eyebrow">Night Exchange Lab</p>
        <h1 className="masthead__title">Stock Backtest</h1>
        <p className="masthead__body">
          把数据底座、模板策略、回测发射和复盘分析压进同一张量化工作台，而不是停留在几块展示页上。
        </p>
      </div>
      <div className="masthead__signals">
        <MetricBadge label="入口矩阵" value={`${String(appRoutes.length).padStart(2, "0")} Routes`} tone="warning" />
        <MetricBadge label="模板仓" value="09 Models" tone="positive" />
        <MetricBadge label="数据覆盖" value="6 Feeds" />
      </div>
    </div>
    <nav className="top-nav" aria-label="Primary">
      {appRoutes.map((item) => (
        <NavLink
          key={item.path}
          className={({ isActive }) => `top-nav__link${isActive ? " top-nav__link--active" : ""}`}
          onFocus={() => void item.preload()}
          onMouseEnter={() => void item.preload()}
          to={item.path}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  </header>
);
