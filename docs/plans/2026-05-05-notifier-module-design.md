# 消息通知模块重构设计方案

## 1. 背景与目标

将现有的钉钉通知重构为可扩展的消息通知框架，支持通过配置选择使用钉钉或企业微信，并为未来扩展其他通知渠道预留接口。

## 2. 架构设计

### 2.1 目录结构

```
app/notifier/
├── __init__.py
├── base.py           # 通知器基类
├── dingding.py      # 钉钉实现
├── weixin.py        # 企业微信实现
└── factory.py       # 通知器工厂
```

### 2.2 类图

```
Notifier (ABC)
├── name: str
├── enabled: bool
├── send(text, is_default) -> bool
├── start()
├── stop()
└── enqueue(text)

    ├── DingdingNotifier
    └── WeixinNotifier
```

## 3. 基类接口

### 3.1 Notifier 基类

```python
from abc import ABC, abstractmethod

class Notifier(ABC):
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
        """发送消息"""
        pass
    
    def start(self):
        """启动通知器（用于异步通知器初始化）"""
        pass
    
    def stop(self):
        """停止通知器"""
        pass
    
    def enqueue(self, text: str):
        """加入发送队列"""
        pass
```

## 4. 配置结构

### 4.1 config.yaml

```yaml
notifier:
  enabled: true
  provider: "dingding"  # 通知渠道：dingding | weixin

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

### 4.2 MySQL 表结构扩展

```sql
ALTER TABLE `binance_config` 
ADD COLUMN `weixin_enabled` TINYINT DEFAULT 0 COMMENT '是否启用企业微信',
ADD COLUMN `weixin_corp_id` VARCHAR(128) DEFAULT '' COMMENT '企业微信CorpID',
ADD COLUMN `weixin_secret` VARCHAR(256) DEFAULT '' COMMENT '企业微信Secret',
ADD COLUMN `weixin_agent_id` INT DEFAULT 0 COMMENT '企业微信AgentID',
ADD COLUMN `weixin_to_user` VARCHAR(64) DEFAULT '@all' COMMENT '企业微信ToUser';
```

## 5. 实现细节

### 5.1 钉钉通知器 (DingdingNotifier)

- 同步发送消息（简单Webhook接口）
- 支持 token/token2 双token
- 检查 enabled 配置决定是否发送

### 5.2 企业微信通知器 (WeixinNotifier)

- 异步队列发送
- AccessToken 管理（自动刷新）
- 线程安全

### 5.3 工厂函数

```python
def get_notifier() -> Notifier:
    """根据配置创建对应的通知器"""
    provider = config.get('notifier.provider', 'dingding')
    if provider == 'weixin':
        return WeixinNotifier()
    return DingdingNotifier()
```

## 6. 影响范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/notifier/__init__.py` | 新建 | 模块入口 |
| `app/notifier/base.py` | 新建 | 基类定义 |
| `app/notifier/dingding.py` | 新建 | 钉钉实现 |
| `app/notifier/weixin.py` | 新建 | 企业微信实现 |
| `app/notifier/factory.py` | 新建 | 工厂函数 |
| `app/dingding.py` | 删除 | 重构后移除 |
| `app/OrderManager.py` | 修改 | 适配新通知器 |
| `runtime_config.py` | 修改 | 增加 notifier 配置 |
| `config.yaml` | 修改 | 增加 notifier 配置 |
| `sql/init_mysql.sql` | 修改 | 增加企业微信字段 |
| `AGENTS.md` | 修改 | 更新文档 |

## 7. 使用示例

```python
from app.notifier import get_notifier

# 获取通知器（根据配置自动选择）
notifier = get_notifier()

# 发送消息
notifier.send("买入成功：BTCUSDT 数量 0.1")
notifier.send("告警：网络异常", is_default=False)  # 使用备用token
```