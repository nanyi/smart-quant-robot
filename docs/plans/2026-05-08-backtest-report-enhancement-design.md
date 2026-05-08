# 回测报告增强设计方案

## 1. 概述

增强回测报告功能：
1. 账户信息增加"现金"和"持仓市值"展示
2. 盈亏计算使用加权平均持仓成本
3. 持仓记录展示（当前持仓 + 历史持仓）
4. 最终资金包含持仓市值

## 2. 账户资金计算

### 原实现

```
final_capital = current_capital（仅现金）
```

### 新实现

```
final_capital = cash + position_value
              = cash + Σ(持仓数量 × 当前价格)
              = 现金 + 持仓市值
```

## 3. 数据模型

### BacktestPosition

```python
@dataclass
class BacktestPosition:
    symbol: str
    side: PositionSide
    quantity: float              # 持仓数量
    avg_entry_price: float       # 加权平均持仓成本
    current_price: float = 0
    unrealized_pnl: float = 0
    unrealized_pnl_ratio: float = 0
    open_time: datetime = None
```

### PositionRecord

```python
@dataclass
class PositionRecord:
    symbol: str
    side: PositionSide
    quantity: float              # 本次交易数量
    entry_price: float          # 开仓价格
    exit_price: float           # 平仓价格
    pnl: float                  # 盈亏金额
    pnl_ratio: float            # 盈亏比例
    open_time: datetime
    close_time: datetime
    hold_seconds: int           # 持仓秒数
```

### BacktestStats

```python
@dataclass
class BacktestStats:
    initial_capital: float
    final_capital: float
    cash: float = 0             # 现金（新增）
    position_value: float = 0   # 持仓市值（新增）
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0
    total_loss: float = 0
    max_drawdown: float = 0
    max_drawdown_ratio: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    sharpe_ratio: float = 0
    position_records: List[PositionRecord] = field(default_factory=list)
```

## 4. 盈亏计算逻辑

### 开仓时

```python
# 维护持仓成本
total_cost = Σ(quantity × price)
total_qty = Σ(quantity)
avg_entry_price = total_cost / total_qty
```

### 平仓时

```python
# 盈亏 = (卖出价 - 平均持仓成本) × 卖出数量 - 手续费
pnl = (exit_price - avg_entry_price) × close_quantity - commission
pnl_ratio = pnl / (avg_entry_price × close_quantity)
```

### 最终资金计算

```python
realized_pnl = Σ(平仓盈亏)
unrealized_pnl = Σ(当前持仓 × (当前价 - avg_entry_price))
final_capital = initial_capital + realized_pnl + unrealized_pnl
cash = 当前现金余额
position_value = Σ(持仓数量 × 当前价格)
```

## 5. 报告展示

### 文本报告

```
============================================================
回测报告
============================================================

【账户信息】
  初始资金: 10000.00 USDT
  最终资金: 11500.00 USDT
  现金: 9500.00 USDT
  持仓市值: 2000.00 USDT
  总收益: 1500.00 USDT
  收益率: 15.00%

【当前持仓】
  DOGEUSDT | 多头 | 数量: 1000 | 成本: 0.1050 | 当前: 0.1100 | 浮动盈亏: +5.00 (+4.76%)

【持仓记录】
  DOGEUSDT | 开仓: 0.1000 @ 2026-01-01 | 平仓: 0.1050 @ 2026-01-05 | 盈亏: +5.00 (+5.00%)

【交易统计】
  总交易次数: 10
  盈利交易次数: 6
  亏损交易次数: 4
  胜率: 60.00%

【收益统计】
  总盈利: 2000.00 USDT
  总亏损: 500.00 USDT
  盈利因子: 4.00
```

## 6. 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| backtest/models.py | BacktestPosition 增加 avg_entry_price, unrealized_pnl_ratio, open_time；新增 PositionRecord；BacktestStats 增加 cash, position_value, position_records |
| backtest/engine.py | 重写 _calculate_stats() 盈亏计算逻辑；run_with_data() 结束时计算 final_capital 含持仓市值 |
| backtest/reporter.py | generate_text_report() 增加现金、持仓市值、当前持仓、历史持仓展示 |

## 7. 实现检查点

1. BacktestPosition.avg_entry_price 正确计算加权平均成本
2. 开仓时更新 avg_entry_price
3. 平仓时使用 avg_entry_price 计算盈亏
4. final_capital = cash + position_value
5. cash 和 position_value 在 reporter 中正确展示
