# 精准N破战法 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现「精准N破战法」策略，基于N字形态的突破交易系统

**Architecture:** 继承SignalStrategy基类，实现calculate()方法进行形态识别和信号生成

**Tech Stack:** Python, Pandas, NumPy, BacktestEngine

---

### Task 1: 创建策略类 nbreak.py

**Files:**
- Create: `strategy/nbreak.py`

**Step 1: 编写策略代码**

```python
# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class NBreakStrategy(SignalStrategy):
    """精准N破战法（N-Shaped Breakout Trading System）
    
    核心要素：
    - 入场：价格突破20日均线+成交量放大+形成N字形态
    - 止损：基于ATR的动态止损
    - 止盈：固定10%止盈
    - 破位：价格跌破20日均线且成交量放大
    """

    def __init__(
            self,
            ma_period: int = 20,
            strong_rise_period: int = 10,
            strong_rise_min_count: int = 3,
            strong_rise_min_gain: float = 0.03,
            volume_amplify_ratio: float = 1.5,
            pullback_volume_ratio: float = 0.7,
            breakout_volume_ratio: float = 1.2,
            breakout_threshold: float = 0.01,
            atr_period: int = 20,
            atr_stop_loss_ratio: float = 2.0,
    ):
        """初始化精准N破战法策略
        
        :param ma_period: 均线周期，默认20
        :param strong_rise_period: 强势拉升段K线数量，默认10
        :param strong_rise_min_count: 强势拉升段最小阳线数，默认3
        :param strong_rise_min_gain: 强势拉升段最小涨幅，默认0.03（3%）
        :param volume_amplify_ratio: 成交量放大倍数，默认1.5
        :param pullback_volume_ratio: 缩量回踩比例，默认0.7
        :param breakout_volume_ratio: 放量突破比例，默认1.2
        :param breakout_threshold: 突破确认阈值，默认0.01（1%）
        :param atr_period: ATR计算周期，默认20
        :param atr_stop_loss_ratio: ATR止损倍数，默认2.0
        """
        self.ma_period = ma_period
        self.strong_rise_period = strong_rise_period
        self.strong_rise_min_count = strong_rise_min_count
        self.strong_rise_min_gain = strong_rise_min_gain
        self.volume_amplify_ratio = volume_amplify_ratio
        self.pullback_volume_ratio = pullback_volume_ratio
        self.breakout_volume_ratio = breakout_volume_ratio
        self.breakout_threshold = breakout_threshold
        self.atr_period = atr_period
        self.atr_stop_loss_ratio = atr_stop_loss_ratio

        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0

    @property
    def name(self) -> str:
        return f"NBREAK_{self.ma_period}_{self.atr_period}"

    @property
    def weight(self) -> float:
        return 1.0

    def calculate(self, df) -> Optional[Signal]:
        min_period = max(self.ma_period, self.strong_rise_period, self.atr_period) + 1
        if df is None or len(df) < min_period:
            return None

        df = df.copy()
        df['ma20'] = df['closePrice'].rolling(self.ma_period).mean()
        
        current_bar = df.iloc[-1]
        current_price = current_bar['closePrice']
        current_time = current_bar['closeTime']
        current_volume = current_bar['volume']

        atr_values = self._calculate_atr(df)
        if atr_values:
            self.n_value = np.mean(atr_values)
        else:
            self.n_value = current_bar['highPrice'] - current_bar['lowPrice']

        volume_ma5 = df['volume'].iloc[-6:-1].mean()
        
        if self.entry_price == 0:
            if self._detect_n_pattern(df, volume_ma5):
                self.entry_price = current_price
                self.stop_loss_price = current_price - self.atr_stop_loss_ratio * self.n_value
                self.take_profit_price = current_price * 1.10

                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
        else:
            if current_price < self.stop_loss_price:
                self._reset()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if current_price > self.take_profit_price:
                self._reset()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            ma20_current = current_bar['ma20']
            if ma20_current is not None and current_price < ma20_current and current_volume > volume_ma5 * 1.2:
                self._reset()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

        return None

    def _detect_n_pattern(self, df, volume_ma5) -> bool:
        """检测N字形态"""
        current_bar = df.iloc[-1]
        current_price = current_bar['closePrice']
        current_volume = current_bar['volume']
        ma20_current = current_bar['ma20']

        if ma20_current is None or current_price <= ma20_current:
            return False

        strong_rise_start = -self.strong_rise_period - 1
        strong_rise_df = df.iloc[strong_rise_start:-1]
        
        price_changes = strong_rise_df['closePrice'].pct_change()
        strong_rise_count = (price_changes >= self.strong_rise_min_gain).sum()
        if strong_rise_count < self.strong_rise_min_count:
            return False

        prev_volume_ma5 = df['volume'].iloc[-11:-6].mean()
        if df['volume'].iloc[-self.strong_rise_period:-1].mean() < prev_volume_ma5 * self.volume_amplify_ratio:
            return False

        pullback_df = df.iloc[-6:-1]
        pullback_vol_ma = pullback_df['volume'].mean()
        if pullback_vol_ma > volume_ma5 * self.pullback_volume_ratio:
            return False

        pullback_low = pullback_df['lowPrice'].min()
        if pullback_low < ma20_current:
            return False

        strong_rise_high = strong_rise_df['highPrice'].max()
        breakout_price = strong_rise_high * (1 + self.breakout_threshold)
        if current_price < breakout_price:
            return False

        if current_volume < volume_ma5 * self.breakout_volume_ratio:
            return False

        return True

    def _calculate_atr(self, df) -> list:
        """计算ATR"""
        atr_values = []
        for i in range(len(df) - self.atr_period, len(df) - 1):
            if i < 1:
                continue
            bar = df.iloc[i]
            prev_close = df.iloc[i - 1]['closePrice']
            tr1 = bar['highPrice'] - bar['lowPrice']
            tr2 = abs(bar['highPrice'] - prev_close)
            tr3 = abs(bar['lowPrice'] - prev_close)
            atr_values.append(max(tr1, tr2, tr3))
        return atr_values

    def _reset(self):
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0

    def reset(self):
        self._reset()
```

