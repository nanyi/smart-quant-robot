# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum


class SignalType(IntEnum):
    """信号类型"""
    NEUTRAL = 0
    BUY = 1
    SELL = -1


@dataclass
class Signal:
    """交易信号"""
    signal_type: SignalType
    strategy_name: str
    weight: float
    price: float
    time: str
    confidence: float = 1.0


class SignalStrategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    def weight(self) -> float:
        """策略权重"""
        return 1.0
    
    @abstractmethod
    def calculate(self, df, idx: int = -1):
        """计算交易信号
        
        :param df: K线数据 DataFrame
        :param idx: 当前K线所在索引（回测时使用）
        :return: Signal 或 None
        """
        pass
