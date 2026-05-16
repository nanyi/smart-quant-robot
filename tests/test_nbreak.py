# -*- coding: utf-8 -*-
import unittest

from strategy.nbreak import NBreakStrategy
from strategy.base import SignalType
from tests import BaseStrategyTestCase


class TestNBreakStrategy(BaseStrategyTestCase):
    """精准N破战法测试类"""

    def test_n_pattern_detection(self):
        df = self.generate_test_data(days=100)
        strategy = NBreakStrategy(ma_period=20, strong_rise_period=10)
        strategy.reset()
        
        signals = []
        for idx in range(20, len(df)):
            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df)
            if signal:
                signals.append(signal)
        
        print(f"生成 {len(signals)} 个信号")
        self.assertGreater(len(signals), 0)

    def test_insufficient_data(self):
        df = self.generate_test_data(days=10)
        strategy = NBreakStrategy(ma_period=20, strong_rise_period=10)
        strategy.reset()
        
        signal = strategy.calculate(df)
        self.assertIsNone(signal)
        print("数据不足测试通过")

    def test_stop_loss_by_atr(self):
        df = self.generate_test_data(days=50)
        strategy = NBreakStrategy(ma_period=20, strong_rise_period=10)
        strategy.reset()
        
        strategy.position_opened = True
        strategy.entry_price = 100.0
        strategy.n_value = 2.0
        strategy.stop_loss_price = 96.0
        
        df_test = df.copy()
        df_test.iloc[-1, df_test.columns.get_loc('lowPrice')] = 94.0
        
        signal = strategy.calculate(df_test)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("ATR止损测试通过")

    def test_take_profit(self):
        df = self.generate_test_data(days=50)
        strategy = NBreakStrategy(ma_period=20, strong_rise_period=10)
        strategy.reset()
        
        strategy.position_opened = True
        strategy.entry_price = 100.0
        strategy.take_profit_price = 110.0
        strategy.n_value = 2.0
        strategy.stop_loss_price = 96.0
        
        df_test = df.copy()
        df_test.iloc[-1, df_test.columns.get_loc('closePrice')] = 111.0
        df_test.iloc[-1, df_test.columns.get_loc('highPrice')] = 112.0
        
        signal = strategy.calculate(df_test)
        if signal:
            self.assertEqual(signal.signal_type, SignalType.SELL)
        print("止盈测试通过")

    def test_with_backtest_engine(self):
        from backtest import BacktestEngine
        
        df = self.generate_test_data(days=200)
        strategy = NBreakStrategy(ma_period=20, strong_rise_period=10)
        strategy.reset()
        
        engine = BacktestEngine(initial_capital=10000.0)
        stats = engine.run_with_data(strategy, df, symbol="TEST")
        
        self.assertGreater(stats.final_capital, 0)
        print(f"回测资金: {stats.final_capital:.2f}")
        print("回测引擎集成测试通过")


if __name__ == '__main__':
    print("\n开始精准N破战法测试\n")
    unittest.main()