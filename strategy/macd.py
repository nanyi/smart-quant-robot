# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import time as time_module

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
    
    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < self.slow + self.signal:
            return None

        # 创建副本
        df = df.copy()
        current_bar = df.iloc[-1]
        current_time = current_bar['closeTime']

        ema_fast = df['closePrice'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['closePrice'].ewm(span=self.slow, adjust=False).mean()
        df['DIF'] = ema_fast - ema_slow
        df['DEA'] = df['DIF'].ewm(span=self.signal, adjust=False).mean()
        df['MACD'] = (df['DIF'] - df['DEA']) * 2
        
        dif = df['DIF']
        dea = df['DEA']
        
        buy_signal = (dif > dea) & (dif.shift(1) <= dea.shift(1))
        sell_signal = (dif < dea) & (dif.shift(1) >= dea.shift(1))

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
