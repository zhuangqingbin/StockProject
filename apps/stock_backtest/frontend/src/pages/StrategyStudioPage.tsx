import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Surface } from "../components/Surface";
import { StrategyCodeEditor } from "../components/StrategyCodeEditor";
import { Button, StatusTag } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { demoStrategies, demoTemplates } from "../services/demoData";
import { useStrategyStudioStore } from "../stores/strategyStudioStore";

export const StrategyStudioPage = () => {
  const { data: strategies = [] } = useQuery({
    queryKey: ["strategies"],
    queryFn: stockBacktestClient.getStrategies,
    initialData: demoStrategies,
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["templates"],
    queryFn: stockBacktestClient.getTemplates,
    initialData: demoTemplates,
  });
  const { activeStrategyId, editorMode, setActiveStrategyId, setEditorMode } = useStrategyStudioStore();

  const activeStrategy = strategies.find((strategy) => strategy.id === activeStrategyId) ?? strategies[0];
  const activeTemplate = templates.find((template) => template.templateId === activeStrategy?.templateId) ?? templates[0];

  return (
    <div className="page-grid page-grid--two">
      <Surface className="strategy-list" eyebrow="Strategy Inventory" title="策略工坊">
        <div className="card-list">
          {strategies.map((strategy) => (
            <button
              key={strategy.id}
              className={`strategy-card${strategy.id === activeStrategy?.id ? " strategy-card--active" : ""}`}
              onClick={() => setActiveStrategyId(strategy.id)}
              type="button"
            >
              <div className="strategy-card__header">
                <strong>{strategy.name}</strong>
                <StatusTag tone={strategy.sourceType === "template" ? "warning" : "accent"}>
                  {strategy.sourceType === "template" ? "模板" : "自定义"}
                </StatusTag>
              </div>
              <p>{strategy.description}</p>
              <div className="strategy-card__meta">
                <span>{strategy.lastRunLabel}</span>
                <span>{(strategy.annualReturn * 100).toFixed(1)}%</span>
              </div>
            </button>
          ))}
        </div>
      </Surface>

      <div className="stack">
        <Surface
          eyebrow="Edit Surface"
          title={activeStrategy?.name ?? "策略编辑"}
          action={
            <div className="segment">
              <Button onClick={() => setEditorMode("template")} variant={editorMode === "template" ? "primary" : "secondary"}>
                模板配置
              </Button>
              <Button onClick={() => setEditorMode("code")} variant={editorMode === "code" ? "primary" : "secondary"}>
                代码编辑
              </Button>
            </div>
          }
        >
          {editorMode === "template" ? (
            <div className="parameter-grid">
              {Object.entries(activeTemplate?.parameters ?? {}).map(([key, value]) => (
                <div className="parameter-card" key={key}>
                  <span>{key}</span>
                  <strong>{String(value.default)}</strong>
                  <small>{value.type}</small>
                </div>
              ))}
            </div>
          ) : (
            <StrategyCodeEditor code={activeStrategy?.code ?? ""} />
          )}
        </Surface>

        <Surface
          eyebrow="Template Library"
          title="模板仓"
          action={
            <Link className="inline-link" to="/runs">
              去发射台
            </Link>
          }
        >
          <div className="template-gallery">
            {templates.map((template) => (
              <div className={`template-card${template.templateId === activeTemplate?.templateId ? " template-card--active" : ""}`} key={template.templateId}>
                <div className="template-card__header">
                  <strong>{template.name}</strong>
                  <span className="feed-pill">{template.templateId}</span>
                </div>
                <p>{template.description}</p>
                <div className="pill-row">
                  {template.requiredFeeds.map((feed) => (
                    <span className="feed-pill" key={feed}>
                      {feed}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Surface>

        <Surface eyebrow="Feed Contract" title="数据入口">
          <div className="pill-row">
            {(activeStrategy?.requiredFeeds ?? []).map((feed) => (
              <span className="feed-pill" key={feed}>
                {feed}
              </span>
            ))}
          </div>
          <p className="muted-copy">
            当前模板会优先走 `daily_kline` 主序列，再把资金流和基础面按交易日做轻量拼接，避免执行时出现多源宽表膨胀。
          </p>
        </Surface>
      </div>
    </div>
  );
};
