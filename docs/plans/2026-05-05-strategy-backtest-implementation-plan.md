# 策略模块重构与回测系统实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 重构策略模块支持多策略动态加权合成，创建K线数据持久化，实现回测系统

**Architecture:** 策略基类+组合器模式，数据库K线仓库，回测引擎+报告生成器

**Tech Stack:** Python 3.7+, pandas, sqlite3

---

## Phase 1: 策略模块重构

### Task 1: 创建策略基类 base.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\strategy\base.py`

```python
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum

class SignalType(IntEnum):
    NEUTRAL = 0
    BUY = 1
    SELL = -1

@dataclass
class Signal:
    """交易信号"""
    signal_type: SignalType
    strategy_name: str
    weight: float
    price: float
    time: str
    confidence: float = 1.0

class SignalStrategy(ABC):
    """策略基类"""
    
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
    def calculate(self, df) -> Optional[Signal]:
        """计算交易信号"""
        pass
```

**Step 1: 创建文件并提交**

```bash
git add strategy/base.py
git commit -m "feat(strategy): 添加策略基类SignalStrategy"
```

---

### Task 2: 创建双均线策略 ma.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\strategy\ma.py`

```python
# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import time as time_module

from strategy.base import SignalStrategy, Signal, SignalType

class MAStrategy(SignalStrategy):
    """双均线策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 60):
        self.short_period = short_period
        self.long_period = long_period
    
    @property
    def name(self) -> str:
        return f"MA_{self.short_period}_{self.long_period}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < self.long_period:
            return None
        
        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'])
        df = df.sort_values('openTime', ascending=True)
        
        ma_short = df['closePrice'].rolling(self.short_period).mean()
        ma_long = df['closePrice'].rolling(self.long_period).mean()
        
        s1 = ma_short < ma_long
        s2 = ma_short > ma_long
        
        death_ex = s1 & s2.shift(1)
        golden_ex = ~(s1 | s2.shift(1))
        
        death_dates = df.loc[death_ex].index
        golden_dates = df.loc[golden_ex].index
        
        s1 = pd.Series(data=SignalType.BUY, index=golden_dates)
        s2 = pd.Series(data=SignalType.SELL, index=death_dates)
        
        signals = s1.append(s2).sort_index()
        
        for i in range(len(signals) - 1, -1, -1):
            sig_time = signals.index[i]
            sig_type = signals.iloc[i]
            
            open_time = df.loc[sig_time, 'openTime']
            close_time = df.loc[sig_time, 'closeTime']
            
            if self._is_valid_time(str(open_time), str(close_time)):
                price = float(df.loc[sig_time, 'closePrice'])
                return Signal(
                    signal_type=sig_type,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=price,
                    time=str(open_time),
                    confidence=1.0
                )
        return None
    
    def _is_valid_time(self, openTime: str, closeTime: str) -> bool:
        dt_interval = pd.to_datetime(closeTime) - pd.to_datetime(openTime)
        seconds = dt_interval.seconds
        now = int(round((time_module.time() - seconds) * 1000))
        now_str = time_module.strftime('%Y-%m-%d %H:%M:%S', time_module.localtime(now / 1000))
        return now_str >= openTime and now_str <= closeTime
```

**Step 1: 创建文件并提交**

```bash
git add strategy/ma.py
git commit -m "feat(strategy): 添加双均线策略MAStrategy"
```

---

### Task 3: 创建策略组合器 composite.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\strategy\composite.py`

