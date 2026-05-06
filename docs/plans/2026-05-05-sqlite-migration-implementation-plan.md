# MySQL 转 SQLite 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 将配置存储从 MySQL 改为 SQLite，简化部署并支持多线程读写

**Architecture:** 使用 sqlite3 库替代 pymysql，配置加载器新增 `_load_from_sqlite()` 方法

**Tech Stack:** Python 3.7+, sqlite3（标准库）

---

## Task 1: 创建 SQLite 初始化脚本

**Files:**
- Create: `E:\projects\sumiz-projects\smart-quant-robot\sql\init_sqlite.sql`

**Step 1: 创建 SQL 脚本**

```sql
-- Smart Quant Robot SQLite 数据库初始化脚本
-- 数据库文件保存在 /data/db/smart_quant_robot.db

-- 确保目录存在（在应用启动时创建）
-- CREATE DATABASE IF NOT EXISTS 不适用于 SQLite

-- 币安配置表
CREATE TABLE IF NOT EXISTS binance_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key VARCHAR(256) NOT NULL,
    api_secret VARCHAR(256) NOT NULL,
    dingding_token VARCHAR(256) DEFAULT '',
    dingding_token2 VARCHAR(256) DEFAULT '',
    enabled INTEGER DEFAULT 1,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置（测试用）
INSERT OR IGNORE INTO binance_config (id, api_key, api_secret, dingding_token, dingding_token2, enabled) 
VALUES (1, '', '', '', '', 1);
```

**Step 2: 提交**

```bash
git add sql/init_sqlite.sql
git commit -m "feat(db): 添加SQLite初始化脚本"
```

---

## Task 2: 更新 runtime_config.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\runtime_config.py`

**Step 1: 修改导入**

将：
```python
import pymysql
```

改为：
```python
import sqlite3
import os
```

**Step 2: 修改默认配置**

将：
```python
'mysql': {
    'enabled': False,
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'smart_quant',
    'charset': 'utf8mb4',
},
```

改为：
```python
'sqlite': {
    'enabled': False,
    'db_path': './data/db/smart_quant_robot.db',
},
```

**Step 3: 修改配置加载方法**

将 `_load_from_mysql()` 方法改为 `_load_from_sqlite()`：

```python
def _load_from_sqlite(self):
    """从 SQLite 数据库加载 Binance API 配置"""
    sqlite_config = self._config.get('sqlite', {})
    if not sqlite_config.get('enabled', False):
        print('SQLite 配置未启用，跳过从数据库加载')
        return

    db_path = sqlite_config.get('db_path', './data/db/smart_quant_robot.db')
    
    # 确保目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f'创建数据库目录: {db_dir}')

    # 如果数据库文件不存在，先创建
    if not os.path.exists(db_path):
        print(f'数据库文件不存在，将创建: {db_path}')
        self._init_sqlite_db(db_path)
        return

    try:
        connection = sqlite3.connect(db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute(
                'SELECT api_key, api_secret, dingding_token, dingding_token2 FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
            )
            result = cursor.fetchone()
            if result:
                if result['api_key']:
                    self._config['binance']['api_key'] = result['api_key']
                    self._config['binance']['api_secret'] = result['api_secret']
                    print('已从 SQLite 加载 Binance API 配置')
                if result['dingding_token'] is not None:
                    self._config['dingding']['token'] = result['dingding_token']
                    print('已从 SQLite 加载钉钉配置')
                if result['dingding_token2'] is not None:
                    self._config['dingding']['token2'] = result['dingding_token2']
            else:
                print('SQLite 中没有启用的 Binance 配置，使用 YAML 或默认配置')
        finally:
            connection.close()
    except Exception as e:
        print(f'SQLite 连接失败，使用 YAML 或默认配置: {e}')

def _init_sqlite_db(self, db_path):
    """初始化 SQLite 数据库"""
    try:
        connection = sqlite3.connect(db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS binance_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key VARCHAR(256) NOT NULL,
                    api_secret VARCHAR(256) NOT NULL,
                    dingding_token VARCHAR(256) DEFAULT '',
                    dingding_token2 VARCHAR(256) DEFAULT '',
                    enabled INTEGER DEFAULT 1,
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute(
                "INSERT OR IGNORE INTO binance_config (id, api_key, api_secret, dingding_token, dingding_token2, enabled) VALUES (1, '', '', '', '', 1)"
            )
            connection.commit()
            print(f'SQLite 数据库初始化完成: {db_path}')
        finally:
            connection.close()
    except Exception as e:
        print(f'SQLite 数据库初始化失败: {e}')
```

**Step 4: 修改 __init__ 方法**

将 `self._load_from_mysql()` 改为 `self._load_from_sqlite()`

**Step 2: 提交**

```bash
git add runtime_config.py
git commit -m "refactor: 将MySQL改为SQLite配置加载"
```

---

## Task 3: 更新 config.yaml

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\config.yaml`

**Step 1: 修改配置**

将：
```yaml
mysql:
  enabled: true
  host: "localhost"
  port: 3306
  user: "root"
  password: "rootroot"
  database: "smart_quant_robot"
  charset: "utf8mb4"
```

改为：
```yaml
sqlite:
  enabled: true
  db_path: "/data/db/smart_quant_robot.db"
```

**Step 2: 提交**

```bash
git add config.yaml
git commit -m "feat(config): MySQL配置改为SQLite配置"
```

---

## Task 4: 更新 requirements.txt

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\requirements.txt`

**Step 1: 移除 pymysql**

从依赖列表中删除 `pymysql>=1.0.0`

**Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: 移除pymysql依赖（SQLite使用标准库）"
```

---

## Task 5: 更新 AGENTS.md

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\AGENTS.md`

**Step 1: 更新配置管理规范**

将第8.1节中的 mysql 配置改为 sqlite 配置：
```yaml
sqlite:
  enabled: true
  db_path: "/data/db/smart_quant_robot.db"
```

**Step 2: 提交**

```bash
git add AGENTS.md
git commit -m "docs: 更新AGENTS.md添加SQLite配置说明"
```

---

## 验证测试

1. 设置 `sqlite.enabled: true`，确认从 SQLite 加载配置
2. 设置 `sqlite.enabled: false`，确认跳过数据库加载
3. 多线程环境下数据库访问正常（无锁冲突）