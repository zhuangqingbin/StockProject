const PROFILE_DESCRIPTIONS: Record<string, string> = {
  trade_day_post_close_core: "交易日收盘后的核心行情刷新链路",
  trade_day_post_close_extended: "交易日收盘后的扩展行情与补充数据链路",
  reference_trade_day_post_close: "交易日收盘后的参考数据刷新链路",
  reference_calendar_nightly: "夜间参考数据刷新链路",
  reference_manual_snapshot: "手工触发的参考数据快照链路",
  manual_special: "用于少量专项表的手工任务链路",
  manual_infrastructure: "用于基础设施同步与库内元数据维护的手工链路",
};

export const getProfileDescription = (profile?: string | null) => {
  if (!profile) {
    return "当前表未绑定显式 profile，通常表示手工维护或无需定时触发。";
  }

  return PROFILE_DESCRIPTIONS[profile] ?? "当前 profile 已绑定到调度链路，但暂未补充额外说明。";
};
