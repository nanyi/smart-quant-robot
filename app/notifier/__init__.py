# -*- coding: utf-8 -*-
"""
消息通知模块

支持钉钉和企业微信通知，通过配置选择通知渠道
"""
from app.notifier.base import Notifier
from app.notifier.dingding import DingdingNotifier
from app.notifier.factory import get_notifier
from app.notifier.weixin import WeixinNotifier

__all__ = ['Notifier', 'DingdingNotifier', 'WeixinNotifier', 'get_notifier']