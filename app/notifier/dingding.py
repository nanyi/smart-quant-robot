# -*- coding: utf-8 -*-
import json
import logging
from typing import Optional

import requests

from app.notifier.base import Notifier
from runtime_config import config

logger = logging.getLogger(__name__)


class DingdingNotifier(Notifier):
    """钉钉消息通知器"""

    @property
    def name(self) -> str:
        return "dingding"

    @property
    def enabled(self) -> bool:
        return config.get('dingding.enabled', True)

    def send(self, text: str, is_default: bool = True) -> bool:
        """发送钉钉消息"""
        if not self.enabled:
            logger.debug('钉钉通知未启用')
            return False

        token = config.get('dingding.token', '') if is_default else config.get('dingding.token2', '')

        if not token:
            print(f'钉钉: {text}')
            return False

        headers = {'Content-Type': 'application/json;charset=utf-8'}
        api_url = f"https://oapi.dingtalk.com/robot/send?access_token={token}"

        json_text = {
            "msgtype": "text",
            "at": {"atMobiles": [], "isAtAll": False},
            "text": {"content": f"{text}\n______"}
        }

        try:
            response = requests.post(api_url, json.dumps(json_text), headers=headers, timeout=10)
            print(f'钉钉响应: {response.content}')
            return True
        except Exception as e:
            logger.error(f'钉钉消息发送失败: {e}')
            return False
