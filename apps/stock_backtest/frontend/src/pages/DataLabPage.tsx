import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Surface } from "../components/Surface";
import { DataTable } from "../components/ui";
import { stockBacktestClient } from "../services/client";
import { demoBenchmarks, demoDataOverview, demoUniverse } from "../services/demoData";
import type { UniverseRecord } from "../services/types";

export const DataLabPage = () => {
  const [keyword, setKeyword] = useState("");
  const [industry, setIndustry] = useState("");

  const { data: dataOverview = demoDataOverview } = useQuery({
    queryKey: ["data-overview"],
    queryFn: stockBacktestClient.getDataOverview,
    initialData: demoDataOverview,
  });
  const { data: benchmarks = demoBenchmarks } = useQuery({
    queryKey: ["benchmarks"],
    queryFn: stockBacktestClient.getBenchmarks,
    initialData: demoBenchmarks,
  });
  const { data: universe = demoUniverse } = useQuery({
    queryKey: ["universe", keyword, industry],
    queryFn: () => stockBacktestClient.searchUniverse({ keyword, industry }),
    initialData: demoUniverse,
  });

  const industries = dataOverview.topIndustries.map((item) => item.industry);

  return (
    <div className="stack">
      <Surface eyebrow="Market Lab" title="数据实验室">
        <div className="control-grid control-grid--summary">
          <div className="control-stat">
            <span>股票池规模</span>
            <strong>{dataOverview.symbolCount}</strong>
          </div>
          <div className="control-stat">
            <span>行业覆盖</span>
            <strong>{dataOverview.industryCount}</strong>
          </div>
          <div className="control-stat">
            <span>基准可用性</span>
            <strong>{dataOverview.benchmarkCount}</strong>
          </div>
        </div>
      </Surface>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Feed Health" title="数据源状态">
          <DataTable<(typeof dataOverview.feedHealth)[number]>
            columns={[
              { key: "label", title: "Feed", dataIndex: "label" },
              { key: "tableName", title: "表", dataIndex: "tableName" },
              { key: "symbolCount", title: "覆盖股票", render: (record) => record.symbolCount.toLocaleString("zh-CN") },
              { key: "recordCount", title: "记录数", render: (record) => record.recordCount.toLocaleString("zh-CN") },
              { key: "latestTradeDate", title: "最近更新", dataIndex: "latestTradeDate" },
            ]}
            data={dataOverview.feedHealth}
            rowKey="feedId"
          />
        </Surface>

        <Surface eyebrow="Benchmark Deck" title="基准指数">
          <div className="card-list">
            {benchmarks.map((benchmark) => (
              <div className="micro-card micro-card--wide" key={benchmark.tsCode}>
                <span>{benchmark.tsCode}</span>
                <strong>{benchmark.name}</strong>
                <p>最新交易日 {benchmark.latestTradeDate ?? "未知"}。</p>
              </div>
            ))}
          </div>
        </Surface>
      </div>

      <div className="page-grid page-grid--two">
        <Surface eyebrow="Industry Mesh" title="行业热区">
          <div className="industry-cloud">
            {dataOverview.topIndustries.map((item) => (
              <button
                className={`industry-chip${industry === item.industry ? " industry-chip--active" : ""}`}
                key={item.industry}
                onClick={() => setIndustry(industry === item.industry ? "" : item.industry)}
                type="button"
              >
                {item.industry} {item.symbolCount}
              </button>
            ))}
          </div>
          <p className="muted-copy">热门行业只做入口，不在前端堆砌复杂 DSL。细筛交给回测发射台和 Notebook。</p>
        </Surface>

        <Surface eyebrow="Universe Search" title="股票检索">
          <div className="control-grid">
            <label className="control-field" htmlFor="universe-keyword">
              <span>关键词</span>
              <input
                className="control-input"
                id="universe-keyword"
                onChange={(event) => setKeyword(event.target.value)}
                placeholder="输入股票代码或名称"
                value={keyword}
              />
            </label>
            <label className="control-field" htmlFor="universe-industry">
              <span>行业过滤</span>
              <select className="control-input" id="universe-industry" onChange={(event) => setIndustry(event.target.value)} value={industry}>
                <option value="">全部行业</option>
                {industries.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <DataTable<UniverseRecord>
            columns={[
              { key: "tsCode", title: "代码", dataIndex: "tsCode" },
              { key: "name", title: "名称", dataIndex: "name" },
              { key: "industry", title: "行业", dataIndex: "industry" },
              { key: "market", title: "板块", dataIndex: "market" },
            ]}
            data={universe}
            rowKey="tsCode"
          />
        </Surface>
      </div>
    </div>
  );
};
