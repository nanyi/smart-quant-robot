# -*- coding: utf-8 -*-
import atexit
import logging
import queue
import threading
import time
from typing import Optional

import requests

from app.notifier.base import Notifier
from runtime_config import config

logger = logging.getLogger(__name__)


class WeixinNotifier(Notifier):
    """企业微信消息通知器"""

    def __init__(self):
        self._corp_id = config.get('weixin.corp_id', '').strip()
        self._secret = config.get('weixin.secret', '').strip()
        self._agent_id = config.get('weixin.agent_id', 0)
        self._to_user = config.get('weixin.to_user', '@all').strip() or '@all'
        self._token: Optional[str] = None
        self._token_expire_at = 0.0
        self._queue: queue.Queue[str] = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return "weixin"

    @property
    def enabled(self) -> bool:
        return bool(self._corp_id and self._secret)

    def start(self):
        """启动通知器"""
        if not self.enabled:
            logger.info('企业微信推送未启用：缺少 weixin.CorpID 或 weixin.Secret')
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name='weixin-notifier', daemon=True)
        self._thread.start()
        atexit.register(self.stop)

    def stop(self):
        """停止通知器"""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def enqueue(self, text: str):
        """加入发送队列"""
        if not self.enabled:
            return
        text = (text or '').strip()
        if not text:
            return
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            self._queue.put_nowait(text)

    def send(self, text: str, is_default: bool = True) -> bool:
        """发送企业微信消息"""
        if not self.enabled:
            logger.debug('企业微信通知未启用')
            return False
        try:
            self._send_text(text)
            return True
        except Exception as e:
            logger.error(f'企业微信消息发送失败: {e}')
            return False

    def _run(self):
        """异步发送线程"""
        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._send_text(message)
            except Exception as e:
                logger.warning('企业微信消息发送失败: %s', repr(e))

    def _get_access_token(self) -> str:
        """获取AccessToken"""
        now = time.time()
        if self._token and now < self._token_expire_at - 60:
            return self._token

        resp = requests.get(
            'https://qyapi.weixin.qq.com/cgi-bin/gettoken',
            params={'corpid': self._corp_id, 'corpsecret': self._secret},
            timeout=10,
        )
        data = resp.json()
        err_code = data.get('errcode', -1)
        if err_code != 0:
            raise RuntimeError(f'gettoken failed: errcode={err_code}, errmsg={data.get("errmsg", "")}')

        token = str(data.get('access_token', '') or '').strip()
        if not token:
            raise RuntimeError('gettoken failed: empty access_token')

        self._token = token
        expires_in = int(data.get('expires_in', 7200) or 7200)
        self._token_expire_at = now + expires_in
        return token

    def _send_text(self, text: str):
        """发送文本消息"""
        token = self._get_access_token()
        payload = {
            'touser': self._to_user,
            'msgtype': 'text',
            'agentid': self._agent_id,
            'text': {'content': text},
            'safe': 0,
        }
        resp = requests.post(
            f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}',
            json=payload,
            timeout=10,
        )
        data = resp.json()
        err_code = data.get('errcode', -1)
        if err_code != 0:
            raise RuntimeError(f'send message failed: errcode={err_code}, errmsg={data.get("errmsg", "")}')
