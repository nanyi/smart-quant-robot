# 利费莫尔与海龟交易策略设计方案

## 1. 概述

本文档描述为 Smart Quant Robot 添加利费莫尔交易法则和海龟交易法则的设计方案。

## 2. 利费莫尔交易法则（Livermore Trading System）

### 2.1 核心要素

| 要素 | 参数 | 说明 |
|------|------|------|
| 入场信号 | 突破前高/前低 | 突破历史高低点产生信号 |
| 金字塔加仓 | 5%-10%间隔 | 每次加仓在上次价格的5%-10%处 |
| 移动止损 | 10%回落 | 从最高点回落10%止损 |
| 分批出场 | 3批 | 价格每上涨一定比例卖1/3 |

### 2.2 策略实现

```python
class LivermoreStrategy(SignalStrategy):
    def __init__(
        self,
        breakout_period: int = 30,      # 突破周期
        pyramid_ratio: float = 0.05,     # 金字塔加仓比例
        stop_loss_ratio: float = 0.10,   # 止损比例
        exit_ratio: float = 0.20,        # 分批出场比例
    ):
        self.breakout_period = breakout_period
        self.pyramid_ratio = pyramid_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.exit_ratio = exit_ratio
```

### 2.3 信号逻辑

- **买入**：价格突破 `breakout_period` 周期内的最高价
- **加仓**：价格上涨 `pyramid_ratio` 时加仓
- **止损**：价格从最高点回落 `stop_loss_ratio` 时止损
- **卖出**：价格跌破 `breakout_period` 周期内的最低价，或分批止盈

## 3. 海龟交易法则（Turtle Trading System）

### 3.1 核心要素

| 要素 | 参数 | 说明 |
|------|------|------|
| 入场 | 唐奇安通道 | 突破N日最高买入，跌破N日最低卖出 |
| 加仓 | N值倍数 | 每波动1个ATR加仓1份 |
| 止损 | 2N | 2倍ATR止损 |
| 仓位管理 | 单位 | 1个单位 = 账户风险 / (2N × 价格) |

### 3.2 策略实现

```python
class TurtleStrategy(SignalStrategy):
    def __init__(
        self,
        entry_period: int = 20,        # 入场唐奇安通道周期
        exit_period: int = 10,         # 出场唐奇安通道周期
        atr_period: int = 20,           # ATR计算周期
        risk_ratio: float = 0.02,       # 单笔风险比例
        max_units: int = 4,            # 最大持仓单位
    ):
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.risk_ratio = risk_ratio
        self.max_units = max_units
```

### 3.3 信号逻辑

- **买入**：价格突破 `entry_period` 日最高价
- **加仓**：价格突破上次的 + 0.5N 时加仓1个单位
- **止损**：价格跌破买入价 - 2N 时止损
- **卖出**：价格跌破 `exit_period` 日最低价

## 4. 策略文件结构

```
strategy/
├── lifemore.py      # 利费莫尔策略
├── turtle.py        # 海龟策略
```

## 5. 配置文件

```yaml
strategy:
  lifemore:
    breakout_period: 30
    pyramid_ratio: 0.05
    stop_loss_ratio: 0.10
    exit_ratio: 0.20
  turtle:
    entry_period: 20
    exit_period: 10
    atr_period: 20
    risk_ratio: 0.02
    max_units: 4
```

## 6. 回测入口

```bash
python backtest/lifemore_backtest.py
python backtest/turtle_backtest.py
```

## 7. 测试类

- `tests/test_lifemore.py` - 利费莫尔策略测试
- `tests/test_turtle.py` - 海龟策略测试

## 8. 实现检查点

### 利费莫尔策略
1. 突破信号正确识别历史高低点
2. 金字塔加仓逻辑正确
3. 移动止损正确追踪最高点
4. 分批出场正确执行

### 海龟策略
1. 唐奇安通道正确计算
2. N值（ATR）正确计算
3. 加仓单位正确管理
4. 2N止损正确执行
