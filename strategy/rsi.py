# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class RSIStrategy(SignalStrategy):
    """RSI 策略
    
    RSI (Relative Strength Index) 相对强弱指数：
    - 买入：RSI < 30 超卖区域
    - 卖出：RSI > 70 超买区域
    """
    
    def __init__(self, period: int = 14):
        self.period = period
    
    @property
    def name(self) -> str:
        return f"RSI_{self.period}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df, idx: int = -1) -> Optional[Signal]:
        if df is None or len(df) < self.period + 1:
            return None

        if idx > -1:
            current_time = df.iloc[idx]['closeTime']
        else:
            current_time = int(time_module.mktime(time_module.gmtime()) * 1000)

        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'], unit='ms')
        df['closeTime'] = pd.to_datetime(df['closeTime'], unit='ms')
        df = df.sort_values('openTime', ascending=True)
        
        delta = df['closePrice'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(self.period).mean()
        avg_loss = loss.rolling(self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['RSI'] = rsi
        
        buy_signal = (df['RSI'] < 30) & (df['RSI'].shift(1) >= 30)
        sell_signal = (df['RSI'] > 70) & (df['RSI'].shift(1) <= 70)
        
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