```python
# -*- coding: utf-8 -*-
from typing import Optional, List

from strategy.base import SignalStrategy, Signal, SignalType

class CompositeStrategy(SignalStrategy):
    """策略组合器 - 动态加权合成"""
    
    def __init__(self, strategies: List[SignalStrategy], weights: List[float]):
        self.strategies = strategies
        self.weights = weights
    
    @property
    def name(self) -> str:
        return "composite"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        signals = []
        for strategy in self.strategies:
            signal = strategy.calculate(df)
            if signal:
                signals.append(signal)
        
        if not signals:
            return None
        
        buy_score = sum(s.weight for s in signals if s.signal_type == SignalType.BUY)
        sell_score = sum(s.weight for s in signals if s.signal_type == SignalType.SELL)
        
        threshold = 0.5
        
        if buy_score > sell_score and buy_score > threshold:
            latest = next(s for s in reversed(signals) if s.signal_type == SignalType.BUY)
            return Signal(
                signal_type=SignalType.BUY,
                strategy_name=self.name,
                weight=buy_score,
                price=latest.price,
                time=latest.time,
                confidence=buy_score
            )
        elif sell_score > buy_score and sell_score > threshold:
            latest = next(s for s in reversed(signals) if s.signal_type == SignalType.SELL)
            return Signal(
                signal_type=SignalType.SELL,
                strategy_name=self.name,
                weight=sell_score,
                price=latest.price,
                time=latest.time,
                confidence=sell_score
            )
        return None
```

**Step 1: 创建文件并提交**

```bash
git add strategy/composite.py
git commit -m "feat(strategy): 添加策略组合器CompositeStrategy"
```

---

### Task 4: 创建策略模块入口 __init__.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\strategy\__init__.py`

```python
# -*- coding: utf-8 -*-
from strategy.base import SignalStrategy, Signal, SignalType
from strategy.ma import MAStrategy
from strategy.composite import CompositeStrategy

__all__ = ['SignalStrategy', 'Signal', 'SignalType', 'MAStrategy', 'CompositeStrategy']
```

**Step 1: 更新文件并提交**

```bash
git add strategy/__init__.py
git commit -m "feat(strategy): 更新策略模块入口"
```

---

## Phase 2: 数据库重构 - K线数据持久化

### Task 5: 创建数据库管理模块

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\db\manager.py`

```python
# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import Optional

class DBManager:
    _instance = None
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
    
    @classmethod
    def get_instance(cls, db_path: str = None):
        if cls._instance is None:
            if db_path is None:
                from runtime_config import config
                db_path = config.get('sqlite.db_path', './data/db/smart_quant_robot.db')
            cls._instance = cls(db_path)
        return cls._instance
    
    def _ensure_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_kline_table(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kline_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    open_time INTEGER NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    close_time INTEGER NOT NULL,
                    turnover REAL DEFAULT 0,
                    trade_count INTEGER DEFAULT 0,
                    buy_volume REAL DEFAULT 0,
                    buy_turnover REAL DEFAULT 0,
                    is_candle_closed INTEGER DEFAULT 1,
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, interval, open_time)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval ON kline_data(symbol, interval)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_kline_open_time ON kline_data(open_time)')
            conn.commit()
        finally:
            conn.close()
```

**Step 1: 创建目录和文件并提交**

```bash
git add db/manager.py db/__init__.py
git commit -m "feat(db): 添加数据库管理器DBManager"
```

---

### Task 6: 创建K线数据仓库 kline_repo.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\db\kline_repo.py`

```python
# -*- coding: utf-8 -*-
from typing import List, Optional
import pandas as pd

from db.manager import DBManager

class KlineRepo:
    def __init__(self, db_path: str = None):
        self.db = DBManager.get_instance(db_path)
    
    def save_klines(self, symbol: str, interval: str, klines: List):
        """保存K线数据"""
        if not klines:
            return
        
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            for k in klines:
                cursor.execute('''
                    INSERT OR REPLACE INTO kline_data 
                    (symbol, interval, open_time, open_price, high_price, low_price, close_price, 
                     volume, close_time, turnover, trade_count, buy_volume, buy_turnover, is_candle_closed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, interval, k[0], float(k[1]), float(k[2]), float(k[3]),
                    float(k[4]), float(k[5]), k[6], float(k[7]) if len(k) > 7 else 0,
                    int(k[8]) if len(k) > 8 else 0, float(k[9]) if len(k) > 9 else 0,
                    float(k[10]) if len(k) > 10 else 0, 1
                ))
            conn.commit()
        finally:
            conn.close()
    
    def get_klines(self, symbol: str, interval: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """获取K线数据"""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT open_time, open_price, high_price, low_price, close_price, 
                       volume, close_time, turnover, trade_count, buy_volume, buy_turnover
                FROM kline_data
                WHERE symbol = ? AND interval = ?
                ORDER BY open_time DESC
                LIMIT ?
            ''', (symbol, interval, limit))
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            data = {
                'openTime': [r['open_time'] for r in rows],
                'openPrice': [r['open_price'] for r in rows],
                'maxPrice': [r['high_price'] for r in rows],
                'minPrice': [r['low_price'] for r in rows],
                'closePrice': [r['close_price'] for r in rows],
                'closeTime': [r['close_time'] for r in rows],
                'openTime2': [r['open_time'] for r in rows]
            }
            return pd.DataFrame(data)
        finally:
            conn.close()
```

