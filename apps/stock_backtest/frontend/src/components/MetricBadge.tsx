type MetricBadgeProps = {
  label: string;
  value: string;
  tone?: "positive" | "warning" | "neutral";
};

export const MetricBadge = ({ label, value, tone = "neutral" }: MetricBadgeProps) => (
  <div className={`metric-badge metric-badge--${tone}`}>
    <span className="metric-badge__label">{label}</span>
    <strong className="metric-badge__value">{value}</strong>
  </div>
);
