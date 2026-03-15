import type { DataConsistency } from "../../lib/api/types";
import { AlertBanner } from "../../ui";

interface ConsistencyBannerProps {
  consistency: DataConsistency;
}

export const ConsistencyBanner = ({ consistency }: ConsistencyBannerProps) => {
  if (consistency.consistent || consistency.warnings.length === 0) {
    return null;
  }

  return (
    <AlertBanner
      className="consistency-banner"
      tone="warning"
      title="数据日期不一致"
      description={consistency.warnings.join("；")}
    />
  );
};
