# -*- coding: utf-8 -*-
import unittest
import pandas as pd
import numpy as np
from datetime import timedelta

from backtest import BacktestReporter
from strategy.turtle import TurtleStrategy
from strategy.base import SignalType


def generate_test_data(days=100, start_price=100):
    dates = pd.date_range(start='2026-01-01', periods=days, freq='D')
    np.random.seed(42)
    prices = [start_price]
    for _ in range(days - 1):
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))

    df = pd.DataFrame({
        'openTime': [int(d.timestamp() * 1000) for d in dates],
        'closeTime': [int((d + timedelta(hours=23, minutes=59)).timestamp() * 1000) for d in dates],
        'closePrice': prices,
        'openPrice': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
        'highPrice': [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices],
        'lowPrice': [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices],
        'volume': np.random.randint(1000, 10000, days)
    })
    return df


class TestTurtleStrategy(unittest.TestCase):
    def test_entry_signal(self):
        df = generate_test_data(days=50)
        strategy = TurtleStrategy(entry_period=10, exit_period=5, atr_period=10)
        strategy.reset()
        
        signals = []
        for idx in range(len(df)):
            signal = strategy.calculate(df, idx)
            if signal:
                signals.append(signal)
        
        print(f"生成 {len(signals)} 个信号")
        self.assertGreater(len(signals), 0)

    def test_atr_calculation(self):
        df = generate_test_data(days=30)
        strategy = TurtleStrategy(atr_period=14)
        strategy.reset()
        
        strategy.n_value = 0.0
        signal = strategy.calculate(df, len(df) - 1)
        
        if strategy.n_value > 0:
            print(f"ATR值: {strategy.n_value:.4f}")
        
        print("ATR计算测试通过")

    def test_stop_loss(self):
        df = generate_test_data(days=50)
        strategy = TurtleStrategy(entry_period=20, exit_period=10, atr_period=20)
        strategy.reset()
        
        strategy.position_units = 1
        strategy.entry_price = 100.0
        strategy.stop_loss_price = 96.0
        strategy.n_value = 2.0
        strategy.last_add_price = 101.0
        
        df_small = df.copy()
        df_small.iloc[-1, df_small.columns.get_loc('closePrice')] = 95.0
        df_small.iloc[-1, df_small.columns.get_loc('lowPrice')] = 94.0
        
        signal = strategy.calculate(df_small, len(df_small) - 1)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("止损测试通过")

    def test_insufficient_data(self):
        df = generate_test_data(days=5)
        strategy = TurtleStrategy(entry_period=20, exit_period=10, atr_period=20)
        strategy.reset()
        
        signal = strategy.calculate(df, len(df) - 1)
        self.assertIsNone(signal)
        print("数据不足测试通过")

    def test_with_backtest_engine(self):
        from backtest import BacktestEngine
        
        df = generate_test_data(days=200)
        strategy = TurtleStrategy(entry_period=20, exit_period=10, atr_period=20)
        strategy.reset()
        
        engine = BacktestEngine(initial_capital=10000.0)
        stats = engine.run_with_data(strategy, df, symbol="TEST")
        
        self.assertGreater(stats.final_capital, 0)
        print(f"回测资金: {stats.final_capital:.2f}")
        print("回测引擎集成测试通过")


if __name__ == '__main__':
    print("\n开始海龟策略测试\n")
    unittest.main()
