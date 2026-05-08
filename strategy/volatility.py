# -*- coding: utf-8 -*-
from typing import Optional

import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class VolatilityStrategy(SignalStrategy):
    """波动率突破策略
    
    当价格突破一定周期的波动率通道时产生信号：
    - 买入：价格突破上轨（MA + N × STD）
    - 卖出：价格跌破下轨（MA - N × STD）
    """
    
    def __init__(self, period: int = 20, std_mult: float = 2.0):
        self.period = period
        self.std_mult = std_mult
    
    @property
    def name(self) -> str:
        return f"VOLATILITY_{self.period}_{self.std_mult}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < self.period:
            return None

        # 创建副本
        df = df.copy()
        current_bar = df.iloc[-1]
        current_time = current_bar['closeTime']

        df['MA'] = df['closePrice'].rolling(self.period).mean()
        df['STD'] = df['closePrice'].rolling(self.period).std()
        df['upper'] = df['MA'] + self.std_mult * df['STD']
        df['lower'] = df['MA'] - self.std_mult * df['STD']
        
        close = df['closePrice']
        upper = df['upper']
        lower = df['lower']
        
        buy_signal = (close > upper) & (close.shift(1) <= upper.shift(1))
        sell_signal = (close < lower) & (close.shift(1) >= lower.shift(1))

        if buy_signal.iloc[-1]:
            return Signal(
                signal_type=SignalType.BUY,
                strategy_name=self.name,
                weight=self.weight,
                price=float(current_bar['closePrice']),
                time=str(pd.to_datetime(current_time, unit='ms')),
                confidence=1.0
            )
        if sell_signal.iloc[-1]:
            return Signal(
                signal_type=SignalType.SELL,
                strategy_name=self.name,
                weight=self.weight,
                price=float(current_bar['closePrice']),
                time=str(pd.to_datetime(current_time, unit='ms')),
                confidence=1.0
            )
        return None
