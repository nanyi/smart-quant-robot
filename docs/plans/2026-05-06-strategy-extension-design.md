# 策略扩展设计方案

## 1. 概述

本文档描述为 Smart Quant Robot 添加多个技术分析策略的设计方案，支持多策略动态加权合成。

## 2. 架构

```
strategy/
├── base.py              # 策略基类（已存在）
├── ma.py                # 双均线策略（已存在）
├── composite.py         # 策略组合器（已存在）
├── volatility.py        # 波动率突破策略（新增）
├── volume.py            # 成交量验证策略（新增）
├── rsi.py               # RSI策略（新增）
├── bollinger.py         # 布林带策略（新增）
└── macd.py              # MACD策略（新增）
```

## 3. 各策略设计

| 策略 | 买入条件 | 卖出条件 | 默认参数 |
|------|----------|----------|----------|
| **波动率突破** | 价格突破上轨（MA+N×STD）| 价格跌破下轨（MA-N×STD）| period=20, std_mult=2 |
| **成交量验证** | 量增价涨（量>均量且价>MA）| 量缩价跌（量<均量且价<MA）| vol_ma=5, price_ma=20 |
| **RSI** | RSI < 30 超卖区域 | RSI > 70 超买区域 | period=14 |
| **布林带** | 价格触及下轨 | 价格触及上轨 | period=20, std_mult=2 |
| **MACD** | DIF上穿DEA（金叉）| DIF下穿DEA（死叉）| fast=12, slow=26, signal=9 |

## 4. 配置示例

```yaml
strategy:
  enabled_strategies: ["ma", "rsi", "bollinger"]
  weights:
    ma: 1.0
    rsi: 0.8
    bollinger: 0.8
  threshold: 0.5
```

## 5. 继承关系

所有新策略继承 `SignalStrategy` 基类，实现：
- `name` 属性：策略名称
- `weight` 属性：策略权重
- `calculate(df)` 方法：计算交易信号

## 6. 信号合成逻辑

`CompositeStrategy` 使用动态加权法：
1. 收集各策略信号
2. 计算买入总分 = Σ(买入信号 × 权重)
3. 计算卖出总分 = Σ(卖出信号 × 权重)
4. 综合得分 > 阈值(0.5) 时产生交易信号