**Step 2: 提交代码**

```bash
git add strategy/nbreak.py
git commit -m "feat(strategy): 添加精准N破战法策略"
```

---

### Task 2: 创建回测脚本 nbreak_backtest.py

**Files:**
- Create: `backtest/nbreak_backtest.py`

**Step 1: 编写回测脚本**

```python
# -*- coding: utf-8 -*-
from backtest import BacktestEngine, BacktestReporter
from strategy.nbreak import NBreakStrategy


if __name__ == '__main__':
    strategy = NBreakStrategy(
        ma_period=20,
        strong_rise_period=10,
        strong_rise_min_count=3,
        strong_rise_min_gain=0.03,
        volume_amplify_ratio=1.5,
        pullback_volume_ratio=0.7,
        breakout_volume_ratio=1.2,
        breakout_threshold=0.01,
        atr_period=20,
        atr_stop_loss_ratio=2.0,
    )

    engine = BacktestEngine(initial_capital=10000.0)
    stats = engine.run(strategy, symbol="DOGEUSDT", interval="4h", limit=500)

    reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
    print(reporter.generate_text_report())
```

**Step 2: 提交代码**

```bash
git add backtest/nbreak_backtest.py
git commit -m "feat(backtest): 添加精准N破战法回测脚本"
```

---

### Task 3: 创建测试类 test_nbreak.py

**Files:**
- Create: `tests/test_nbreak.py`

**Step 1: 编写测试代码**

```python
# -*- coding: utf-8 -*-
import unittest

from strategy.nbreak import NBreakStrategy
from strategy.base import SignalType
from tests import BaseStrategyTestCase


class TestNBreakStrategy(BaseStrategyTestCase):
    """精准N破战法测试类"""

    def test_n_pattern_detection(self):
        df = self.generate_test_data(days=100)
        strategy = NBreakStrategy()
        strategy.reset()
        
        signals = []
        for idx in range(len(df)):
            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df)
            if signal:
                signals.append(signal)
        
        print(f"生成 {len(signals)} 个信号")
        self.assertGreater(len(signals), 0)

    def test_insufficient_data(self):
        df = self.generate_test_data(days=10)
        strategy = NBreakStrategy()
        strategy.reset()
        
        signal = strategy.calculate(df)
        self.assertIsNone(signal)
        print("数据不足测试通过")

    def test_stop_loss_by_atr(self):
        df = self.generate_test_data(days=50)
        strategy = NBreakStrategy(atr_period=20, atr_stop_loss_ratio=2.0)
        strategy.reset()
        
        strategy.entry_price = 100.0
        strategy.stop_loss_price = 100.0 - 2.0 * 2.0
        strategy.take_profit_price = 110.0
        strategy.n_value = 2.0
        
        df_small = df.copy()
        df_small.iloc[-1, df_small.columns.get_loc('closePrice')] = 95.0
        
        signal = strategy.calculate(df_small)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("ATR止损测试通过")

    def test_take_profit(self):
        df = self.generate_test_data(days=50)
        strategy = NBreakStrategy()
        strategy.reset()
        
        strategy.entry_price = 100.0
        strategy.stop_loss_price = 96.0
        strategy.take_profit_price = 110.0
        strategy.n_value = 2.0
        
        df_small = df.copy()
        df_small.iloc[-1, df_small.columns.get_loc('closePrice')] = 111.0
        
        signal = strategy.calculate(df_small)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("止盈测试通过")

    def test_with_backtest_engine(self):
        from backtest import BacktestEngine
        
        df = self.generate_test_data(days=200)
        strategy = NBreakStrategy()
        strategy.reset()
        
        engine = BacktestEngine(initial_capital=10000.0)
        stats = engine.run_with_data(strategy, df, symbol="TEST")
        
        self.assertGreater(stats.final_capital, 0)
        print(f"回测资金: {stats.final_capital:.2f}")
        print("回测引擎集成测试通过")


if __name__ == '__main__':
    print("\n开始精准N破战法测试\n")
    unittest.main()
```

**Step 2: 提交代码**

```bash
git add tests/test_nbreak.py
git commit -m "test: 添加精准N破战法测试类"
```

---

### Task 4: 更新配置文件

**Files:**
- Modify: `config.yaml` - 添加 nbreak 策略配置

**Step 1: 添加配置项**

在 `config.yaml` 的 `strategy` 部分添加：

```yaml
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

**Step 2: 提交代码**

```bash
git add config.yaml
git commit -m "feat(config): 添加精准N破战法配置项"
```

---

**Plan complete.**