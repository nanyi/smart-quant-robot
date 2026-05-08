# 交互语言要求

1. **强制使用中文**：所有回答、思考过程、输出内容必须使用中文
2. **代码除外**：代码本身和特殊专有名词（如类名、方法名、API 名称）使用英文
3. **展示思考过程**：在回答问题时，需要展示分析和推理过程

---

# Smart Quant Robot 开发指南

## 1. 项目概述

Smart Quant Robot 是一个基于 Binance 交易所的数字货币量化交易系统，采用双均线交易策略（金叉买入、死叉卖出）实现自动化交易。

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        主程序层 (Main)                               │
│  main.py - 程序入口，定时任务调度                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  订单管理     │          │  交易策略     │          │  通知服务     │
│  OrderManager │          │  DoubleAvg    │          │  DingDing     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  BinanceAPI   │          │  Pandas       │          │  Schedule     │
│  币安接口封装  │          │  数据分析     │          │  定时任务      │
└───────────────┘          └───────────────┘          └───────────────┘
```

### 1.2 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| Python | Python | 3.7+ |
| 数据分析 | Pandas | - |
| 交易所API | Binance API | - |
| 通知 | 钉钉自定义机器人 | - |
| 定时任务 | Schedule | - |

### 1.3 目录结构

```
smart-quant-robot/
├── app/
│   ├── __init__.py
│   ├── authorization.py    # API密钥配置
│   ├── BinanceAPI.py       # 币安API封装
│   ├── dingding.py         # 钉钉通知
│   └── OrderManager.py     # 订单管理器（核心业务逻辑）
├── strategy/
│   ├── __init__.py
│   └── DoubleAverageLinesStrategy.py  # 双均线策略
├── runtime_config.py        # 运行时配置（策略参数、交易对等）
├── main.py                 # 程序入口
├── AGENTS.md               # 开发规范
└── README.md               # 项目说明
```

### 1.4 功能模块

| 模块ID | 模块名称 | 说明 |
|--------|----------|------|
| MOD-001 | BinanceAPI | 币安交易所API封装，订单操作、行情查询 |
| MOD-002 | OrderManager | 订单生命周期管理，买入/卖出/持久化 |
| MOD-003 | DoubleAverageLinesStrategy | 双均线策略实现，金叉死叉信号识别 |
| MOD-004 | DingDingNotification | 钉钉机器人通知，交易状态推送 |

---

## 2. 代码规范

### Python (项目主语言)

- **Python 版本**: 3.7+
- **编码**: UTF-8 (# -*- coding: utf-8 -*-)
- **命名规范**:
  - 类：CamelCase（如 `OrderManager`、`ExchangeRule`）
  - 函数/变量：snake_case（如 `get_spot_asset_by_symbol`）
  - 常量：UPPER_SNAKE_CASE（如 `API_KEY`）
- **文档字符串**：使用中文 docstring，详细说明参数和返回值
- **类型提示**：建议添加类型注解

### 文件头部注释

每个 Python 文件应包含：

```python
# -*- coding: utf-8 -*-
# @Time    : YYYY/MM/DD HH:MM
# @Author  : Ryan
```

### 导入规则

```python
# 标准库
import json, os, time, datetime, math
import traceback

# 第三方库
import pandas as pd

# 本地导入（按相对路径分组）
from app.BinanceAPI import BinanceAPI
from app.authorization import api_key, api_secret
```

### 类设计规范

- 所有类应有中文 docstring 说明功能
- 方法必须包含完整的 docstring（参数说明、返回值说明）
- 公开方法在上，私有方法在下

### 代码格式

- 缩进：4 空格
- 行宽：120 字符
- 单行注释： `# 注释内容`（前面一个空格）
- 多行字符串：使用 `"""` 或 `'''`

---

## 3. Git 工作规范

### 代码提交要求

**每次代码修改完成后，必须进行 Git 提交**

- 完成一个功能模块或修复一个问题后，应立即提交代码
- 提交信息应清晰描述本次修改的内容
- 提交前确保代码能正常运行

### 禁止回滚规则

**严禁使用以下命令回滚任何代码和文件**：

- `git checkout`（用于文件恢复）
- `git revert`
- `git reset`（含 --hard, --soft 等参数）
- 任何其他回滚命令

**正确的处理方式**：
- 如果需要撤销修改，直接删除或重新编辑相关代码
- 如果提交了错误的代码，应该创建一个新的提交来修复

### Git 提交规范

```
提交类型(模块): 提交说明

提交类型：
- feat: 新功能
- fix: Bug 修复
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建/工具链

示例：
- feat(order): 添加分批卖出策略功能
- fix(strategy): 修复双均线金叉判断逻辑
- docs: 更新README文档
```

### 强制提交场景

以下情况**必须**提交代码：
- 完成任何功能模块的实现
- 修复任何 Bug
- 更新文档
- 修改配置文件
- 进行任何代码修改后

---

## 4. 交易系统开发规范

### 策略参数配置

所有策略参数集中在 `runtime_config.py` 中：

