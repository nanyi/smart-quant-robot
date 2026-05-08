# -*- coding: utf-8 -*-
import unittest
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