**Step 1: 创建文件并提交**

```bash
git add db/kline_repo.py
git commit -m "feat(db): 添加K线数据仓库KlineRepo"
```

---

### Task 7: 更新SQL初始化脚本

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\sql\init_sqlite.sql`

**Step 1: 添加K线数据表**

```sql
-- K线数据表
CREATE TABLE IF NOT EXISTS kline_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    interval VARCHAR(10) NOT NULL,
    open_time INTEGER NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    close_time INTEGER NOT NULL,
    turnover REAL DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    buy_volume REAL DEFAULT 0,
    buy_turnover REAL DEFAULT 0,
    is_candle_closed INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, open_time)
);

CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval ON kline_data(symbol, interval);
CREATE INDEX IF NOT EXISTS idx_kline_open_time ON kline_data(open_time);
```

**Step 2: 提交**

```bash
git add sql/init_sqlite.sql
git commit -m "feat(db): init_sqlite.sql增加kline_data表"
```

---

## Phase 3: 回测模块

### Task 8: 创建回测数据模型 models.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\backtest\models.py`

```python
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class Trade:
    """交易记录"""
    trade_type: str  # BUY / SELL
    price: float
    quantity: float
    time: str
    commission: float = 0

@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float = 0
    annual_return: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    win_rate: float = 0
    profit_loss_ratio: float = 0
    total_trades: int = 0
    buy_signals: List[str] = field(default_factory=list)
    sell_signals: List[str] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
```

**Step 1: 创建文件并提交**

```bash
git add backtest/models.py backtest/__init__.py
git commit -m "feat(backtest): 添加回测数据模型"
```

---

### Task 9: 创建回测引擎 engine.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\backtest\engine.py`

```python
# -*- coding: utf-8 -*-
from typing import List, Optional
import pandas as pd

from strategy.base import SignalType, SignalStrategy
from backtest.models import BacktestResult, Trade

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.capital = initial_capital
        self.position = 0
        self.trades: List[Trade] = []
        self.buy_signals = []
        self.sell_signals = []
    
    def run(self, df: pd.DataFrame, strategy: SignalStrategy) -> BacktestResult:
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.buy_signals = []
        self.sell_signals = []
        
        for i in range(len(df)):
            signal = strategy.calculate(df.iloc[:i+1])
            if signal is None:
                continue
            
            price = float(df.iloc[i]['closePrice'])
            
            if signal.signal_type == SignalType.BUY and self.capital >= price:
                quantity = self.capital / price
                commission = quantity * price * self.commission
                self.capital -= quantity * price + commission
                self.position += quantity
                self.trades.append(Trade('BUY', price, quantity, str(df.iloc[i]['openTime']), commission))
                self.buy_signals.append(str(df.iloc[i]['openTime']))
            
            elif signal.signal_type == SignalType.SELL and self.position > 0:
                commission = self.position * price * self.commission
                self.capital += self.position * price - commission
                self.trades.append(Trade('SELL', price, self.position, str(df.iloc[i]['openTime']), commission))
                self.sell_signals.append(str(df.iloc[i]['openTime']))
                self.position = 0
        
        final_value = self.capital + self.position * float(df.iloc[-1]['closePrice'])
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        wins = sum(1 for i in range(1, len(self.trades), 2) if self.trades[i].price > self.trades[i-1].price)
        total_trades = len(self.trades)
        
        return BacktestResult(
            total_return=total_return,
            annual_return=total_return,
            sharpe_ratio=0,
            max_drawdown=0,
            win_rate=wins / (total_trades / 2) if total_trades > 1 else 0,
            profit_loss_ratio=0,
            total_trades=total_trades,
            buy_signals=self.buy_signals,
            sell_signals=self.sell_signals,
            trades=self.trades
        )
```

