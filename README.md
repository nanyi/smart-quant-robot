# smart-quant-robot
数字货币，币安Binance交易所，比特币BTC 以太坊ETH 莱特币LTC 狗币DOGE 量化交易系统 火币 OKEX 交易策略 量化策略 自动交易

如果国内不能访问币安api，需要科学上网。

## 简介
这是一个数字货币量化交易系统，使用Binance币安的交易API。

本系统支持**多策略动态加权合成**，默认采用双均线策略，两条均线出现金叉则买入，出现死叉则卖出。

[币安账号注册页面](https://www.bsmkweb.cc/referral/earn-together/refer2earn-usdc/claim?hl=zh-CN&ref=GRO_28502_EM5R3&utm_source=referral_entrance&utm_medium=web_share_copy)（通过链接注册，享受交易返现优惠政策）

币安账号注册邀请码：GRO_28502_EM5R3

![binance_20210430132249_69_656.jpg](images/binance_20210430132249_69_656.jpg)

这世上，没有百分百赚钱的方式，量化交易策略只是一个辅助工具。

币圈有风险，入市需谨慎！！


## 系统架构

```
smart-quant-robot/
├── app/
│   ├── BinanceAPI.py       # 币安API封装
│   ├── OrderManager.py     # 订单管理器
│   ├── notifier.py         # 钉钉通知
│   └── services/
│       └── kline_service.py # K线服务层
├── strategy/
│   ├── base.py             # 策略基类
│   ├── ma.py               # 双均线策略
│   ├── composite.py        # 策略组合器
│   ├── volatility.py       # 波动率突破策略
│   ├── volume.py           # 成交量验证策略
│   ├── rsi.py             # RSI策略
│   ├── bollinger.py       # 布林带策略
│   └── macd.py            # MACD策略
├── backtest/
│   ├── models.py           # 回测数据模型
│   ├── engine.py           # 回测引擎
│   └── reporter.py         # 回测报告生成器
├── db/
│   ├── manager.py         # 数据库管理器
│   ├── kline_repo.py      # K线数据仓库
│   └── kline_data.py      # K线数据模型
├── scripts/
│   └── load_kline.py      # K线数据加载脚本
├── runtime_config.py       # 运行时配置
├── config.yaml            # 配置文件
└── main.py                # 程序入口
```


## 支持的策略

| 策略 | 说明 | 默认权重 |
|------|------|----------|
| MA | 双均线策略 | 1.0 |
| RSI | 相对强弱指数策略 | 0.8 |
| Bollinger | 布林带策略 | 0.8 |
| MACD | 指数平滑异同移动平均线 | 0.8 |
| Volatility | 波动率突破策略 | 0.7 |
| Volume | 成交量验证策略 | 0.7 |

策略采用动态加权合成，综合得分 > 阈值(0.5) 时产生交易信号。


## 双均线策略
以 ETH 为例，5分钟K线数据，均线5 和 均线60 为例：

均线5上穿均线60是金叉，执行买入；
均线5下穿均线60是死叉，执行卖出；

使用时，必须根据自身情况，调整 K线 和 均线！


## 为什么选择币安交易所

交易的手续费看起来很少，但是随着交易次数逐步增多，手续费也是一笔不小的开支。
所以我选择了币安，手续费低的大平台交易所

> 火币手续费 Maker 0.2% Taker 0.2%

> 币安手续费 Maker 0.1% Taker 0.1% （加上BNB家持手续费低至0.075%）

[币安账号注册页面](https://www.bsmkweb.cc/referral/earn-together/refer2earn-usdc/claim?hl=zh-CN&ref=GRO_28502_EM5R3&utm_source=referral_entrance&utm_medium=web_share_copy)（通过链接注册，享受交易返现优惠政策）


## 快速使用

### 1、环境配置

```
python3.7+
pip install -r requirements.txt
```

### 2、获取币安API的 api_key 和 api_secret

申请api_key地址:

[币安API管理页面](https://www.binance.com/cn/usercenter/settings/api-management)


### 3、注册钉钉自定义机器人Webhook

[钉钉自定义机器人注册方法](https://m.dingtalk.com/qidian/help-detail-20781541)

### 4、修改配置文件 config.yaml

```yaml
binance:
  api_key: '币安key'
  api_secret: '币安secret'

dingding:
  enabled: true
  token: '钉钉群机器人token'

strategy:
  enabled_strategies:
    - "ma"         # 启用双均线策略
    - "rsi"        # 可添加更多策略
  weights:
    ma: 1.0
    rsi: 0.8
  threshold: 0.5

trade:
  strategy:
    ma:
      short_period: 5          # 短期均线
      long_period: 60         # 长期均线
  kLine_type: '15m' # K线周期
  binance_tradeCoin: "DOGE"
```

### 5、加载K线数据

```bash
# 加载最新1000条K线
python scripts/load_kline.py --symbol DOGEUSDT --interval 15m --limit 1000

# 加载最近30天K线
python scripts/load_kline.py --symbol DOGEUSDT --interval 15m --days 30
```

### 6、运行程序

```bash
python main.py
```


## 回测系统

### 基本使用

```python
from backtest import BacktestEngine, BacktestReporter
from strategy import MAStrategy
from db.kline_data import KlineData

# 准备K线数据
klines = [...]  # KlineData列表，或从数据库加载

# 创建回测引擎
engine = BacktestEngine(initial_capital=10000.0, commission_rate=0.001)

# 创建策略
strategy = MAStrategy(short_period=5, long_period=60)

# 运行回测
stats = engine.run_with_data(strategy, df, symbol='DOGEUSDT')

# 生成报告
reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
print(reporter.generate_text_report())
```

### 回测报告示例

```
============================================================
回测报告
============================================================

【账户信息】
  初始资金: 10000.00 USDT
  最终资金: 11500.00 USDT
  总收益: 1500.00 USDT
  收益率: 15.00%

【交易统计】
  总交易次数: 10
  盈利交易次数: 6
  亏损交易次数: 4
  胜率: 60.00%

【收益统计】
  总盈利: 2000.00 USDT
  总亏损: 500.00 USDT
  盈利因子: 4.00

【风险统计】
  最大回撤: 500.00 USDT
  最大回撤率: 5.00%
  夏普比率: 1.50
```

### 从数据库加载数据运行回测

```python
from backtest import BacktestEngine, BacktestReporter
from strategy import CompositeStrategy, MAStrategy, RSIStrategy
from app.services import KlineService
from db.kline_data import KlineData

# 创建K线服务
kline_service = KlineService()

# 从数据库加载K线数据
klines = kline_service.get_from_db('DOGEUSDT', '15m', limit=1000)

# 转换为DataFrame
df = KlineData.to_dataframe(klines)

# 创建策略组合
strategies = [MAStrategy(short_period=5, long_period=60), RSIStrategy(period=14)]
composite = CompositeStrategy(strategies, weights={'ma': 1.0, 'rsi': 0.8})

# 创建回测引擎
engine = BacktestEngine(initial_capital=10000.0)

# 运行回测
stats = engine.run_with_data(composite, df, symbol='DOGEUSDT')

# 生成JSON格式报告
reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
report_json = reporter.generate_json_report()
print(report_json)
```


## 服务器部署
购买服务器，建议是海外服务器，可以访问币安API

### 服务器配置：
Linux, 1核CPU, 2G内存(1G也可)

可以在阿里云上购买的日本东京服务器(传说币安服务器就在东京)

也可选择 新加坡、香港服务器
