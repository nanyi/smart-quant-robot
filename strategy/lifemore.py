# -*- coding: utf-8 -*-
from typing import Optional

import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class LivermoreStrategy(SignalStrategy):
    """利费莫尔交易法则（Livermore Trading System）
    
    核心要素：
    - 入场：突破历史高低点
    - 加仓：金字塔型，5%-10%间隔
    - 止损：移动止损，最高点回落10%
    - 出场：分批平仓
    """

    def __init__(
            self,
            breakout_period: int = 30,
            pyramid_ratio: float = 0.05,
            stop_loss_ratio: float = 0.10,
            exit_ratio: float = 0.20,
    ):
        """初始化利费莫尔交易策略
        
        基于杰西·利费莫尔的交易理念：关键点突破、金字塔加仓、严格止损
        
        :param breakout_period: 突破周期（关键价格区间），默认30
        :param pyramid_ratio: 金字塔加仓比例（价格每上涨多少比例加仓），默认0.05
        :param stop_loss_ratio: 止损比例，默认0.10
        :param exit_ratio: 出场回撤比例，默认0.20
        """
        self.breakout_period = breakout_period
        self.pyramid_ratio = pyramid_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.exit_ratio = exit_ratio

        # 持仓状态跟踪变量
        self.highest_price = 0.0
        self.position_count = 0
        self.last_add_price = 0.0
        self.entry_price = 0.0

    @property
    def name(self) -> str:
        return f"LIVERMORE_{self.breakout_period}_{self.pyramid_ratio}_{self.stop_loss_ratio}"

    @property
    def weight(self) -> float:
        return 1.0

    def calculate(self, df) -> Optional[Signal]:
        if df is None or len(df) < self.breakout_period + 1:
            return None

        current_bar = df.iloc[-1]
        current_price = current_bar['closePrice']
        current_time = current_bar['closeTime']

        period_high = df['closePrice'].iloc[- self.breakout_period - 1:-1].max()
        period_low = df['closePrice'].iloc[- self.breakout_period - 1:-1].min()

        if self.position_count == 0:
            self.highest_price = 0.0
            self.last_add_price = 0.0
            self.entry_price = 0.0

            if current_price > period_high:
                self.position_count = 1
                self.highest_price = current_price
                self.last_add_price = current_price
                self.entry_price = current_price

                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
            elif current_price < period_low:
                self.position_count = -1
                self.highest_price = current_price
                self.last_add_price = current_price
                self.entry_price = current_price

                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
        elif self.position_count > 0:
            if current_price > self.highest_price:
                self.highest_price = current_price
                self.last_add_price = current_price

            if current_price < self.highest_price * (1 - self.stop_loss_ratio):
                self.position_count = 0
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            add_price = self.last_add_price * (1 + self.pyramid_ratio)
            if current_price >= add_price and self.position_count < 4:
                self.position_count += 1
                self.last_add_price = add_price
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if current_price < period_low:
                self.position_count = 0
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )
        else:
            if current_price < self.highest_price:
                self.highest_price = current_price
                self.last_add_price = current_price

            if current_price > self.highest_price * (1 + self.stop_loss_ratio):
                self.position_count = 0
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            add_price = self.last_add_price * (1 - self.pyramid_ratio)
            if current_price <= add_price and self.position_count > -4:
                self.position_count -= 1
                self.last_add_price = add_price
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if current_price > period_high:
                self.position_count = 0
                return Signal(
                    signal_type=SignalType.BUY,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

        return None

    def reset(self):
        self.highest_price = 0.0
        self.position_count = 0
        self.last_add_price = 0.0
        self.entry_price = 0.0
