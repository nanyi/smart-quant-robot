# 配置管理重构设计方案

## 1. 背景与目标

将 `authorization.py` 的配置项合并到 `runtime_config.py`，并支持：
- 从 `config.yaml` 配置文件加载
- 启动时从 MySQL 数据库重载 Binance API 密钥

## 2. 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| YAML解析 | PyYAML | 配置文件加载 |
| MySQL客户端 | pymysql | 直接操作SQL，轻量 |
| 配置存储 | 全局单例 | runtime_config 全局配置对象 |

## 3. 配置结构

### 3.1 config.yaml

```yaml
binance:
  api_key: ""
  api_secret: ""
  recv_window: 5000
  proxy_host: "127.0.0.1"
  proxy_port: 7890

dingding:
  token: ""
  token2: ""

trade:
  strategy:
    ma:
      short_period: 5
      long_period: 60
  kLine_type: '15m'
  binance_market: "SPOT"
  binance_coinBase: "USDT"
  binance_coinBase_count: 20
  binance_tradeCoin: "DOGE"
  isOpenSellStrategy: true
  sellStrategy1:
    profit: 1.05
    sell: 0.1
  sellStrategy2:
    profit: 1.10
    sell: 0.2
  sellStrategy3:
    profit: 1.20
    sell: 0.2

mysql:
  enabled: false
  host: "localhost"
  port: 3306
  user: "root"
  password: ""
  database: "smart_quant"
  charset: "utf8mb4"
```

### 3.2 MySQL表结构

```sql
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `api_key` VARCHAR(256) NOT NULL COMMENT '币安API密钥',
  `api_secret` VARCHAR(256) NOT NULL COMMENT '币安API私钥',
  `enabled` TINYINT DEFAULT 1 COMMENT '是否启用此配置',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 4. 配置加载优先级

1. **MySQL数据库**（如果 enabled=true 且有数据）> **config.yaml** > **默认值**

## 5. 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `config.yaml` | 新建 | 配置文件 |
| `runtime_config.py` | 重写 | 配置加载器 |
| `app/authorization.py` | 删除 | 配置已合并 |
| `app/BinanceAPI.py` | 修改 | 移除 recv_window 导入，改为从配置读取 |
| `main.py` | 修改 | 适配新的配置方式 |
| `requirements.txt` | 修改 | 添加依赖 |

## 6. 实现细节

### 6.1 runtime_config.py 结构

```python
# -*- coding: utf-8 -*-
import os, yaml, pymysql
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_YAML = os.path.join(REPO_ROOT, 'config.yaml')

class Config:
    """全局配置单例"""
    _instance = None
    
    def __init__(self):
        self._config = {}
        self._load_yaml()
        self._load_from_mysql()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_yaml(self):
        # 加载 config.yaml
        
    def _load_from_mysql(self):
        # 从MySQL加载API密钥
    
    def get(self, key, default=None):
        # 获取配置值

config = Config.get_instance()
```

### 6.2 修改 BinanceAPI.py

- 移除 `from app.authorization import recv_window`
- 改为 `from runtime_config import config`
- 使用 `config.get('binance.recv_window', 5000)`

### 6.3 修改 OrderManager.py

- 移除 `from runtime_config import ...`
- 改为 `from runtime_config import config`

## 7. 错误处理

- MySQL连接失败：记录日志，使用 config.yaml 配置
- 配置项不存在：使用默认值
- YAML解析失败：使用默认配置

## 8. 测试验证

1. 仅 config.yaml 配置时正常启动
2. 配置 MySQL 后启动时 API 密钥正确重载
3. 网络异常时能降级到 config.yaml