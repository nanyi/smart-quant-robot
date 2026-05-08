# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class TurtleStrategy(SignalStrategy):
    """海龟交易法则（Turtle Trading System）
    
    核心要素：
    - 入场：突破N日最高/最低点
    - 加仓：价格突破0.5N时加仓1个单位
    - 止损：价格跌破买入价-2N时止损
    - 出场：跌破N日最低点
    """

    def __init__(
            self,
            entry_period: int = 20,
            exit_period: int = 10,
            atr_period: int = 20,
            risk_ratio: float = 0.02,
            max_units: int = 4,
    ):
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        self.risk_ratio = risk_ratio
        self.max_units = max_units

        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.position_units = 0
        self.last_add_price = 0.0
        self.n_value = 0.0

    @property
    def name(self) -> str:
        return f"TURTLE_{self.entry_period}_{self.exit_period}_{self.atr_period}"

    @property
    def weight(self) -> float:
        return 1.0

    def calculate(self, df) -> Optional[Signal]:
        min_period = max(self.entry_period, self.exit_period, self.atr_period)
        if df is None or len(df) < min_period + 1:
            return None

        current_bar = df.iloc[-1]
        current_price = current_bar['closePrice']
        current_time = current_bar['closeTime']
        high_price = current_bar['highPrice']
        low_price = current_bar['lowPrice']

        entry_high = df['highPrice'].iloc[-self.entry_period - 1:-1].max()
        entry_low = df['lowPrice'].iloc[-self.entry_period - 1:-1].min()
        exit_high = df['highPrice'].iloc[-self.exit_period - 1:-1].max()
        exit_low = df['lowPrice'].iloc[-self.exit_period - 1:-1].min()

        prev_bar = df.iloc[-2]
        tr1 = prev_bar['highPrice'] - prev_bar['lowPrice']
        tr2 = abs(prev_bar['highPrice'] - df.iloc[-3]['closePrice'])
        tr3 = abs(prev_bar['lowPrice'] - df.iloc[-3]['closePrice'])
        current_tr = max(tr1, tr2, tr3)

        if len(df) >= self.atr_period:
            atr_values = []
            for i in range(len(df) - self.atr_period - 1, len(df) - 1):
                bar = df.iloc[i]
                prev_bar = df.iloc[i - 1]
                tr1 = bar['highPrice'] - bar['lowPrice']
                tr2 = abs(bar['highPrice'] - prev_bar['closePrice'])
                tr3 = abs(bar['lowPrice'] - prev_bar['closePrice'])
                atr_values.append(max(tr1, tr2, tr3))
            self.n_value = np.mean(atr_values)
        else:
            self.n_value = current_tr

        if self.position_units == 0:
            self.entry_price = 0.0
            self.stop_loss_price = 0.0
            self.last_add_price = 0.0

            if high_price > entry_high and self.n_value > 0:
                self.position_units = 1
                self.entry_price = current_price
                self.stop_loss_price = current_price - 2 * self.n_value
                self.last_add_price = current_price + 0.5 * self.n_value

                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
            elif low_price < entry_low and self.n_value > 0:
                self.position_units = -1
                self.entry_price = current_price
                self.stop_loss_price = current_price + 2 * self.n_value
                self.last_add_price = current_price - 0.5 * self.n_value

                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
        elif self.position_units > 0:
            if current_price < self.stop_loss_price:
                self.position_units = 0
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if low_price < exit_low:
                self.position_units = 0
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            add_price = self.last_add_price + 0.5 * self.n_value
            if high_price > add_price and self.position_units < self.max_units:
                self.position_units += 1
                self.last_add_price = add_price
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
        else:
            if current_price > self.stop_loss_price:
                self.position_units = 0
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if high_price > exit_high:
                self.position_units = 0
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            add_price = self.last_add_price - 0.5 * self.n_value
            if low_price < add_price and self.position_units > -self.max_units:
                self.position_units -= 1
                self.last_add_price = add_price
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

        return None

    def reset(self):
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.position_units = 0
        self.last_add_price = 0.0
        self.n_value = 0.0
