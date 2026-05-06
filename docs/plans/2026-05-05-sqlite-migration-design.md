# 数据库从 MySQL 改为 SQLite 设计方案

## 1. 背景与目标

将配置存储从 MySQL 改为 SQLite，简化部署（无需独立数据库服务），并支持多线程读写。

## 2. 数据库配置

### 2.1 config.yaml

```yaml
sqlite:
  enabled: true
  db_path: "/data/db/smart_quant_robot.db"
```

### 2.2 目录结构

```
smart-quant-robot/
├── data/
│   └── db/                    # 数据库目录
│       └── smart_quant_robot.db
└── sql/
    └── init_sqlite.sql        # SQLite 初始化脚本
```

## 3. SQLite 多线程支持

SQLite 默认单线程访问，需要配置 `check_same_thread=False` 以支持多线程读写：

```python
import sqlite3

conn = sqlite3.connect(db_path, check_same_thread=False)
conn.row_factory = sqlite3.Row
```

## 4. 表结构

```sql
CREATE TABLE IF NOT EXISTS binance_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key VARCHAR(256) NOT NULL,
    api_secret VARCHAR(256) NOT NULL,
    dingding_token VARCHAR(256) DEFAULT '',
    dingding_token2 VARCHAR(256) DEFAULT '',
    enabled INTEGER DEFAULT 1,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 5. 影响范围

| 文件 | 操作 | 说明 |
|------|------|------|
| `runtime_config.py` | 修改 | pymysql → sqlite3，`_load_from_sqlite()` |
| `config.yaml` | 修改 | mysql → sqlite 配置 |
| `sql/init_sqlite.sql` | 新建 | SQLite 初始化脚本 |
| `requirements.txt` | 修改 | 移除 pymysql |
| `AGENTS.md` | 修改 | 更新文档 |

## 6. 配置加载优先级

1. **SQLite 数据库**（如果 enabled=true 且存在）> **config.yaml** > **默认值**