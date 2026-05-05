# -*- coding: utf-8 -*-
"""
消息通知模块

支持钉钉和企业微信通知，通过配置选择通知渠道
"""
from app.notifier.factory import get_notifier

__all__ = ['get_notifier']
