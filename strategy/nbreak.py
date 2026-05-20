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
            strong_rise_min_count: int = 3,
            strong_rise_body_ratio: float = 1.5,
            volume_amplify_ratio: float = 1.5,
            pullback_volume_ratio: float = 0.7,
            breakout_volume_ratio: float = 1.2,
            breakout_threshold: float = 0.01,
            atr_period: int = 20,
            atr_stop_loss_ratio: float = 2.0,
            breakout_check_volume_ratio: float = 1.0,
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
        :param breakout_check_volume_ratio: 破位出场成交量检查倍数，默认1.0
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
        self.breakout_check_volume_ratio = breakout_check_volume_ratio

        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0
        self.position_opened = False

        self._in_rise_phase = False
        self._in_pullback_phase = False
        self._pullback_low = 0.0
        self._pullback_high = 0.0
        self._rise_high = 0.0
        self._pre_rise_volume_ma = 0.0

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

        if len(df) >= self.atr_period + 1:
            high_prices = df['highPrice'].values
            low_prices = df['lowPrice'].values
            close_prices = df['closePrice'].values
            
            tr_values = np.zeros(len(df) - 1)
            for i in range(1, len(df)):
                high_low = high_prices[i] - low_prices[i]
                high_close = abs(high_prices[i] - close_prices[i - 1])
                low_close = abs(low_prices[i] - close_prices[i - 1])
                tr_values[i - 1] = max(high_low, high_close, low_close)
            
            first_tr_avg = np.mean(tr_values[:self.atr_period])
            
            atr_value = first_tr_avg
            for i in range(self.atr_period, len(tr_values)):
                atr_value = (atr_value * (self.atr_period - 1) + tr_values[i]) / self.atr_period
            
            self.n_value = atr_value
        else:
            self.n_value = current_high - current_low

        if not self.position_opened:
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
            
            self._detect_n_pattern(df, current_price, ma, volume_ma5, current_volume, current_high)
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

            if current_price < ma and current_volume > volume_ma5 * self.breakout_check_volume_ratio:
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
        
        if self._in_rise_phase:
            if current_price < self._rise_high * 0.98:
                self._in_rise_phase = False
                self._in_pullback_phase = True
                self._pullback_low = current_price
                self._pullback_high = self._rise_high
        else:
            rise_bars = df.iloc[-self.strong_rise_period - 1:-1]
            rise_count = 0
            total_body = 0.0

            for bar in rise_bars.itertuples():
                body = bar.closePrice - bar.openPrice
                if body > 0:
                    total_body += body
                    rise_count += 1

            avg_body = total_body / rise_count if rise_count > 0 else 0.0

            prev_volume_start = -self.strong_rise_period - 10
            prev_volume_end = -self.strong_rise_period - 1
            if prev_volume_start >= -len(df):
                prev_volume_ma = df['volume'].iloc[prev_volume_start:prev_volume_end].mean()
            else:
                prev_volume_ma = df['volume'].iloc[:-self.strong_rise_period - 1].mean()
            
            recent_volume_ma = df['volume'].iloc[-self.strong_rise_period - 1:-1].mean()
            
            volume_amplified = False
            if prev_volume_ma > 0 and recent_volume_ma >= prev_volume_ma * self.volume_amplify_ratio:
                volume_amplified = True

            if rise_count >= self.strong_rise_min_count and volume_amplified and avg_body >= self.n_value * self.strong_rise_body_ratio:
                if current_price > ma:
                    self._in_rise_phase = True
                    self._rise_high = current_high
                    self._pre_rise_volume_ma = prev_volume_ma

        if self._in_pullback_phase:
            if current_price < self._pullback_low:
                self._pullback_low = current_price

            if self._pre_rise_volume_ma > 0:
                pullback_volume_check = df['volume'].iloc[-3:].mean()
                if pullback_volume_check > self._pre_rise_volume_ma * self.pullback_volume_ratio:
                    self._in_pullback_phase = False
                    self._pullback_low = 0.0
                    self._pullback_high = 0.0
                    self._rise_high = 0.0
                    self._pre_rise_volume_ma = 0.0
                    return

            if current_price < ma:
                self._in_pullback_phase = False
                self._pullback_low = 0.0
                self._pullback_high = 0.0
                self._rise_high = 0.0
                self._pre_rise_volume_ma = 0.0

    def _reset_phase_detection(self):
        self._in_rise_phase = False
        self._in_pullback_phase = False
        self._pullback_low = 0.0
        self._pullback_high = 0.0
        self._rise_high = 0.0
        self._pre_rise_volume_ma = 0.0

    def reset(self):
        self.entry_price = 0.0
        self.stop_loss_price = 0.0
        self.take_profit_price = 0.0
        self.n_value = 0.0
        self.position_opened = False
        self._reset_phase_detection()