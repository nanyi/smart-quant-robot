# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import time as time_module

from strategy.base import SignalStrategy, Signal, SignalType


class MAStrategy(SignalStrategy):
    """双均线策略"""
    
    def __init__(self, ma_x: int = 5, ma_y: int = 60):
        self.ma_x = ma_x
        self.ma_y = ma_y
    
    @property
    def name(self) -> str:
        return f"MA_{self.ma_x}_{self.ma_y}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < self.ma_y:
            return None
        
        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'])
        df = df.sort_values('openTime', ascending=True)
        
        maX = df['closePrice'].rolling(self.ma_x).mean()
        maY = df['closePrice'].rolling(self.ma_y).mean()
        
        s1 = maX < maY
        s2 = maX > maY
        
        death_ex = s1 & s2.shift(1)
        golden_ex = ~(s1 | s2.shift(1))
        
        death_dates = df.loc[death_ex].index
        golden_dates = df.loc[golden_ex].index
        
        s1_series = pd.Series(data=SignalType.BUY, index=golden_dates)
        s2_series = pd.Series(data=SignalType.SELL, index=death_dates)
        
        signals = s1_series.append(s2_series).sort_index()
        
        for i in range(len(signals) - 1, -1, -1):
            sig_time = signals.index[i]
            sig_type = signals.iloc[i]
            
            open_time = df.loc[sig_time, 'openTime']
            close_time = df.loc[sig_time, 'closeTime']
            
            if self._is_valid_time(str(open_time), str(close_time)):
                price = float(df.loc[sig_time, 'closePrice'])
                return Signal(
                    signal_type=sig_type,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=price,
                    time=str(open_time),
                    confidence=1.0
                )
        return None
    
    def _is_valid_time(self, openTime: str, closeTime: str) -> bool:
        dt_interval = pd.to_datetime(closeTime) - pd.to_datetime(openTime)
        seconds = dt_interval.seconds
        now = int(round((time_module.time() - seconds) * 1000))
        now_str = time_module.strftime('%Y-%m-%d %H:%M:%S', time_module.localtime(now / 1000))
        return now_str >= openTime and now_str <= closeTime
