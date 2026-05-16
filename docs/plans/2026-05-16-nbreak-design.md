# 精准N破战法 - 设计文档

## 1. 策略概述

**精准N破战法**是基于N字形态的突破交易系统，仅依赖价格行为与成交量验证，遵循「突破即进、破位即走」原则。

**核心特征**：
- 单次交易决策（不补仓、不扛单、不幻想）
- ATR动态风控
- 20日均线过滤趋势方向

## 2. 策略参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ma_period` | 20 | 均线周期 |
| `strong_rise_period` | 10 | 强势拉升段K线数量 |
| `strong_rise_min_count` | 3 | 强势拉升段最小阳线数 |
| `strong_rise_min_gain` | 0.03 | 强势拉升段最小涨幅（3%） |
| `volume_amplify_ratio` | 1.5 | 成交量放大倍数（较前5日均量） |
| `pullback_volume_ratio` | 0.7 | 缩量回踩比例 |
| `breakout_volume_ratio` | 1.2 | 放量突破比例 |
| `breakout_threshold` | 0.01 | 突破确认阈值（1%） |
| `atr_period` | 20 | ATR计算周期 |
| `atr_stop_loss_ratio` | 2.0 | ATR止损倍数 |

## 3. 交易规则

### 3.1 入场条件（必须全部满足）

1. **趋势过滤**：价格在20日均线上方
2. **强势拉升段**：
   - 过去10根K线中至少3根阳线涨幅≥3%
   - 成交量较前5日均量放大50%+
3. **缩量回踩段**：
   - 回调期间成交量持续低于前5日均量30%+
   - 回调低点不跌破20日均线
4. **放量突破段**：
   - 价格突破前高（突破K线收盘价 > 前高 * 1.01）
   - 突破K线成交量≥前5日均量120%

### 3.2 出场条件

| 类型 | 触发条件 |
|------|----------|
| **止损** | 价格 < 入场价 - 2*ATR |
| **止盈** | 价格 > 入场价 * 1.10 |
| **破位** | 价格 < 20日均线 且 成交量放大 |

## 4. 代码结构

```
strategy/nbreak.py         # NBreakStrategy类
backtest/nbreak_backtest.py  # 回测脚本
tests/test_nbreak.py      # 测试类
```

## 5. 实现要点

### 5.1 形态识别
- `detect_n_pattern(df)` - 检测N字形态
- 使用 `closePrice`, `highPrice`, `lowPrice`, `volume` 列名
- 添加MA20列用于均线过滤

### 5.2 信号生成
- `calculate(df)` - 返回 Signal 或 None
- 状态管理：持仓时跟踪止损/止盈/破位

### 5.3 回测集成
- 使用 BacktestEngine
- 使用 4小时K线数据

## 6. 配置集成

在 `config.yaml` 中添加：
```yaml
strategy:
  nbreak:
    ma_period: 20
    strong_rise_period: 10
    strong_rise_min_count: 3
    strong_rise_min_gain: 0.03
    volume_amplify_ratio: 1.5
    pullback_volume_ratio: 0.7
    breakout_volume_ratio: 1.2
    breakout_threshold: 0.01
    atr_period: 20
    atr_stop_loss_ratio: 2.0
```