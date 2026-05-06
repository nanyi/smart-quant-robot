# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class VolumeStrategy(SignalStrategy):
    """成交量验证策略
    
    结合成交量确认价格趋势：
    - 买入：量增价涨（成交量 > 均量且价格 > MA）
    - 卖出：量缩价跌（成交量 < 均量且价格 < MA）
    """
    
    def __init__(self, vol_ma: int = 5, price_ma: int = 20):
        self.vol_ma = vol_ma
        self.price_ma = price_ma
    
    @property
    def name(self) -> str:
        return f"VOLUME_{self.vol_ma}_{self.price_ma}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < max(self.vol_ma, self.price_ma):
            return None
        
        df = df.copy()
        df['openTime'] = pd.to_datetime(df['openTime'])
        df = df.sort_values('openTime', ascending=True)
        
        df['vol_ma'] = df['volume'].rolling(self.vol_ma).mean()
        df['price_ma'] = df['closePrice'].rolling(self.price_ma).mean()
        
        vol_cond = df['volume'] > df['vol_ma']
        price_cond = df['closePrice'] > df['price_ma']
        
        buy_signal = vol_cond & price_cond & (vol_cond.shift(1) == False)
        sell_signal = (~vol_cond) & (~price_cond) & (vol_cond.shift(1) == True)
        
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
