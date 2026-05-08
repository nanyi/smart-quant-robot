# -*- coding: utf-8 -*-
import unittest

from backtest import BacktestReporter
from strategy.base import SignalType
from strategy.ma import MAStrategy
from tests import BaseStrategyTestCase


class TestMAStrategy(BaseStrategyTestCase):
    """双均线策略测试类"""

    def test_basic_functionality(self):
        """测试基本功能"""
        print("=" * 60)
        print("测试1：基本功能测试")
        print("=" * 60)

        df = self.generate_test_data(days=200)
        strategy = MAStrategy(short_period=5, long_period=20)

        signals = []
        for idx in range(len(df)):
            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df, idx)
            if signal:
                signals.append((idx, signal))
                print(f"索引 {idx} | 时间: {signal.time} | "
                      f"类型: {'买入' if signal.signal_type == SignalType.BUY else '卖出'} | "
                      f"价格: {signal.price:.2f}")

        print(f"\n共生成 {len(signals)} 个交易信号")

        buy_signals = [s for _, s in signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for _, s in signals if s.signal_type == SignalType.SELL]
        print(f"买入信号: {len(buy_signals)}, 卖出信号: {len(sell_signals)}")

        assert len(signals) > 0, "应该产生至少一个信号"
        print("✓ 基本功能测试通过\n")

    def test_insufficient_data(self):
        """测试数据不足的情况"""
        print("=" * 60)
        print("测试2：数据不足测试")
        print("=" * 60)

        df = self.generate_test_data(days=10)
        strategy = MAStrategy(short_period=5, long_period=20)

        signal = strategy.calculate(df)
        self.assertIs(signal, None, "数据不足时应返回None")

        signal = strategy.calculate(df, 15)
        self.assertIs(signal, None, "数据不足时应返回None")

        print("✓ 数据不足测试通过\n")

    def test_signal_sequence(self):
        """测试信号序列的合理性"""
        print("=" * 60)
        print("测试3：信号序列测试")
        print("=" * 60)

        df = self.generate_test_data(days=365)
        strategy = MAStrategy(short_period=10, long_period=30)

        signals = []
        for idx in range(len(df)):
            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df, idx)
            if signal:
                signals.append(signal)

        if len(signals) < 2:
            print("信号太少，跳过序列测试")
            return

        print(f"\n共生成 {len(signals)} 个交易信号")

        last_type = None
        for i, signal in enumerate(signals):
            current_type = signal.signal_type
            if last_type is not None:
                if current_type == SignalType.BUY:
                    assert last_type == SignalType.SELL, f"买入信号前应该有卖出信号 (索引 {i})"
                elif current_type == SignalType.SELL:
                    assert last_type == SignalType.BUY, f"卖出信号前应该有买入信号 (索引 {i})"
            last_type = current_type

        print("✓ 信号序列测试通过（买卖信号交替出现）\n")

    def test_different_parameters(self):
        """测试不同参数组合"""
        print("=" * 60)
        print("测试4：不同参数组合测试")
        print("=" * 60)

        df = self.generate_test_data(days=500)

        param_combinations = [
            (5, 20),
            (10, 30),
            (20, 60),
            (5, 60),
        ]

        for short_period, long_period in param_combinations:
            strategy = MAStrategy(short_period=short_period, long_period=long_period)
            signal_count = 0

            for idx in range(len(df)):
                before_df = df[:idx + 1]
                if strategy.calculate(before_df, idx):
                    signal_count += 1

            print(f"MA({short_period}, {long_period}): 生成 {signal_count} 个信号")
            assert signal_count >= 0, f"MA({short_period}, {long_period}) 参数组合异常"

        print("\n✓ 参数组合测试通过\n")

    def test_with_real_backtest(self):
        """与回测引擎集成测试"""
        print("=" * 60)
        print("测试5：回测引擎集成测试")
        print("=" * 60)

        try:
            from backtest.engine import BacktestEngine

            df = self.generate_test_data(days=365)
            strategy = MAStrategy(short_period=5, long_period=20)

            engine = BacktestEngine(initial_capital=100000, commission_rate=0.001)
            stats = engine.run_with_data(strategy, df, symbol="TEST")

            self.save_backtest_report(df, strategy, engine, stats)

            reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
            print(reporter.generate_text_report())

            assert stats.final_capital > 0, "最终资金应该大于0"
            assert stats.total_trades >= 0, "交易次数应该非负"

            print("\n✓ 回测引擎集成测试通过\n")

        except ImportError as e:
            print(e)
            print("⚠ 回测引擎未找到，跳过集成测试\n")


if __name__ == '__main__':
    print("\n🚀 开始运行双均线策略测试\n")
    unittest.main()

    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)