# 钉钉通知配置管理重构设计方案

## 1. 背景与目标

将钉钉通知配置（token、token2）也纳入 MySQL 数据库管理，并增加 `enabled` 配置项控制是否开启钉钉通知功能。

## 2. 数据库变更

### 2.1 修改 binance_config 表

在现有表中增加钉钉相关字段：

```sql
ALTER TABLE `binance_config` 
ADD COLUMN `dingding_token` VARCHAR(256) DEFAULT '' COMMENT '钉钉主token',
ADD COLUMN `dingding_token2` VARCHAR(256) DEFAULT '' COMMENT '钉钉备用token';
```

## 3. 配置结构变更

### 3.1 config.yaml

```yaml
dingding:
  enabled: true      # 是否开启钉钉通知
  token: ""
  token2: ""
```

### 3.2 默认配置

```python
'dingding': {
    'enabled': True,
    'token': '',
    'token2': '',
},
```

## 4. runtime_config.py 变更

在 `_load_from_mysql()` 方法中，从 `binance_config` 表同时读取：
- `api_key`, `api_secret`（已有）
- `dingding_token`, `dingding_token2`（新增）

## 5. dingding.py 变更

在 `dingding_warn` 方法开头增加检查：

```python
def dingding_warn(self, text, isDefaultToken=True):
    # 钉钉通知未启用，直接返回
    if not config.get('dingding.enabled', True):
        return
    # ... 后续逻辑
```

## 6. 优先级

配置加载顺序：MySQL > config.yaml > 默认值

## 7. 影响范围

| 文件 | 变更 |
|------|------|
| sql/init_mysql.sql | 增加 ALTER TABLE 语句 |
| runtime_config.py | 增加 dingding 配置重载逻辑 |
| config.yaml | 增加 enabled 字段 |
| dingding.py | 增加 enabled 检查 |
| AGENTS.md | 更新配置管理规范 |