# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class BollingerStrategy(SignalStrategy):
    """布林带策略
    
    价格触及布林带轨道产生信号：
    - 买入：价格触及下轨
    - 卖出：价格触及上轨
    """
    
    def __init__(self, period: int = 20, std_mult: float = 2.0):
        self.period = period
        self.std_mult = std_mult
    
    @property
    def name(self) -> str:
        return f"BOLLINGER_{self.period}_{self.std_mult}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df, idx: int=-1) -> Optional[Signal]:
        if df is None or len(df) < self.period:
            return None

        if idx > -1:
            current_time = df.iloc[idx]['closeTime']
        else:
            current_time = int(time_module.mktime(time_module.gmtime()) * 1000)

        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'], unit='ms')
        df['closeTime'] = pd.to_datetime(df['closeTime'], unit='ms')
        df = df.sort_values('openTime', ascending=True)
        
        df['MA'] = df['closePrice'].rolling(self.period).mean()
        df['STD'] = df['closePrice'].rolling(self.period).std()
        df['upper'] = df['MA'] + self.std_mult * df['STD']
        df['lower'] = df['MA'] - self.std_mult * df['STD']
        
        close = df['closePrice']
        upper = df['upper']
        lower = df['lower']
        
        buy_signal = (close <= lower) & (close.shift(1) > lower.shift(1))
        sell_signal = (close >= upper) & (close.shift(1) < upper.shift(1))
        
        for i in range(len(df) - 1, -1, -1):
            if buy_signal.iloc[i]:
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(df.iloc[i]['closePrice']),
                    time=str(df.iloc[i]['openTime']),
                    confidence=1.0
                )
            if sell_signal.iloc[i]:
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(df.iloc[i]['closePrice']),
                    time=str(df.iloc[i]['openTime']),
                    confidence=1.0
                )
        return None
