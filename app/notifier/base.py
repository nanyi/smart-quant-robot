# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import Optional


class Notifier(ABC):
    """消息通知器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """通知器名称"""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """是否启用"""
        pass

    @abstractmethod
    def send(self, text: str, is_default: bool = True) -> bool:
        """
        发送消息
        
        :param text: 消息内容
        :param is_default: 是否使用主配置（True用主配置，False用备用）
        :return: 是否发送成功
        """
        pass

    def start(self):
        """启动通知器（用于异步通知器初始化）"""
        pass

    def stop(self):
        """停止通知器"""
        pass

    def enqueue(self, text: str):
        """加入发送队列（默认同步发送）"""
        self.send(text)