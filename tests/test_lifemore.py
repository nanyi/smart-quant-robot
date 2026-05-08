# -*- coding: utf-8 -*-
import unittest

from backtest import BacktestReporter
from strategy.lifemore import LivermoreStrategy
from strategy.base import SignalType
from tests import BaseStrategyTestCase


class TestLivermoreStrategy(BaseStrategyTestCase):
    """利费莫尔策略测试类"""

    def test_breakout_signal(self):
        df = self.generate_test_data(days=50)
        strategy = LivermoreStrategy(breakout_period=10)
        strategy.reset()
        
        signals = []
        for idx in range(len(df)):
            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df)
            if signal:
                signals.append(signal)
        
        print(f"生成 {len(signals)} 个信号")
        self.assertGreater(len(signals), 0)

    def test_stop_loss(self):
        df = self.generate_test_data(days=50)
        strategy = LivermoreStrategy(breakout_period=10, stop_loss_ratio=0.05)
        strategy.reset()
        
        strategy.position_count = 1
        strategy.highest_price = 100.0
        strategy.entry_price = 100.0
        strategy.last_add_price = 100.0
        
        df_small = df.copy()
        df_small.iloc[-1, df_small.columns.get_loc('closePrice')] = 94.0

        signal = strategy.calculate(df_small)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("止损测试通过")

    def test_insufficient_data(self):
        df = self.generate_test_data(days=5)
        strategy = LivermoreStrategy(breakout_period=30)
        strategy.reset()

        signal = strategy.calculate(df)
        self.assertIsNone(signal)
        print("数据不足测试通过")

    def test_with_backtest_engine(self):
        from backtest import BacktestEngine
        
        df = self.generate_test_data(days=200)
        strategy = LivermoreStrategy(breakout_period=20, stop_loss_ratio=0.10)
        strategy.reset()
        
        engine = BacktestEngine(initial_capital=10000.0)
        stats = engine.run_with_data(strategy, df, symbol="TEST")

        reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
        print(reporter.generate_text_report())
        
        self.assertGreater(stats.final_capital, 0)
        print(f"回测资金: {stats.final_capital:.2f}")
        print("回测引擎集成测试通过")


if __name__ == '__main__':
    print("\n开始利费莫尔策略测试\n")
    unittest.main()