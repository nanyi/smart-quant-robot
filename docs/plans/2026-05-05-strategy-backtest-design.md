# 策略模块重构与回测系统设计方案

## 1. 背景与目标

1. **策略模块重构**：将 `DoubleAverageLinesStrategy.py` 抽象为可扩展的策略架构，支持多策略动态加权合成
2. **数据库重构**：创建历史K线数据表，实现数据持久化
3. **回测模块**：增加策略回测功能，支持完整回测报告

## 2. 策略模块架构

### 2.1 目录结构

```
strategy/
├── __init__.py
├── base.py              # 策略基类 SignalStrategy
├── ma.py                # 双均线策略 (MA)
├── volatility.py        # 波动率突破策略 (未来扩展)
├── volume.py            # 成交量验证策略 (未来扩展)
└── composite.py         # 策略组合器 CompositeStrategy
```

### 2.2 策略基类接口

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class SignalType(Enum):
    BUY = 1
    SELL = -1
    NEUTRAL = 0

@dataclass
class Signal:
    signal_type: SignalType
    strategy_name: str
    weight: float
    price: float
    time: str
    confidence: float = 1.0  # 信号置信度

class SignalStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    def weight(self) -> float:
        """策略权重"""
        return 1.0
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Optional[Signal]:
        """计算交易信号"""
        pass
```

### 2.3 动态加权合成

```python
class CompositeStrategy:
    def __init__(self, strategies: list, weights: list):
        self.strategies = strategies
        self.weights = weights  # e.g., [0.5, 0.3, 0.2]
    
    def calculate(self, df: pd.DataFrame) -> Optional[Signal]:
        # 获取各策略信号
        signals = []
        for strategy in self.strategies:
            signal = strategy.calculate(df)
            if signal:
                signals.append(signal)
        
        # 动态加权合成
        buy_score = sum(s.weight for s in signals if s.signal_type == SignalType.BUY)
        sell_score = sum(s.weight for s in signals if s.signal_type == SignalType.SELL)
        
        if buy_score > sell_score and buy_score > 0.5:
            return Signal(SignalType.BUY, "composite", buy_score, ...)
        elif sell_score > buy_score and sell_score > 0.5:
            return Signal(SignalType.SELL, "composite", sell_score, ...)
        return None
```

### 2.4 双均线策略实现

```python
class MAStrategy(SignalStrategy):
    def __init__(self, short_period: int = 5, long_period: int = 60):
        self.short_period = short_period
        self.long_period = long_period
    
    @property
    def name(self) -> str:
        return f"MA_{self.short_period}_{self.long_period}"
    
    def calculate(self, df: pd.DataFrame) -> Optional[Signal]:
        # 金叉买入、死叉卖出逻辑
        ...
```

## 3. 数据库重构 - K线数据持久化

### 3.1 K线数据表

```sql
CREATE TABLE IF NOT EXISTS kline_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,          -- 交易对 BTCUSDT
    interval VARCHAR(10) NOT NULL,       -- 周期 15m, 1h, 1d
    open_time INTEGER NOT NULL,           -- 开盘时间戳(毫秒)
    open_price REAL NOT NULL,              -- 开盘价
    high_price REAL NOT NULL,             -- 最高价
    low_price REAL NOT NULL,              -- 最低价
    close_price REAL NOT NULL,            -- 收盘价
    volume REAL NOT NULL,                  -- 成交量
    close_time INTEGER NOT NULL,           -- 收盘时间戳(毫秒)
    turnover REAL DEFAULT 0,              -- 成交额
    trade_count INTEGER DEFAULT 0,        -- 成交笔数
    buy_volume REAL DEFAULT 0,           -- 主动买入成交量
    buy_turnover REAL DEFAULT 0,          -- 主动买入成交额
    is_candle_closed INTEGER DEFAULT 1,  -- K线是否收线(1=已收线)
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, open_time)
);

CREATE INDEX idx_kline_symbol_interval ON kline_data(symbol, interval);
CREATE INDEX idx_kline_open_time ON kline_data(open_time);
```

### 3.2 数据库管理模块

```
db/
├── __init__.py
├── manager.py       # 数据库管理器
└── kline_repo.py   # K线数据仓库
```

## 4. 回测模块

### 4.1 目录结构

```
backtest/
├── __init__.py
├── engine.py       # 回测引擎
├── reporter.py    # 回测报告生成
└── models.py      # 回测数据模型
```

### 4.2 回测数据模型

```python
@dataclass
class BacktestResult:
    total_return: float           # 总收益率
    annual_return: float         # 年化收益率
    sharpe_ratio: float          # 夏普比率
    max_drawdown: float         # 最大回撤
    win_rate: float              # 胜率
    profit_loss_ratio: float     # 平均盈亏比
    total_trades: int            # 总交易次数
    buy_signals: list            # 买入信号列表
    sell_signals: list           # 卖出信号列表
```

### 4.3 回测报告内容

- **收益指标**：总收益率、年化收益率、夏普比率
- **风险指标**：最大回撤、平均回撤
- **交易统计**：总交易次数、胜率、平均盈亏比
- **持仓记录**：买卖点时间、价格、持仓时长
- **月度收益**：按月统计收益

## 5. 配置变更

### 5.1 config.yaml

```yaml
strategy:
  composite:
    enabled: true
    weights:
      ma: 0.5
      volatility: 0.3
      volume: 0.2
  ma:
    short_period: 5
    long_period: 60
  volatility:
    period: 20
    multiplier: 2
  volume:
    threshold: 1.5

backtest:
  initial_capital: 10000
  commission: 0.001
  slippage: 0.0005
```

## 6. 影响范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `strategy/__init__.py` | 新建 | 策略模块入口 |
| `strategy/base.py` | 新建 | 策略基类 |
| `strategy/ma.py` | 新建 | 双均线策略 |
| `strategy/volatility.py` | 新建 | 波动率策略(占位) |
| `strategy/volume.py` | 新建 | 成交量策略(占位) |
| `strategy/composite.py` | 新建 | 策略组合器 |
| `db/__init__.py` | 新建 | 数据库模块入口 |
| `db/manager.py` | 新建 | 数据库管理器 |
| `db/kline_repo.py` | 新建 | K线数据仓库 |
| `backtest/__init__.py` | 新建 | 回测模块入口 |
| `backtest/engine.py` | 新建 | 回测引擎 |
| `backtest/reporter.py` | 新建 | 报告生成器 |
| `backtest/models.py` | 新建 | 数据模型 |
| `sql/init_sqlite.sql` | 修改 | 增加kline_data表 |
| `runtime_config.py` | 修改 | 增加策略和回测配置 |
| `config.yaml` | 修改 | 增加策略和回测配置 |
| `app/OrderManager.py` | 修改 | 适配新策略模块 |

## 7. 信号权重计算

动态加权合成法核心逻辑：

```
综合得分 = Σ(策略i信号 × 策略i权重)

- 综合得分 > 阈值(0.5) → 买入信号
- 综合得分 < -阈值(0.5) → 卖出信号
- 否则 → 无信号
```