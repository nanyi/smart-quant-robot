# 配置管理重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 authorization.py 配置合并到 runtime_config.py，支持 config.yaml 和 MySQL 两种配置源

**Architecture:** 采用单例模式配置管理类，支持 YAML 配置文件加载和 MySQL 数据库重载，优先级：MySQL > YAML > 默认值

**Tech Stack:** Python 3.7+, PyYAML, pymysql

---

## Task 1: 创建 config.yaml 配置文件

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\config.yaml`

**Step 1: 创建配置文件**

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

**Step 2: 提交**

```bash
git add config.yaml
git commit -m "feat(config): 添加 config.yaml 配置文件"
```

---

## Task 2: 创建 MySQL 初始化脚本

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\sql\init_mysql.sql`

**Step 1: 创建 SQL 脚本**

```sql
-- Smart Quant Robot 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS smart_quant DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smart_quant;

-- 币安配置表
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `api_key` VARCHAR(256) NOT NULL COMMENT '币安API密钥',
  `api_secret` VARCHAR(256) NOT NULL COMMENT '币安API私钥',
  `enabled` TINYINT DEFAULT 1 COMMENT '是否启用此配置（1=启用，0=禁用）',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='币安API配置表';

-- 插入默认配置（测试用）
INSERT INTO `binance_config` (`api_key`, `api_secret`, `enabled`) VALUES ('', '', 1);
```

**Step 2: 提交**

```bash
git add sql/init_mysql.sql
git commit -m "feat(db): 添加 MySQL 初始化脚本"
```

---

## Task 3: 重写 runtime_config.py 配置加载器

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\runtime_config.py`

**Step 1: 编写配置加载器**

```python
# -*- coding: utf-8 -*-
import os
import copy
import yaml
import pymysql
from typing import Optional, Any

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_YAML = os.path.join(REPO_ROOT, 'config.yaml')

_DEFAULT_CONFIG = {
    'binance': {
        'api_key': '',
        'api_secret': '',
        'recv_window': 5000,
        'proxy_host': '127.0.0.1',
        'proxy_port': 7890,
    },
    'dingding': {
        'token': '',
        'token2': '',
    },
    'trade': {
        'strategy': {
            'ma': {
                'short_period': 5,
                'slow_window': 60,
            }
        },
        'kLine_type': '15m',
        'binance_market': 'SPOT',
        'binance_coinBase': 'USDT',
        'binance_coinBase_count': 20,
        'binance_tradeCoin': 'DOGE',
        'isOpenSellStrategy': True,
        'sellStrategy1': {'profit': 1.05, 'sell': 0.1},
        'sellStrategy2': {'profit': 1.10, 'sell': 0.2},
        'sellStrategy3': {'profit': 1.20, 'sell': 0.2},
    },
    'mysql': {
        'enabled': False,
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'smart_quant',
        'charset': 'utf8mb4',
    },
}


def _deep_merge_dict(base: dict, override: dict) -> dict:
    """深度合并字典"""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_config(data: dict) -> dict:
    """标准化配置数据（键名小写化）"""
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for section, section_values in data.items():
        section_name = str(section).strip().lower()
        if not section_name or not isinstance(section_values, dict):
            continue
        normalized[section_name] = {}
        for key, value in section_values.items():
            normalized[section_name][str(key).strip()] = value
    return normalized


