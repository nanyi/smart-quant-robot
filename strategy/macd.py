# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class MACDStrategy(SignalStrategy):
    """MACD 策略
    
    MACD (Moving Average Convergence Divergence) 指数平滑异同移动平均线：
    - 买入：DIF 上穿 DEA（金叉）
    - 卖出：DIF 下穿 DEA（死叉）
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    @property
    def name(self) -> str:
        return f"MACD_{self.fast}_{self.slow}_{self.signal}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df, idx: int = -1) -> Optional[Signal]:
        if df is None or len(df) < self.slow + self.signal:
            return None

        if idx > -1:
            current_time = df.iloc[idx]['closeTime']
        else:
            current_time = int(time_module.mktime(time_module.gmtime()) * 1000)

        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'], unit='ms')
        df['closeTime'] = pd.to_datetime(df['closeTime'], unit='ms')
        df = df.sort_values('openTime', ascending=True)
        
        ema_fast = df['closePrice'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['closePrice'].ewm(span=self.slow, adjust=False).mean()
        df['DIF'] = ema_fast - ema_slow
        df['DEA'] = df['DIF'].ewm(span=self.signal, adjust=False).mean()
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        
        dif = df['DIF']
        dea = df['DEA']
        
        buy_signal = (dif > dea) & (dif.shift(1) <= dea.shift(1))
        sell_signal = (dif < dea) & (dif.shift(1) >= dea.shift(1))
        
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
