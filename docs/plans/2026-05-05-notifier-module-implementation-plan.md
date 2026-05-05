# 消息通知模块重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 重构消息通知模块，支持钉钉和企业微信，通过配置选择通知渠道

**Architecture:** 创建 notifier 包，包含基类、钉钉实现、企业微信实现和工厂函数

**Tech Stack:** Python 3.7+, requests, queue, threading

---

## Task 1: 创建 notifier 模块目录

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\app\notifier\__init__.py`

**Step 1: 创建模块目录和 __init__.py**

```python
# -*- coding: utf-8 -*-
"""
消息通知模块

支持钉钉和企业微信通知，通过配置选择通知渠道
"""
from app.notifier.factory import get_notifier

__all__ = ['get_notifier']
```

**Step 2: 提交**

```bash
git add app/notifier/__init__.py
git commit -m "feat(notifier): 创建notifier模块目录"
```

---

## Task 2: 创建 Notifier 基类

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\app\notifier\base.py`

**Step 1: 创建基类**

```python
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
        :param is_default: 是否使用主配置（True用token，False用备用）
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
```

**Step 2: 提交**

```bash
git add app/notifier/base.py
git commit -m "feat(notifier): 添加Notifier基类"
```

---

## Task 3: 创建钉钉通知器

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\app\notifier\dingding.py`

**Step 1: 创建钉钉通知器**

```python
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

    def __init__(self):
        self._token = ''
        self._token2 = ''

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
```

**Step 2: 提交**

```bash
git add app/notifier/dingding.py
git commit -m "feat(notifier): 添加DingdingNotifier钉钉通知器"
```

---

## Task 4: 创建企业微信通知器

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\app\notifier\weixin.py`

**Step 1: 创建企业微信通知器**

```python
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
```

**Step 2: 提交**

```bash
git add app/notifier/weixin.py
git commit -m "feat(notifier): 添加WeixinNotifier企业微信通知器"
```

---

## Task 5: 创建工厂函数

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\app\notifier\factory.py`

**Step 1: 创建工厂函数**

```python
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
```

**Step 2: 更新 __init__.py**

```python
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
```

**Step 3: 提交**

```bash
git add app/notifier/factory.py app/notifier/__init__.py
git commit -m "feat(notifier): 添加get_notifier工厂函数"
```

---

## Task 6: 更新 runtime_config.py 默认配置

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\runtime_config.py`

**Step 1: 添加 notifier 和 weixin 默认配置**

在 _DEFAULT_CONFIG 中添加：

```python
'notifier': {
    'enabled': True,
    'provider': 'dingding',  # dingding | weixin
},
'weixin': {
    'enabled': False,
    'corp_id': '',
    'secret': '',
    'agent_id': 0,
    'to_user': '@all',
},
```

**Step 2: 提交**

```bash
git add runtime_config.py
git commit -m "feat(config): 添加notifier和weixin默认配置"
```

---

## Task 7: 更新 config.yaml

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\config.yaml`

**Step 1: 添加配置**

```yaml
notifier:
  enabled: true
  provider: "dingding"  # dingding | weixin

dingding:
  enabled: true
  token: ""
  token2: ""

weixin:
  enabled: false
  corp_id: ""
  secret: ""
  agent_id: 0
  to_user: "@all"
```

**Step 2: 提交**

```bash
git add config.yaml
git commit -m "feat(config): 添加notifier和weixin配置"
```

---

## Task 8: 更新 SQL 初始化脚本

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\sql\init_mysql.sql`

**Step 1: 添加企业微信字段**

```sql
ALTER TABLE `binance_config` 
ADD COLUMN `weixin_enabled` TINYINT DEFAULT 0 COMMENT '是否启用企业微信',
ADD COLUMN `weixin_corp_id` VARCHAR(128) DEFAULT '' COMMENT '企业微信CorpID',
ADD COLUMN `weixin_secret` VARCHAR(256) DEFAULT '' COMMENT '企业微信Secret',
ADD COLUMN `weixin_agent_id` INT DEFAULT 0 COMMENT '企业微信AgentID',
ADD COLUMN `weixin_to_user` VARCHAR(64) DEFAULT '@all' COMMENT '企业微信ToUser';
```

**Step 2: 提交**

```bash
git add sql/init_mysql.sql
git commit -m "feat(db): binance_config表增加企业微信字段"
```

---

## Task 9: 修改 OrderManager.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\app\OrderManager.py`

**Step 1: 修改导入和使用**

找到：

```python
from app.notifier.dingding import Message

msg = Message()
```

改为：
```python
from app.notifier import get_notifier
msg = get_notifier()
```

**Step 2: 提交**

```bash
git add app/OrderManager.py
git commit -m "refactor: OrderManager改用新的notifier模块"
```

---

## Task 10: 更新 main.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\main.py`

**Step 1: 检查并修改钉钉相关导入**

如果 main.py 中有 `from app.dingding import Message`，改为从 notifier 导入

**Step 2: 提交**

```bash
git add main.py
git commit -m "refactor: main.py改用新的notifier模块"
```

---

## Task 11: 删除旧的 dingding.py

**Files:**
- Delete: `E:\projects\sumiz-projects\smart-quant-robot\app\dingding.py`

**Step 1: 删除并提交**

```bash
git add -A
git commit -m "refactor: 删除旧的dingding.py，由notifier模块替代"
```

---

## Task 12: 更新 AGENTS.md

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\AGENTS.md`

**Step 1: 添加 notifier 模块说明**

在配置管理规范中添加：

```yaml
notifier:
  enabled: true
  provider: "dingding"  # dingding | weixin

weixin:
  enabled: false
  corp_id: ""
  secret: ""
  agent_id: 0
  to_user: "@all"
```

**Step 2: 提交**

```bash
git add AGENTS.md
git commit -m "docs: 更新AGENTS.md添加notifier模块说明"
```

---

## 验证测试

1. 设置 `notifier.provider: "dingding"` 时，使用钉钉通知
2. 设置 `notifier.provider: "weixin"` 且配置完整时，使用企业微信通知
3. 设置 `dingding.enabled: false` 时，不发送钉钉消息
4. 多个订单管理器共享同一个 notifier 实例