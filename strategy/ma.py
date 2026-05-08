# -*- coding: utf-8 -*-
from typing import Optional
import pandas as pd
import time as time_module

from strategy.base import SignalStrategy, Signal, SignalType


class MAStrategy(SignalStrategy):
    """双均线策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 60):
        # 快线周期
        self.short_period = short_period
        # 慢线周期
        self.long_period = long_period
    
    @property
    def name(self) -> str:
        return f"MA_{self.short_period}_{self.long_period}"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df, idx: int = -1) -> Optional[Signal]:
        # 如果数据还不够计算长均线（比如刚开始回测的前几天），就直接返回，不操作
        if df is None or len(df) < self.long_period:
            return None

        if idx > -1:
            current_time = df.iloc[idx]['closeTime']
        else:
            current_time = int(time_module.mktime(time_module.gmtime()) * 1000)

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

        open_time = df.iloc[idx]['openTime']
        close_time = df.iloc[idx]['closeTime']

        if open_time <= current_time <= close_time:
            if golden_cross:
                price = float(df.iloc[idx]['closePrice'])
                open_time = pd.to_datetime(current_time, unit='ms')
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=price,
                    time=str(open_time),
                    confidence=1.0
                )
            elif death_cross:
                price = float(df.iloc[idx]['closePrice'])
                open_time = pd.to_datetime(current_time, unit='ms')
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=price,
                    time=str(open_time),
                    confidence=1.0
                )
        
        # signals = buy_series.append(sell_series).sort_index()
        #
        # for i in range(len(signals) - 1, -1, -1):
        #     sig_time = signals.index[i]
        #     sig_type = signals.iloc[i]
        #
        #     open_time = df.loc[sig_time, 'openTime']
        #     close_time = df.loc[sig_time, 'closeTime']
        #
        #     if close_time < current_time:
        #         break
        #
        #     if open_time <= current_time <= close_time:
        #         # 判断当前时间是否在当前 K 线区间内
        #         price = float(df.loc[sig_time, 'closePrice'])
        #         return Signal(
        #             signal_type=sig_type,
        #             strategy_name=self.name,
        #             weight=self.weight,
        #             price=price,
        #             time=str(pd.to_datetime(current_time, unit='ms')),
        #             confidence=1.0
        #         )
        return None
