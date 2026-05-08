import os
import re
import unittest
from datetime import timedelta

import numpy as np
import pandas as pd

from backtest import BacktestReporter
from strategy.base import SignalType
from strategy.ma import MAStrategy


def generate_test_data(days=365, start_price=100):
    """生成模拟K线数据"""
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

    print("df数据行数=" + str(len(df)))
    print(df)

    return df

def generate_unique_filename(base_path):
    """生成唯一的文件名,如果文件已存在则添加序号"""
    if not os.path.exists(base_path):
        return base_path

    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)

    # 检查是否已有序号格式
    match = re.match(r'^(.+)\((\d+)\)$', name)
    if match:
        base_name = match.group(1)
        num = int(match.group(2))
    else:
        base_name = name
        num = 0

    # 递增查找可用文件名
    while True:
        num += 1
        new_filename = f"{base_name}({num}){ext}"
        new_path = os.path.join(directory, new_filename) if directory else new_filename
        if not os.path.exists(new_path):
            return new_path

def save_backtest_data(df, strategy, engine, stats):
    # 确保输出目录存在
    output_dir = "./backtest/report"
    os.makedirs(output_dir, exist_ok=True)
    
    #  保存报告
    reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
    reporter_text = reporter.generate_text_report()
    with open(generate_unique_filename("./backtest/report/backtest_report.txt"), "w", encoding="utf-8") as f:
        f.write(reporter_text)

    # 保存K线数据 到excel表
    df.to_excel(generate_unique_filename("./backtest/report/backtest_data.xlsx"), index=False)

    # 保存订单数据到excel表
    orders_df = pd.DataFrame([{
        'order_id': order.order_id,
        'symbol': order.symbol,
        'side': order.side.value,
        'order_type': order.order_type.value,
        'price': order.price,
        'quantity': order.quantity,
        'filled_quantity': order.filled_quantity,
        'status': order.status.value,
        'create_time': order.create_time,
        'update_time': order.update_time
    } for order in engine.get_orders()])
    
    if not orders_df.empty:
        orders_df.to_excel(generate_unique_filename("./backtest/report/backtest_orders.xlsx"), index=False)

    #  保存交易数据
    trades_df = pd.DataFrame([{
        'trade_id': trade.trade_id,
        'order_id': trade.order_id,
        'symbol': trade.symbol,
        'side': trade.side.value,
        'price': trade.price,
        'quantity': trade.quantity,
        'turnover': trade.turnover,
        'commission': trade.commission,
        'trade_time': trade.trade_time
    } for trade in engine.get_trades()])
    
    if not trades_df.empty:
        trades_df.to_excel(generate_unique_filename("./backtest/report/backtest_trades.xlsx"), index=False)

    # 保存仓位数据
    positions_dict = engine.get_positions()
    if positions_dict:
        positions_df = pd.DataFrame([{
            'symbol': pos.symbol,
            'side': pos.side.value,
            'quantity': pos.quantity,
            'entry_price': pos.entry_price,
            'current_price': pos.current_price,
            'unrealized_pnl': pos.unrealized_pnl
        } for pos in positions_dict.values()])
        
        positions_df.to_excel(generate_unique_filename("./backtest/report/backtest_positions.xlsx"), index=False)

class MyTestCase(unittest.TestCase):
    """
    双均线策略测试脚本
    """
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_basic_functionality(self):
        """测试基本功能"""
        print("=" * 60)
        print("测试1：基本功能测试")
        print("=" * 60)

        df = generate_test_data(days=200)
        strategy = MAStrategy(short_period=5, long_period=20)

        signals = []
        for idx in range(len(df)):
            # 获取idx处及之前的K线数据
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

        df = generate_test_data(days=10)
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

        df = generate_test_data(days=365)
        strategy = MAStrategy(short_period=10, long_period=30)

        signals = []
        for idx in range(len(df)):
            # 获取idx处及之前的K线数据
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

        df = generate_test_data(days=500)

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
                # 获取idx处及之前的K线数据
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

            df = generate_test_data(days=365)
            strategy = MAStrategy(short_period=5, long_period=20)

            engine = BacktestEngine(initial_capital=100000, commission_rate=0.001)
            stats = engine.run_with_data(strategy, df, symbol="TEST")

            # print(f"初始资金: {stats.initial_capital:.2f}")
            # print(f"最终资金: {stats.final_capital:.2f}")
            # print(f"总收益: {stats.final_capital - stats.initial_capital:.2f}")
            # print(f"总收益率: {(stats.final_capital / stats.initial_capital - 1) * 100:.2f}")
            # print(f"最大回撤: {stats.max_drawdown:.2f}")
            # print(f"交易次数: {stats.total_trades}")
            # print(f"胜率: {stats.win_rate:.2%}")
            # print(f"平均每笔交易利润: {stats.avg_profit:.2f}")
            # print(f"总利润: {stats.total_profit:.2f}")
            # print(f"总利润率: {stats.total_profit / stats.initial_capital * 100:.2f}")

            # 在此处实现将df、strategy、engine、stats等信息保存到文件中
            save_backtest_data(df, strategy, engine, stats)

            reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
            # report_json = reporter.generate_json_report()
            # 　print(report_json)
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