class Config:
    """全局配置单例"""
    _instance = None

    def __init__(self):
        self._config = copy.deepcopy(_DEFAULT_CONFIG)
        self._load_from_yaml()
        self._load_from_mysql()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_from_yaml(self):
        """从 YAML 文件加载配置"""
        if not os.path.exists(CONFIG_YAML):
            print(f'配置文件不存在，将创建默认配置: {CONFIG_YAML}')
            self._save_yaml(self._config)
            return

        try:
            with open(CONFIG_YAML, 'rt', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
            normalized = _normalize_config(yaml_data)
            self._config = _deep_merge_dict(self._config, normalized)
            print(f'已从 YAML 加载配置: {CONFIG_YAML}')
        except Exception as e:
            print(f'YAML 解析失败，使用默认配置: {e}')

    def _load_from_mysql(self):
        """从 MySQL 数据库加载 Binance API 配置"""
        mysql_config = self._config.get('mysql', {})
        if not mysql_config.get('enabled', False):
            print('MySQL 配置未启用，跳过从数据库加载')
            return

        try:
            connection = pymysql.connect(
                host=mysql_config.get('host', 'localhost'),
                port=int(mysql_config.get('port', 3306)),
                user=mysql_config.get('user', 'root'),
                password=mysql_config.get('password', ''),
                database=mysql_config.get('database', 'smart_quant'),
                charset=mysql_config.get('charset', 'utf8mb4'),
                connect_timeout=5
            )
            try:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        'SELECT api_key, api_secret FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
                    )
                    result = cursor.fetchone()
                    if result and result.get('api_key'):
                        self._config['binance']['api_key'] = result['api_key']
                        self._config['binance']['api_secret'] = result['api_secret']
                        print('已从 MySQL 加载 Binance API 配置')
                    else:
                        print('MySQL 中没有启用的 Binance 配置，使用 YAML 或默认配置')
            finally:
                connection.close()
        except Exception as e:
            print(f'MySQL 连接失败，使用 YAML 或默认配置: {e}')

    def _save_yaml(self, data: dict):
        """保存配置到 YAML 文件"""
        try:
            with open(CONFIG_YAML, 'wt', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f'保存 YAML 配置失败: {e}')

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号路径
        例如: config.get('binance.api_key')
        """
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value if value is not None else default

    def set(self, key_path: str, value: Any):
        """设置配置值，支持点号路径"""
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value


config = Config.get_instance()
```

**Step 2: 提交**

```bash
git add runtime_config.py
git commit -m "feat(config): 重写配置加载器，支持YAML和MySQL"
```

---

## Task 4: 修改 BinanceAPI.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\app\BinanceAPI.py`

**Step 1: 修改导入和初始化**

修改前：
```python
from app.authorization import recv_window
```

修改后：
```python
from runtime_config import config
```

修改 BinanceAPI.__init__ 方法：
```python
def __init__(self, key=None, secret=None, proxy_host=None, proxy_port=None):
    self.key = key if key is not None else config.get('binance.api_key', '')
    self.secret = secret if secret is not None else config.get('binance.api_secret', '')
    proxy_host = proxy_host or config.get('binance.proxy_host', '127.0.0.1')
    proxy_port = proxy_port or config.get('binance.proxy_port', 7890)
    self.proxies = {
        "http": f"http://{proxy_host}:{proxy_port}",
        "https": f"http://{proxy_host}:{proxy_port}",
    }
```

修改 recv_window 使用：
找到 `recv_window` 的使用，改为 `config.get('binance.recv_window', 5000)`

**Step 2: 提交**

```bash
git add app/BinanceAPI.py
git commit -m "refactor: BinanceAPI改用runtime_config获取配置"
```

---

## Task 5: 修改 OrderManager.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\app\OrderManager.py`

**Step 1: 修改导入**

修改前：
```python
from runtime_config import sellStrategy1, sellStrategy2, sellStrategy3, short_period, long_period, isOpenSellStrategy, kLine_type
```

修改后：
```python
from runtime_config import config
```

**Step 2: 修改使用方式**

需要修改的地方：
- `sellStrategy1` → `config.get('trade.sellStrategy1')`
- `sellStrategy2` → `config.get('trade.sellStrategy2')`
- `sellStrategy3` → `config.get('trade.sellStrategy3')`
- `short_period` → `config.get('trade.strategy.ma.short_period', 5)`
- `long_period` → `config.get('trade.strategy.ma.long_period', 60)`
- `isOpenSellStrategy` → `config.get('trade.isOpenSellStrategy', False)`
- `kLine_type` → `config.get('trade.kLine_type', '15m')`

**Step 3: 提交**

```bash
git add app/OrderManager.py
git commit -m "refactor: OrderManager改用runtime_config获取配置"
```

---

## Task 6: 修改 main.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\main.py`

**Step 1: 修改导入和初始化**

修改 BinanceAPI 初始化，移除硬编码的 api_key/api_secret：
```python
binan = BinanceAPI()
```

修改 OrderManager 初始化，使用配置：
```python
orderManager_doge = OrderManager(
    config.get('trade.binance_coinBase', 'USDT'),
    config.get('trade.binance_coinBase_count', 20),
    config.get('trade.binance_tradeCoin', 'DOGE'),
    config.get('trade.binance_market', 'SPOT')
)
```

**Step 2: 提交**

```bash
git add main.py
git commit -m "refactor: main.py改用runtime_config获取配置"
```

---

## Task 7: 更新 requirements.txt

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\requirements.txt`

**Step 1: 添加依赖**

```
pymysql>=1.0.0
pyyaml>=6.0
schedule>=1.0.0
requests>=2.25.0
pandas>=1.2.0
```

**Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: 添加pymysql和pyyaml依赖"
```

---

## Task 8: 删除 authorization.py

**Files:**
- Delete: `E:\projects\sumiz-projects\smart-quant-robot\app\authorization.py`

**Step 1: 删除文件并提交**

```bash
rm app/authorization.py
git add -A
git commit -m "refactor: 删除authorization.py，配置已合并到runtime_config"
```

---

## Task 9: 更新 AGENTS.md

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\AGENTS.md`

**Step 1: 添加配置管理规范**

在文档中添加：
- config.yaml 配置说明
- MySQL 配置说明
- 配置加载优先级

**Step 2: 提交**

```bash
git add AGENTS.md
git commit -m "docs: 更新AGENTS.md配置管理规范"
```

---

## 验证测试

完成所有任务后，执行以下验证：

1. **YAML 配置测试**：
   - 设置 config.yaml 中的 api_key/api_secret
   - 确保 mysql.enabled = false
   - 运行程序，检查是否使用 YAML 配置

2. **MySQL 重载测试**：
   - 配置 MySQL 并插入 API 密钥
   - 设置 mysql.enabled = true
   - 运行程序，检查是否从 MySQL 加载配置

---

**计划完成，所有任务已提交到 Git。**