# analysis 目录 README 设计

## 背景

`apps/data_hub/data_pipeline_ts/analysis/` 目录已经存在多类分析脚本与策略目录，例如：

- `bottom_val_strategies`
- `block_trade`
- `chip_distribution`
- `cross_factor`
- `earnings`
- `holder_number`
- `holdertrade`
- `limit_board`
- `margin`
- `money_flow`
- `northbound`
- `share_float`

当前问题不是“没有策略目录”，而是缺少一个总入口文档来解释：

- `analysis/` 目录的定位
- 以后新增策略的目录组织规范
- 顶层脚本与策略目录的边界
- `bottom_val_strategies/bottom_volume_matrix.py` 的用途与运行方式

这导致后续继续往 `analysis/` 扩策略时，缺少统一约定，也不方便快速找到现有脚本的用法。

## 目标与非目标

### 目标

- 新增 `apps/data_hub/data_pipeline_ts/analysis/README.md`
- 在 README 中明确：以后 `analysis` 下每个文件夹代表一个策略大类
- 说明当前目录处于“策略目录 + 顶层历史/通用脚本”并存状态
- 为 `bottom_val_strategies/bottom_volume_matrix.py` 增加清晰的介绍与使用说明
- 让 README 成为 `analysis/` 的统一导航入口

### 非目标

- 不迁移现有目录结构
- 不批量搬运顶层脚本进入新目录
- 不修改 `bottom_volume_matrix.py` 的业务逻辑
- 不为每个子目录都新增 README
- 不补全所有分析脚本的详细文档，只先覆盖总规范和 `bottom_val_strategies`

## 方案对比

### 方案 A：只给 `bottom_val_strategies` 单独写说明

优点：

- 改动最小

缺点：

- 无法建立 `analysis/` 的全局规范
- 不能解决“以后每个文件夹是一个策略大类”的约束表达

### 方案 B：新增总 README，并采用渐进收敛策略

做法：

- 新增 `analysis/README.md`
- 在文档中声明以后新策略优先按“一个策略大类一个文件夹”组织
- 对现有顶层脚本标记为历史/通用分析脚本，后续逐步归档
- 把 `bottom_volume_matrix.py` 作为 README 中的首个详细示例

优点：

- 立刻建立统一目录规范
- 与现有真实结构兼容
- 改动面小，风险低

缺点：

- 短期内仍会存在“新旧并存”

### 方案 C：先做文档，再同步做目录迁移

优点：

- 目录最整齐

缺点：

- 改动面大
- 容易带出导入路径、调用命令、文档链接的连锁修改

### 采用方案

采用 `方案 B：新增总 README，并采用渐进收敛策略`。

## README 结构设计

`analysis/README.md` 建议包含以下部分。

### 1. 目录定位

说明 `analysis/` 是 `data_pipeline_ts` 下的分析与研究脚本目录，主要用于：

- 围绕数据库中的历史行情和侧表数据做研究
- 批量生成信号、分层统计和策略回测摘要
- 为后续策略扩展提供统一入口

### 2. 目录规范

明确以后遵守的约定：

- 每个策略大类一个目录
- 一个目录内可包含：
  - 一个或多个分析脚本
  - `output/` 或 `outputs/` 结果目录
  - 与该策略族直接相关的辅助模块
- 新增策略时，优先在对应策略目录下扩展，不再默认向 `analysis/` 顶层添加新脚本

README 不强行规定目录名必须统一为 `output` 还是 `outputs`，只说明两者都属于结果目录命名约定。

### 3. 当前目录现状

明确当前存在两类内容：

- 已按策略大类组织的目录
- 顶层历史/通用分析脚本

顶层脚本示例：

- `daily_signal_scan.py`
- `factor_importance.py`

文档应说明：

- 这些脚本当前仍然有效
- 它们属于历史或通用分析入口
- 后续若继续沉淀为稳定策略族，再逐步收进独立目录

### 4. 当前已有策略目录索引

README 应列出当前已存在的策略大类目录，至少包含：

- `block_trade/`
- `bottom_val_strategies/`
- `chip_distribution/`
- `cross_factor/`
- `earnings/`
- `holder_number/`
- `holdertrade/`
- `limit_board/`
- `margin/`
- `money_flow/`
- `northbound/`
- `share_float/`

每项只需一行简短说明，重点是可导航，而不是把每个目录展开成完整文档。

### 5. `bottom_val_strategies` 详细说明

这是本次 README 中唯一需要展开写的策略目录。

应包含：

- 目录定位：底部放量、底部反转、底部相关策略研究的承载目录
- 当前脚本：`bottom_volume_matrix.py`
- 主数据源：`stock_stk_factor_pro`
- 当前输出：按时间戳生成的 `csv` 和 `md`
- 当前运行体验：扫描策略组合时带进度条，结束后只打印输出路径和行数

### 6. `bottom_volume_matrix.py` 的介绍

README 需要明确这支脚本的职责：

- 从 `stock_stk_factor_pro` 读取日线及技术指标
- 构造底部定义与放量定义
- 生成唯一 `signal_code`
- 统计每个策略的：
  - 样本数
  - `1d/3d` 胜率
  - `1d/3d` 平均收益
  - `1d/3d` 方差
  - 最新交易日命中该策略的股票集合
- 输出：
  - `mmdd_hhmm.csv`
  - `mmdd_hhmm.md`

### 7. `bottom_volume_matrix.py` 的运行方式

README 中需要提供两种命令。

推荐命令：

```bash
PYTHON_BIN="$(./shared/scripts/resolve_project_python.sh)" && \
"$PYTHON_BIN" -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix --start-date 20240101
```

已处于正确虚拟环境时的简写：

```bash
python -m apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix --start-date 20240101
```

参数说明仅覆盖高频参数：

- `--start-date`
- `--end-date`
- `--min-sample`
- `--top-n`
- `--output-dir`

### 8. 输出说明

README 需要说明：

- `mmdd_hhmm.csv`
  - 策略统计总表
- `mmdd_hhmm.md`
  - `signal_code` 含义说明

不在 README 中展开逐列解释全部 CSV 字段，只给出高层说明即可；字段级细节留在脚本输出和后续专门文档里。

## 文案风格要求

README 的文案应满足：

- 先讲目录规则，再讲实例
- 用中文说明，保留必要的英文路径和命令
- 不写过度抽象的“愿景式”表述
- 直接面向仓库使用者，强调“怎么找、怎么跑、怎么扩”

## 影响范围

本次实现只应改动：

- `apps/data_hub/data_pipeline_ts/analysis/README.md`

如果发现 `bottom_volume_matrix.py` 文件头部注释里已有可复用的一行命令，可以在 README 中吸收其内容，但不要求同步修改脚本。

## 验收标准

- `analysis/README.md` 存在
- README 明确写出“以后每个文件夹是一个策略大类”
- README 对当前“顶层脚本 + 策略目录并存”状态有明确说明
- README 包含 `bottom_val_strategies/bottom_volume_matrix.py` 的用途说明
- README 包含可直接运行的命令示例
- 文档内容与当前仓库真实结构一致，不凭空列出不存在的目录或脚本
