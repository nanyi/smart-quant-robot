# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum


class SignalType(IntEnum):
    """信号类型"""
    NEUTRAL = 0
    BUY = 1
    SELL = -1


@dataclass
class Signal:
    """交易信号数据类
    
    封装策略生成的交易信号信息，包含信号类型、价格、时间等关键属性
    """
    signal_type: SignalType
    """信号类型（买入/卖出/中性）"""
    
    strategy_name: str
    """生成该信号的策略名称"""
    
    weight: float
    """策略权重（用于多策略组合时的资金分配）"""
    
    price: float
    """信号触发时的价格"""
    
    time: str
    """信号触发时间"""
    
    confidence: float = 1.0
    """信号置信度（0-1之间，默认为1.0）"""

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
    def calculate(self, df):
        """计算交易信号
        
        :param df: K线数据 DataFrame
        :return: Signal 或 None
        """
        pass
