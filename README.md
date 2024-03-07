# smart-quant-robot
数字货币，币安Binance交易所，比特币BTC 以太坊ETH 莱特币LTC 狗币DOGE 量化交易系统 火币 OKEX 交易策略 量化策略 自动交易

如果国内不能访问币安api，需要科学上网。

## 简介
这是一个数字货币量化交易系统，使用的Binance币安的交易API。

本系统采用双均线交易策略，两条均线出现金叉则买入，出现死叉则卖出。

[币安账号注册页面](https://www.bsmkweb.cc/referral/earn-together/refer2earn-usdc/claim?hl=zh-CN&ref=GRO_28502_EM5R3&utm_source=referral_entrance&utm_medium=web_share_copy)（通过链接注册，享受交易返现优惠政策）

币安账号注册邀请码：GRO_28502_EM5R3

![binance_20210430132249_69_656.jpg](images/binance_20210430132249_69_656.jpg)

这世上，没有百分百赚钱的方式，量化交易策略只是一个辅助工具。

币圈有风险，入市需谨慎！！


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

## 运行环境

python3.7

由于交易所的api在大陆无法访问，需要科学上网，若无，可用[泰山]

泰山邀请码：OxCJV3VZ

最新地址1：[https://hk.taishan.pro](https://hk.taishan.pro/#/register?code=OxCJV3VZ)

最新地址2：[https://jp.taishan.pro](https://jp.taishan.pro/#/register?code=OxCJV3VZ)

最新地址3：[https://ru.taishan.pro](https://ru.taishan.pro/#/register?code=OxCJV3VZ)


## 快速使用

1、获取币安API的 api_key 和 api_secret

申请api_key地址:

[币安API管理页面](https://www.binance.com/cn/usercenter/settings/api-management)


2、注册钉钉自定义机器人Webhook，用于推送交易信息到指定的钉钉群

[钉钉自定义机器人注册方法](https://m.dingtalk.com/qidian/help-detail-20781541)

3、修改app目录下的authorization文件

```
api_key='币安key'
api_secret='币安secret'
dingding_token = '申请钉钉群助手的token'   # 强烈建议使用
```

4、交易策略配置信息 runtime_config.py

设置配置信息：

```
# 均线, ma_x 要大于 ma_y
ma_x = 5
ma_y = 60

# 币安
binance_market = "SPOT"#现货市场
kLine_type = '15m' # 15分钟k线类型，可以设置为5分钟K线：5m;1小时为：1h;1天为：1d
```
当 kline 5 向上穿过 kline 60， 则执行买入。

当 kline 5 向下穿过 kline 60， 则执行卖出。

可根据自己的喜好，调整 ma_x 和 ma_y 的值。 

也可以调整 kLine_type ，来选择 5分钟K线、15分钟K线、30分钟K线、1小时K线、1天K线等；

不同的K线，最终效果也是不一样的。

5、同时交易多币种

在main.py中

创建多个订单管理对象：
```
# 使用 USDT 购买 DOGE,限定最多100个USDT
orderManager_doge = OrderManager("USDT", 100,"DOGE", binance_market)
# 使用 USDT 购买 ETH,限定最多100个USDT
orderManager_eth = OrderManager("USDT", 100,"ETH", binance_market)
```

将orderManager_doge 和 orderManager_eth 加入定时执行的方法中：
```
def binance_func():
    orderManager_doge.binance_func()
    time.sleep(10)
    orderManager_eth.binance_func()

```

程序可同时监控 DOGE 和 ETH 的均线，并根据策略执行交易。
使用时，可根据自身需要，增加其他币种。

6、运行程序(记得先开科学上网)
```
python main.py
```


## 服务器部署
购买服务器，建议是海外服务器，可以访问币安API

### 服务器配置：
Linux, 1核CPU, 2G内存(1G也可)

可以在阿里云上购买的日本东京服务器(传说币安服务器就在东京)

也可选择 新加坡、香港服务器

