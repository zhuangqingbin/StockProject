-- ============================================
-- Stock BI 数据库索引优化脚本
-- 运行此脚本可显著提升查询性能
-- ============================================

-- 1. daily_kline 日K线表索引
CREATE INDEX IF NOT EXISTS idx_dk_trade_date ON daily_kline (trade_date);
CREATE INDEX IF NOT EXISTS idx_dk_date_pct ON daily_kline (trade_date, pct_chg);
CREATE INDEX IF NOT EXISTS idx_dk_date_amount ON daily_kline (trade_date, amount);

-- 2. daily_basic 每日指标索引
CREATE INDEX IF NOT EXISTS idx_db_trade_date ON daily_basic (trade_date);
CREATE INDEX IF NOT EXISTS idx_db_date_pe ON daily_basic (trade_date, pe);
CREATE INDEX IF NOT EXISTS idx_db_date_turnover ON daily_basic (trade_date, turnover_rate);

-- 3. stock_basic 股票基础信息索引
CREATE INDEX IF NOT EXISTS idx_sb_market ON stock_basic (market);
CREATE INDEX IF NOT EXISTS idx_sb_industry ON stock_basic (industry);

-- 4. moneyflow 资金流向索引
CREATE INDEX IF NOT EXISTS idx_mf_trade_date ON moneyflow (trade_date);
CREATE INDEX IF NOT EXISTS idx_mf_date_netmf ON moneyflow (trade_date, net_mf_amount);

-- 5. moneyflow_hsgt 北向资金索引
CREATE INDEX IF NOT EXISTS idx_hsgt_trade_date ON moneyflow_hsgt (trade_date);

-- 6. top_list 龙虎榜索引
CREATE INDEX IF NOT EXISTS idx_tl_trade_date ON top_list (trade_date);
CREATE INDEX IF NOT EXISTS idx_tl_date_netamt ON top_list (trade_date, net_amount);

-- 7. top_inst 龙虎榜机构索引
CREATE INDEX IF NOT EXISTS idx_ti_trade_date ON top_inst (trade_date);
CREATE INDEX IF NOT EXISTS idx_ti_ts_code ON top_inst (ts_code);

-- 8. limit_list 涨跌停索引
CREATE INDEX IF NOT EXISTS idx_ll_trade_date ON limit_list (trade_date);
CREATE INDEX IF NOT EXISTS idx_ll_date_limit ON limit_list (trade_date, `limit`);

-- 9. stk_limit 涨跌停价格索引
CREATE INDEX IF NOT EXISTS idx_sl_trade_date ON stk_limit (trade_date);

-- 10. index_daily 指数日线索引
CREATE INDEX IF NOT EXISTS idx_id_trade_date ON index_daily (trade_date);

-- 11. index_sw_daily 申万行业指数索引
CREATE INDEX IF NOT EXISTS idx_sw_trade_date ON index_sw_daily (trade_date);
CREATE INDEX IF NOT EXISTS idx_sw_date_pct ON index_sw_daily (trade_date, pct_change);

-- 12. index_member 行业成分股索引
CREATE INDEX IF NOT EXISTS idx_im_con_code ON index_member (con_code);

-- 13. hk_daily 港股日线索引 (⚠️ 需单独购买权限1000元/年，如未购买请保持注释)
-- CREATE INDEX IF NOT EXISTS idx_hk_trade_date ON hk_daily (trade_date);

-- 14. margin 融资融券索引
CREATE INDEX IF NOT EXISTS idx_margin_trade_date ON margin (trade_date);

-- 15. income 利润表索引
CREATE INDEX IF NOT EXISTS idx_income_end_date ON income (end_date);
CREATE INDEX IF NOT EXISTS idx_income_ann_date ON income (ann_date);

-- 16. hk_hold 沪深股通持股索引
CREATE INDEX IF NOT EXISTS idx_hkhold_trade_date ON hk_hold (trade_date);
CREATE INDEX IF NOT EXISTS idx_hkhold_ts_code ON hk_hold (ts_code);

-- 17. cyq_perf 筹码及胜率索引
CREATE INDEX IF NOT EXISTS idx_cyq_trade_date ON cyq_perf (trade_date);

-- 18. stk_factor 技术因子索引
CREATE INDEX IF NOT EXISTS idx_factor_trade_date ON stk_factor (trade_date);

-- 19. block_trade 大宗交易索引
CREATE INDEX IF NOT EXISTS idx_block_trade_date ON block_trade (trade_date);

-- 20. dividend 分红送股索引
CREATE INDEX IF NOT EXISTS idx_div_end_date ON dividend (end_date);
CREATE INDEX IF NOT EXISTS idx_div_ex_date ON dividend (ex_date);

-- 21. share_float 限售股解禁索引
CREATE INDEX IF NOT EXISTS idx_float_date ON share_float (float_date);

-- 22. pledge_stat 股权质押索引
CREATE INDEX IF NOT EXISTS idx_pledge_end_date ON pledge_stat (end_date);

-- ============================================
-- 完成
-- ============================================
SELECT 'Indexes created successfully!' as status;
