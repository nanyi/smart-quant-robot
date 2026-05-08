# -*- coding: utf-8 -*-
from typing import Optional

import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class MAStrategy(SignalStrategy):
    """双均线策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 60):
        """初始化双均线策略

        :param short_period: 短期均线周期（快线），默认5
        :param long_period: 长期均线周期（慢线），默认60
        """
        self.short_period = short_period
        self.long_period = long_period

    @property
    def name(self) -> str:
        return f"MA_{self.short_period}_{self.long_period}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        # 如果数据还不够计算长均线（比如刚开始回测的前几天），就直接返回，不操作
        if df is None or len(df) < self.long_period:
            return None

        current_bar = df.iloc[-1]
        current_time = current_bar['closeTime']

        # 求出均线
        ma_short = df['closePrice'].rolling(self.short_period).mean()
        ma_long = df['closePrice'].rolling(self.long_period).mean()

        if len(ma_short) < self.long_period or pd.isna(ma_short.iloc[-1]) or pd.isna(ma_long.iloc[-1]):
            return None

        current_ma_short = ma_short.iloc[-1]
        current_ma_long = ma_long.iloc[-1]
        prev_ma_short = ma_short.iloc[-2]
        prev_ma_long = ma_long.iloc[-2]

        # 判断金叉：前一日短期均线 <= 长期均线，今日短期均线 > 长期均线
        golden_cross = (current_ma_short > current_ma_long) and (prev_ma_short <= prev_ma_long)
        # 判断死叉：前一日短期均线 >= 长期均线，今日短期均线 < 长期均线
        death_cross = (current_ma_short < current_ma_long) and (prev_ma_short >= prev_ma_long)

        if golden_cross:
            return Signal(
                signal_type=SignalType.BUY,
                strategy_name=self.name,
                weight=self.weight,
                price=float(current_bar['closePrice']),
                time=str(pd.to_datetime(current_time, unit='ms')),
                confidence=1.0
            )
        elif death_cross:
            return Signal(
                signal_type=SignalType.SELL,
                strategy_name=self.name,
                weight=self.weight,
                price=float(current_bar['closePrice']),
                time=str(pd.to_datetime(current_time, unit='ms')),
                confidence=1.0
            )

        return None