**Step 1: 创建文件并提交**

```bash
git add backtest/engine.py
git commit -m "feat(backtest): 添加回测引擎BacktestEngine"
```

---

### Task 10: 创建回测报告生成器 reporter.py

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\backtest\reporter.py`

```python
# -*- coding: utf-8 -*-
from backtest.models import BacktestResult

class BacktestReporter:
    def generate(self, result: BacktestResult) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("回测报告")
        lines.append("=" * 50)
        lines.append(f"总收益率: {result.total_return:.2%}")
        lines.append(f"年化收益率: {result.annual_return:.2%}")
        lines.append(f"夏普比率: {result.sharpe_ratio:.2f}")
        lines.append(f"最大回撤: {result.max_drawdown:.2%}")
        lines.append(f"胜率: {result.win_rate:.2%}")
        lines.append(f"总交易次数: {result.total_trades}")
        lines.append("-" * 50)
        lines.append("买入信号:")
        for t in result.buy_signals:
            lines.append(f"  {t}")
        lines.append("-" * 50)
        lines.append("卖出信号:")
        for t in result.sell_signals:
            lines.append(f"  {t}")
        lines.append("=" * 50)
        return "\n".join(lines)
```

**Step 1: 创建文件并提交**

```bash
git add backtest/reporter.py
git commit -m "feat(backtest): 添加回测报告生成器"
```

---

## Phase 4: 配置与集成

### Task 11: 更新配置

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\runtime_config.py`
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\config.yaml`

**runtime_config.py 添加：**
```python
'strategy': {
    'composite': {
        'enabled': True,
        'weights': {'ma': 0.5, 'volatility': 0.3, 'volume': 0.2}
    },
    'ma': {'short_period': 5, 'long_period': 60},
    'volatility': {'period': 20, 'multiplier': 2},
    'volume': {'threshold': 1.5}
},
'backtest': {
    'initial_capital': 10000,
    'commission': 0.001
}
```

**config.yaml 添加：**
```yaml
strategy:
  composite:
    enabled: true
    weights:
      ma: 0.5
  ma:
    short_period: 5
    long_period: 60

backtest:
  initial_capital: 10000
  commission: 0.001
```

**提交**

```bash
git add runtime_config.py config.yaml
git commit -m "feat(config): 添加策略和回测配置"
```

---

### Task 12: 更新 OrderManager 适配新策略

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\app\OrderManager.py`

**Step 1: 修改导入**

```python
from strategy import MAStrategy, CompositeStrategy
from db.kline_repo import KlineRepo
```

**Step 2: 修改 binance_func 使用新策略**

```python
# 使用双均线策略
ma_strategy = MAStrategy(
    short_period=config.get('strategy.ma.short_period', 5),
    long_period=config.get('strategy.ma.long_period', 60)
)
signal = ma_strategy.calculate(kline_df)
```

**提交**

```bash
git add app/OrderManager.py
git commit -m "refactor: OrderManager适配新策略模块"
```

---

## 验证测试

1. 单独策略计算：`MAStrategy().calculate(df)`
2. 组合策略计算：`CompositeStrategy([ma_strategy], [1.0]).calculate(df)`
3. K线数据保存和读取：`KlineRepo().save_klines() / get_klines()`
4. 回测运行：`BacktestEngine().run(df, strategy)`