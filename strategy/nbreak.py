# -*- coding: utf-8 -*-
from typing import Optional

import numpy as np
import pandas as pd

from strategy.base import SignalStrategy, Signal, SignalType


class NBreakStrategy(SignalStrategy):
    """精准N破战法（N-Breaker Strategy）
    
    核心要素：
    - N字形态：强势拉升段 + 缩量回踩段 + 放量突破段
    - 入场：价格 > 20日均线 + N字形态完成 + 放量突破前高
    - 止损：基于ATR的动态止损（入场价 - 2*ATR）
    - 止盈：固定止盈（入场价 * 1.10）
    - 破位出场：价格 < 20日均线 且 成交量放大
    """

    def __init__(
            self,
            ma_period: int = 20,
            strong_rise_period: int = 10,
            strong_rise_min_count: int = 2,
            strong_rise_body_ratio: float = 1.2,
            volume_amplify_ratio: float = 1.2,
            pullback_volume_ratio: float = 0.7,
            breakout_volume_ratio: float = 1.2,
            breakout_threshold: float = 0.01,
            atr_period: int = 20,
            atr_stop_loss_ratio: float = 2.0,
    ):
        """初始化精准N破战法策略
        
        :param ma_period: 均线周期，默认20
        :param strong_rise_period: 强势拉升段K线数量，默认10
        :param strong_rise_min_count: 强势拉升段最小阳线数，默认3
        :param strong_rise_body_ratio: 拉升段最小平均K线实体/ATR比率，默认1.5
        :param volume_amplify_ratio: 成交量放大倍数，默认1.5
        :param pullback_volume_ratio: 缩量回踩比例，默认0.7
        :param breakout_volume_ratio: 放量突破比例，默认1.2
        :param breakout_threshold: 突破确认阈值，默认1%
        :param atr_period: ATR计算周期，默认20
        :param atr_stop_loss_ratio: ATR止损倍数，默认2.0
        """
        self.ma_period = ma_period
        self.strong_rise_period = strong_rise_period
        self.strong_rise_min_count = strong_rise_min_count
        self.strong_rise_body_ratio = strong_rise_body_ratio
        self.volume_amplify_ratio = volume_amplify_ratio
        self.pullback_volume_ratio = pullback_volume_ratio
        self.breakout_volume_ratio = breakout_volume_ratio
        self.breakout_threshold = breakout_threshold
        self.atr_period = atr_period
        self.atr_stop_loss_ratio = atr_stop_loss_ratio

        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0
        self.position_opened = False

        self._in_rise_phase = False
        self._in_pullback_phase = False
        self._pullback_low = 0.0
        self._pullback_high = 0.0

    @property
    def name(self) -> str:
        return f"NBREAK_{self.ma_period}_{self.strong_rise_period}_{self.atr_period}"

    @property
    def weight(self) -> float:
        return 1.0

    def calculate(self, df) -> Optional[Signal]:
        min_period = max(
            self.ma_period,
            self.strong_rise_period,
            self.atr_period,
            5
        )
        if df is None or len(df) < min_period + 1:
            return None

        current_bar = df.iloc[-1]
        current_price = current_bar['closePrice']
        current_high = current_bar['highPrice']
        current_low = current_bar['lowPrice']
        current_volume = current_bar['volume']
        current_time = current_bar['closeTime']

        ma = df['closePrice'].iloc[-self.ma_period:].mean()
        volume_ma5 = df['volume'].iloc[-6:-1].mean()

        atr_values = []
        for i in range(len(df) - self.atr_period, len(df) - 1):
            if i < 1:
                continue
            bar = df.iloc[i]
            prev_close = df.iloc[i - 1]['closePrice']
            tr1 = bar['highPrice'] - bar['lowPrice']
            tr2 = abs(bar['highPrice'] - prev_close)
            tr3 = abs(bar['lowPrice'] - prev_close)
            atr_values.append(max(tr1, tr2, tr3))

        if atr_values:
            self.n_value = np.mean(atr_values)
        else:
            self.n_value = current_high - current_low

        if not self.position_opened:
            self._detect_n_pattern(df, current_price, ma, volume_ma5, current_volume, current_high)

            if self._in_pullback_phase and current_price > self._pullback_high * (1 + self.breakout_threshold):
                if current_volume >= volume_ma5 * self.breakout_volume_ratio:
                    self.position_opened = True
                    self.entry_price = current_price
                    self.stop_loss_price = current_price - self.atr_stop_loss_ratio * self.n_value
                    self.take_profit_price = current_price * 1.10

                    return Signal(
                        signal_type=SignalType.BUY,
                        strategy_name=self.name,
                        weight=self.weight,
                        price=float(current_price),
                        time=str(pd.to_datetime(current_time, unit='ms')),
                        confidence=1.0
                    )
        else:
            if current_price < self.stop_loss_price:
                self.position_opened = False
                self._reset_phase_detection()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if current_price > self.take_profit_price:
                self.position_opened = False
                self._reset_phase_detection()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

            if current_price < ma and current_volume > volume_ma5 * self.volume_amplify_ratio:
                self.position_opened = False
                self._reset_phase_detection()
                return Signal(
                    signal_type=SignalType.SELL,
                    strategy_name=self.name,
                    weight=self.weight,
                    price=float(current_price),
                    time=str(pd.to_datetime(current_time, unit='ms')),
                    confidence=1.0
                )

        return None

    def _detect_n_pattern(self, df, current_price, ma, volume_ma5, current_volume, current_high):
        """检测N字形态的拉升和回踩阶段
        
        :param df: K线数据DataFrame
        :param current_price: 当前收盘价
        :param ma: 均线值
        :param volume_ma5: 5周期成交量均值（排除当前K线）
        :param current_volume: 当前成交量
        :param current_high: 当前最高价
        """
        
        # 处理拉升阶段转回踩阶段的逻辑
        if self._in_rise_phase:
            if current_price < df['closePrice'].iloc[-2]:
                self._in_rise_phase = False
                self._in_pullback_phase = True
                self._pullback_low = df['lowPrice'].iloc[-1]
                self._pullback_high = df['highPrice'].iloc[-self.strong_rise_period:-1].max()
        else:
            # 检测强势拉升段：统计阳线数量、实体大小和成交量放大
            rise_bars = df.iloc[-self.strong_rise_period - 1:-1]
            rise_count = 0
            total_body = 0.0
            volume_amplified = False

            for bar in rise_bars.itertuples():
                body = bar.closePrice - bar.openPrice
                if body > 0:
                    total_body += body
                    rise_count += 1

            avg_body = total_body / rise_count if rise_count > 0 else 0.0

            # 检测成交量是否放大：对比近期与前期成交量均值
            if len(df) >= 6:
                prev_volume_ma5 = df['volume'].iloc[-self.strong_rise_period - 6:-self.strong_rise_period - 1].mean()
                if prev_volume_ma5 > 0:
                    recent_volume_ma = df['volume'].iloc[-self.strong_rise_period - 1:-1].mean()
                    if recent_volume_ma >= prev_volume_ma5 * self.volume_amplify_ratio:
                        volume_amplified = True

            # 确认拉升段：阳线数量、成交量放大、实体大小、价格位置均满足条件
            if rise_count >= self.strong_rise_min_count and volume_amplified and avg_body >= self.n_value * self.strong_rise_body_ratio:
                if current_price > ma:
                    self._in_rise_phase = True

        # 处理回踩阶段：追踪最低点，检测退出条件
        if self._in_pullback_phase:
            if current_price < self._pullback_low:
                self._pullback_low = current_price

            # 跌破均线则退出回踩阶段
            if current_price < ma:
                self._in_pullback_phase = False
                self._pullback_low = 0.0
                self._pullback_high = 0.0

    def _reset_phase_detection(self):
        self._in_rise_phase = False
        self._in_pullback_phase = False
        self._pullback_low = 0.0
        self._pullback_high = 0.0

    def reset(self):
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0
        self.position_opened = False
        self._reset_phase_detection()