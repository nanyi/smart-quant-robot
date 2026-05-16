# -*- coding: utf-8 -*-
import unittest
import random
from datetime import timedelta

import numpy as np
import pandas as pd


class BaseStrategyTestCase(unittest.TestCase):
    """策略测试基类，提供通用测试方法"""

    @staticmethod
    def generate_test_data(days=365, start_price=100):
        """生成模拟K线数据
        
        :param days: 数据天数
        :param start_price: 起始价格
        :return: DataFrame格式的K线数据
        """
        dates = list(pd.date_range(start='2026-01-01', periods=days, freq='D'))

        random.seed(42)
        np.random.seed(42)
        prices = [start_price]
        for _ in range(days - 1):
            change = np.random.normal(0, 0.02)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1))

        open_prices = [p * (1 + np.random.normal(0, 0.01)) for p in prices]
        high_prices = [p * (1 + abs(np.random.normal(0, 0.02))) for p in prices]
        low_prices = [p * (1 - abs(np.random.normal(0, 0.02))) for p in prices]
        volumes = [random.randint(1000, 10000) for _ in range(days)]

        open_times = [int(d.timestamp() * 1000) for d in dates]
        close_times = [int((d + timedelta(hours=23, minutes=59)).timestamp() * 1000) for d in dates]

        df = pd.DataFrame({
            'openTime': open_times,
            'closeTime': close_times,
            'closePrice': prices,
            'openPrice': open_prices,
            'highPrice': high_prices,
            'lowPrice': low_prices,
            'volume': volumes
        })

        print(f"生成数据行数: {len(df)}")
        return df

    def save_backtest_report(self, df, strategy, engine, stats):
        """保存回测报告到文件
        
        :param df: K线数据DataFrame
        :param strategy: 策略实例
        :param engine: 回测引擎
        :param stats: 回测统计
        """
        from backtest import BacktestReporter
        BacktestReporter.save_backtest_report(df, strategy, engine, stats)