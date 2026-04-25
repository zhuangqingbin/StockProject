import { Button, Card, Col, Row, Typography } from "antd";

import { getProfileDescription } from "../profileInfo";
import { formatShanghaiDateTime } from "../time";
import type { TableDetail } from "../types";

type TableSummaryProps = {
  detail: TableDetail;
};

const { Text, Title } = Typography;

const TableSummary = ({ detail }: TableSummaryProps) => {
  const profileDescription = getProfileDescription(detail.trigger_profile);
  const latestRun = (detail.recent_runs ?? [])[0] ?? null;
  const cards = [
    { label: "所属分类", value: detail.category },
    { label: "总行数", value: detail.summary.row_count },
    { label: "最早数据日期", value: detail.summary.earliest_data_date ?? "—" },
    { label: "最新数据日期", value: detail.summary.latest_data_date ?? "—" },
    { label: "最近更新时间", value: formatShanghaiDateTime(detail.summary.last_updated) },
    { label: "状态", value: detail.summary.status },
    { label: "关联任务", value: detail.job_name ?? "—" },
    { label: "触发 Profile", value: detail.trigger_profile ?? "—" },
    { label: "最近 Run", value: latestRun?.run_id ?? "—" },
    { label: "最近运行结果", value: latestRun?.result ?? "—" },
  ];

  return (
    <section className="summary-stack">
      <div className="detail-hero detail-hero-spotlight">
        <div className="detail-hero-headline">
          <div>
            <Text className="detail-section-label">表详情</Text>
            <Title level={1}>{detail.table_name}</Title>
            <Text className="detail-description">{detail.description}</Text>
          </div>
          {detail.api_url ? (
            <Button href={detail.api_url} rel="noreferrer" target="_blank">
              查看 API 文档
            </Button>
          ) : null}
        </div>
        <div className="detail-chip-row">
          <span className="detail-chip">分类 · {detail.category}</span>
          <span className={`status-pill status-${detail.summary.status}`}>{detail.summary.status}</span>
          <span className="detail-chip">任务 · {detail.job_name ?? "—"}</span>
        </div>
      </div>
      <Row gutter={[16, 16]}>
        {cards.map((card) => (
          <Col key={card.label} lg={8} md={12} span={24}>
            <Card className="metric-card" variant="borderless">
              <Text className="metric-label">{card.label}</Text>
              <Text className="metric-value-text">{String(card.value)}</Text>
            </Card>
          </Col>
        ))}
      </Row>
      <Card className="profile-callout" variant="borderless">
        <Text className="metric-label">Profile 是什么意思</Text>
        <Title level={4}>触发 Profile</Title>
        <Text className="profile-code">{detail.trigger_profile ?? "—"}</Text>
        <Text className="profile-copy">Profile 是这张表绑定的数据触发节奏与执行场景。</Text>
        <Text className="profile-copy profile-copy-secondary">{profileDescription}</Text>
      </Card>
    </section>
  );
};

export default TableSummary;
