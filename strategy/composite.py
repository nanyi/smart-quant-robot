# -*- coding: utf-8 -*-
from typing import Optional, List

from strategy.base import SignalStrategy, Signal, SignalType


class CompositeStrategy(SignalStrategy):
    """策略组合器 - 动态加权合成"""
    
    def __init__(self, strategies: List[SignalStrategy], weights: List[float]):
        self.strategies = strategies
        self.weights = weights
    
    @property
    def name(self) -> str:
        return "composite"
    
    @property
    def weight(self) -> float:
        return 1.0
    
    def calculate(self, df) -> Optional[Signal]:
        signals = []
        for strategy in self.strategies:
            signal = strategy.calculate(df)
            if signal:
                signals.append(signal)
        
        if not signals:
            return None
        
        buy_score = sum(s.weight for s in signals if s.signal_type == SignalType.BUY)
        sell_score = sum(s.weight for s in signals if s.signal_type == SignalType.SELL)
        
        threshold = 0.5
        
        if buy_score > sell_score and buy_score > threshold:
            latest = signals[-1]
            for s in reversed(signals):
                if s.signal_type == SignalType.BUY:
                    latest = s
                    break
            return Signal(
                signal_type=SignalType.BUY,
                strategy_name=self.name,
                weight=buy_score,
                price=latest.price,
                time=latest.time,
                confidence=buy_score
            )
        elif sell_score > buy_score and sell_score > threshold:
            latest = signals[-1]
            for s in reversed(signals):
                if s.signal_type == SignalType.SELL:
                    latest = s
                    break
            return Signal(
                signal_type=SignalType.SELL,
                strategy_name=self.name,
                weight=sell_score,
                price=latest.price,
                time=latest.time,
                confidence=sell_score
            )
        return None
