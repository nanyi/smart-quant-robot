# 钉钉通知配置管理重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 钉钉配置支持 MySQL 重载，增加 enabled 控制开关

**Architecture:** 在现有配置加载流程中增加 dingding 配置的数据库读取，dingding.py 开头增加 enabled 检查

**Tech Stack:** Python 3.7+, pymysql, PyYAML

---

## Task 1: 更新 SQL 初始化脚本

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\sql\init_mysql.sql`

**Step 1: 修改 SQL 脚本**

在 `binance_config` 表中增加钉钉字段：

```sql
-- 币安配置表
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `api_key` VARCHAR(256) NOT NULL COMMENT '币安API密钥',
  `api_secret` VARCHAR(256) NOT NULL COMMENT '币安API私钥',
  `dingding_token` VARCHAR(256) DEFAULT '' COMMENT '钉钉主token',
  `dingding_token2` VARCHAR(256) DEFAULT '' COMMENT '钉钉备用token',
  `enabled` TINYINT DEFAULT 1 COMMENT '是否启用此配置（1=启用，0=禁用）',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='币安API配置表';

-- 插入默认配置（测试用）
INSERT INTO `binance_config` (`api_key`, `api_secret`, `dingding_token`, `dingding_token2`, `enabled`) VALUES ('', '', '', '', 1);
```

**Step 2: 提交**

```bash
git add sql/init_mysql.sql
git commit -m "feat(db: 增加dingding_token和dingding_token2字段"
```

---

## Task 2: 更新 runtime_config.py 默认配置

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\runtime_config.py`

**Step 1: 修改默认配置**

找到 `_DEFAULT_CONFIG` 中的 `dingding` 部分，添加 `enabled` 字段：

```python
'dingding': {
    'enabled': True,
    'token': '',
    'token2': '',
},
```

**Step 2: 修改 _load_from_mysql 方法**

在 SQL 查询中增加 dingding_token 和 dingding_token2 的读取：

找到：
```python
cursor.execute(
    'SELECT api_key, api_secret FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
)
result = cursor.fetchone()
if result and result.get('api_key'):
    self._config['binance']['api_key'] = result['api_key']
    self._config['binance']['api_secret'] = result['api_secret']
```

改为：
```python
cursor.execute(
    'SELECT api_key, api_secret, dingding_token, dingding_token2 FROM binance_config WHERE enabled = 1 ORDER BY id DESC LIMIT 1'
)
result = cursor.fetchone()
if result:
    if result.get('api_key'):
        self._config['binance']['api_key'] = result['api_key']
        self._config['binance']['api_secret'] = result['api_secret']
    if result.get('dingding_token') is not None:
        self._config['dingding']['token'] = result['dingding_token']
    if result.get('dingding_token2') is not None:
        self._config['dingding']['token2'] = result['dingding_token2']
```

**Step 3: 提交**

```bash
git add runtime_config.py
git commit -m "feat(config): dingding配置支持MySQL重载"
```

---

## Task 3: 更新 config.yaml

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\config.yaml`

**Step 1: 修改配置**

在 `dingding` 部分添加 `enabled` 字段：

```yaml
dingding:
  enabled: true
  token: ""
  token2: ""
```

**Step 2: 提交**

```bash
git add config.yaml
git commit -m "feat(config): dingding配置增加enabled开关"
```

---

## Task 4: 修改 dingding.py

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\app\dingding.py`

**Step 1: 修改 dingding_warn 方法**

在方法开头添加 enabled 检查：

```python
def dingding_warn(self, text, isDefaultToken=True):
    """
    发送钉钉告警消息
    ...
    """
    # 钉钉通知未启用，直接返回
    if not config.get('dingding.enabled', True):
        return
    
    tmpToken = config.get('dingding.token', '') if isDefaultToken else config.get('dingding.token2', '')
    # ... 后续逻辑保持不变
```

**Step 2: 提交**

```bash
git add app/dingding.py
git commit -m "feat(dingding): 增加enabled开关控制"
```

---

## Task 5: 更新 AGENTS.md

**Files:**
- Modify: `E:\projects\sumiz-projects\smart-quant-robot\AGENTS.md`

**Step 1: 更新配置管理规范**

在第8节配置管理规范中，更新 dingding 配置结构：

```yaml
dingding:
  enabled: true      # 是否开启钉钉通知
  token: ""          # 钉钉群Token（告警）
  token2: ""         # 钉钉群Token（交易）
```

**Step 2: 提交**

```bash
git add AGENTS.md
git commit -m "docs: 更新AGENTS.md钉钉配置说明"
```

---

## 验证测试

1. 确认 config.yaml 中 `dingding.enabled: false` 时，钉钉消息不发送
2. 确认从 MySQL 加载后，dingding_token 和 dingding_token2 正确覆盖 config.yaml 配置