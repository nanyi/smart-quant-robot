# -*- coding: utf-8 -*-
from typing import Optional

from app.notifier.base import Notifier
from app.notifier.dingding import DingdingNotifier
from app.notifier.weixin import WeixinNotifier
from runtime_config import config


_notifier_singleton: Optional[Notifier] = None


def get_notifier() -> Notifier:
    """
    获取通知器实例

    根据配置创建对应的通知器

    :return: Notifier 实例
    """
    global _notifier_singleton

    if _notifier_singleton is None:
        provider = config.get('notifier.provider', 'dingding')

        if provider == 'weixin':
            _notifier_singleton = WeixinNotifier()
            _notifier_singleton.start()
        else:
            _notifier_singleton = DingdingNotifier()

    return _notifier_singleton