```python
# 均线配置，short_period 必须大于 long_period
short_period = 5   # 短周期均线
long_period = 60  # 长周期均线

# K线周期
kLine_type = '15m'  # 支持: 5m, 15m, 30m, 1h, 1d 等

# 分批卖出策略
isOpenSellStrategy = True
sellStrategy1 = {"profit": 1.05, "sell": 0.1}  # 盈利5%时卖出10%仓位
```

### 订单管理流程

```
买入流程：
1. 获取K线数据 → DataFrame转换
2. 双均线策略判断 → 金叉信号
3. 验证信号有效性（时间窗口）
4. 检查资产余额
5. 执行买入限价单
6. 保存订单信息到本地JSON

卖出流程：
1. 获取死叉信号
2. 检查本地订单信息
3. 检查持仓数量
4. 执行卖出限价单
5. 清理本地订单信息
```

### API 调用规范

- 所有 Binance API 调用通过 `BinanceAPI` 类封装
- 调用后检查返回值是否为 `None`
- 异常使用 `try-except` 捕获，记录堆栈跟踪

### 订单信息持久化

- 订单信息保存在 `JSON` 文件中
- 文件命名：`{symbol}_buyOrderInfo.json`（如 `DOGEUSDT_buyOrderInfo.json`）
- 存储内容：订单号、价格、时间、卖出策略配置

---

## 5. 测试规范

### 测试数据要求

- 使用真实市场数据进行测试
- 注意第一条K线可能产生虚假信号（技术指标计算不完整）
- 测试前确认网络通畅，API 可访问

### 交易安全要求

- 禁止在生产环境使用 Mock 数据进行测试
- 卖出前验证持仓数量大于 0
- 限价单总价值不低于 10 USDT

---

## 6. 运行环境

### 环境要求

- Python 3.7+
- 网络：能访问 Binance API（建议海外服务器）
- 交易所：Binance 账号 + API Key + API Secret

### 配置步骤

1. 申请 Binance API Key
2. 注册钉钉自定义机器人获取 Webhook
3. 修改 `app/authorization.py` 配置密钥
4. 修改 `runtime_config.py` 配置策略参数
5. 运行 `python main.py`

---

## 7. 文档规范

### 文档命名

- 设计文档：`docs/design/{模块名称}-设计文档.md`
- 需求文档：`docs/requirements/{模块名称}-需求文档.md`
- 测试文档：`docs/test/{模块名称}-测试文档.md`

### 代码注释

- 复杂业务逻辑必须添加注释说明
- 注释使用中文
- 禁止无意义的注释（如 `# 注释`）

---

## 8. 配置管理规范

### 8.1 配置文件结构

项目使用 `config.yaml` 作为配置文件，集中管理所有配置项：

```yaml
binance:
  api_key: ""           # 币安API密钥
  api_secret: ""        # 币安API私钥
  recv_window: 5000     # 请求超时时间
  proxy:                # 代理配置
    enabled: false      # 是否开启代理（默认关闭）
    host: "127.0.0.1"
    port: 7890

dingding:
  enabled: true        # 是否开启钉钉通知
  token: ""            # 钉钉群Token（告警）
  token2: ""           # 钉钉群Token（交易）

notifier:
  enabled: true
  provider: "dingding"  # dingding | weixin

weixin:
  enabled: false
  corp_id: ""
  secret: ""
  agent_id: 0
  to_user: "@all"

trade:
  strategy:
    ma:
      short_period: 5               # 短周期均线
      long_period: 60              # 长周期均线
  kLine_type: '15m'     # K线周期
  binance_market: "SPOT"
  binance_coinBase: "USDT"
  binance_coinBase_count: 20
  binance_tradeCoin: "DOGE"
  isOpenSellStrategy: true
  sellStrategy1: {"profit": 1.05, "sell": 0.1}
  sellStrategy2: {"profit": 1.10, "sell": 0.2}
  sellStrategy3: {"profit": 1.20, "sell": 0.2}

sqlite:
  enabled: false        # 是否从SQLite加载配置
  db_path: "/data/db/smart_quant_robot.db"
```

### 8.2 配置加载优先级

1. **SQLite数据库**（如果 enabled=true 且有数据）> **config.yaml** > **默认值**

### 8.3 SQLite配置存储

创建数据库表 `binance_config`：

```sql
CREATE TABLE IF NOT EXISTS `binance_config` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `api_key` VARCHAR(256) NOT NULL,
  `api_secret` VARCHAR(256) NOT NULL,
  `enabled` TINYINT DEFAULT 1,
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 8.4 配置访问方式

使用全局配置单例：

```python
from runtime_config import config

# 获取配置
api_key = config.get('binance.api_key')
ma_config = config.get('trade.strategy.ma')
short_period = ma_config.get('short_period', 5)  # 带默认值

# 设置配置
ma_config.set('short_period', 10)
```

### 8.5 禁止硬编码

- 所有配置必须通过 `config.get()` 获取
- 禁止在代码中硬编码 API 密钥、token 等敏感信息
- 默认值应放在 `runtime_config.py` 的 `_DEFAULT_CONFIG` 中