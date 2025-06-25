# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:24
# @Author  : Ryan

import hashlib
import hmac
import requests
import time

from app.authorization import recv_window

try:
    from urllib import urlencode
# python3
except ImportError:
    from urllib.parse import urlencode


class BinanceAPI(object):
    """
    Binance交易所API封装类
    
    提供与Binance现货和合约交易相关的完整API接口，包括公共数据获取（K线、价格、交易规则）
    和私有账户操作（下单、查询资产、账户信息）。支持自动签名、代理配置和错误处理。
    
    API文档参考：https://binance-docs.github.io/apidocs/spot/cn/
    """
    BASE_URL = "https://www.binance.com/api/v1"
    FUTURE_URL = "https://fapi.binance.com"
    BASE_URL_V3 = "https://api.binance.com/api/v3"
    PUBLIC_URL = "https://www.binance.com/exchange/public/product"

    def __init__(self, key, secret, proxy_host="127.0.0.1", proxy_port=7890):
        """
        初始化Binance API客户端
        
        :param key: Binance API密钥（从官网获取）
        :param secret: Binance API私钥（从官网获取）
        :param proxy_host: 代理服务器主机地址，默认为本地回环地址
        :param proxy_port: 代理服务器端口，默认为7890
        """
        self.key = key
        self.secret = secret
        # 全局代理配置
        self.proxies = {
            "http": f"http://{proxy_host}:{proxy_port}",
            "https": f"http://{proxy_host}:{proxy_port}",
        }
        self.proxies = None

    def ping(self):
        """
        测试API连接状态
        
        发送ping请求验证与Binance API服务器的连接是否正常。
        
        :return: 服务器返回的JSON响应，成功时包含空对象 {}
        """
        path = "%s/ping" % self.BASE_URL_V3
        return requests.get(path, timeout=180, verify=True, proxies=self.proxies).json()

    # 服务器时间
    def serverTime(self):
        """
        获取Binance服务器当前时间
        
        用于同步本地时间与服务器时间，确保订单时间戳的准确性。
        
        :return: 包含服务器时间的字典 {'serverTime': <毫秒时间戳>}
        """
        path = "%s/time" % self.BASE_URL_V3
        return requests.get(path, timeout=180, verify=True, proxies=self.proxies).json()

    # 获取交易规则和交易对信息, GET /api/v3/exchangeInfo
    def exchangeInfo(self):
        """
        获取交易所交易规则和交易对信息
        
        返回所有交易对的详细信息，包括交易对符号、精度要求、最小/最大交易量、
        价格过滤器等，用于格式化订单参数。
        
        :return: 包含交易所信息的字典，主要字段：
                 - 'symbols': 交易对列表，每个元素包含symbol、filters等信息
                 - 'timezone': 服务器时区
                 失败时返回None
        """
        path = "%s/exchangeInfo" % self.BASE_URL_V3
        return requests.get(path, timeout=180, verify=True, proxies=self.proxies).json()

    # 获取最新价格
    def get_ticker_price(self, market):
        """
        获取指定交易对的最新成交价格
        
        :param market: 交易对符号，例如 'BTCUSDT'、'ETHUSDT'
        :return: 最新价格（float类型），失败时抛出异常
        """
        path = "%s/ticker/price" % self.BASE_URL_V3
        params = {"symbol": market}
        res = self._get_no_sign(path, params)
        print("get_ticker_price=")
        print(res)
        time.sleep(2)
        return float(res['price'])

    # 24hr 价格变动情况
    def get_ticker_24hour(self, market):
        """
        获取指定交易对24小时价格统计信息
        
        返回过去24小时内的价格变化、成交量、最高价、最低价等统计数据。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :return: 包含24小时统计数据的字典，主要字段：
                 - 'priceChange': 价格变化量
                 - 'priceChangePercent': 价格变化百分比
                 - 'highPrice': 最高价
                 - 'lowPrice': 最低价
                 - 'volume': 成交量
                 - 'quoteVolume': 成交额
        """
        path = "%s/ticker/24hr" % self.BASE_URL_V3
        params = {"symbol": market}
        res = self._get_no_sign(path, params)
        return res

    # 获取K线 https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=15m&startTime=1619761128000&endTime=1619764848000
    def get_klines(self, market, interval, limit=0, startTime=None, endTime=None):
        """
        获取指定交易对的K线（蜡烛图）数据
        
        支持自定义时间范围和数量限制，返回OHLCV（开盘价、最高价、最低价、收盘价、成交量）数据。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :param interval: K线时间间隔，可选值：'1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M'
        :param limit: 返回K线数量，范围1-1000，默认500
        :param startTime: 起始时间（毫秒时间戳），可选
        :param endTime: 结束时间（毫秒时间戳），可选
        :return: K线数据列表，每个元素为数组：
                 [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, 
                  主动买入量, 主动买入额, 忽略]
        """
        path = "%s/klines" % self.BASE_URL_V3
        params = None
        if startTime is None:
            params = {"symbol": market, "interval": interval}
        else:
            params = {"symbol": market, "interval": interval, "startTime": startTime, "endTime": endTime}

        if limit is None or limit <= 0 or limit > 1000:
            limit = 500

        params['limit'] = limit

        return self._get_no_sign(path, params)

    # 现货，账户信息，GET /api/v3/account
    def get_Spot_UserData_account(self):
        """
        获取现货账户完整信息（需要签名）
        
        返回账户中所有资产的余额、冻结金额、交易权限等详细信息。
        此接口为私有接口，需要使用API密钥和签名。
        
        :return: 账户信息字典，主要字段：
                 - 'makerCommission': 买单手续费率
                 - 'takerCommission': 卖单手续费率
                 - 'balances': 资产余额列表，每个元素包含asset、free、locked
                 - 'canTrade': 是否允许交易
                 失败时返回None
        """
        stamp_now = int(round(time.time() * 1000))
        path = "%s/account" % self.BASE_URL_V3
        params = {"timestamp": stamp_now, "recvWindow": recv_window}
        res = self._get_with_sign(path, params)
        return res

    def get_spot_asset_by_symbol(self, symbol):
        """
        获取指定资产的现货余额信息
        
        从账户信息中提取特定资产的可用余额和冻结余额。
        
        :param symbol: 资产符号，例如 'USDT'、'BTC'、'ETH'
        :return: 资产信息字典 {'asset': <资产符号>, 'free': <可用余额>, 'locked': <冻结余额>}，
                 未找到资产时返回None
        """
        ud_account = self.get_Spot_UserData_account()

        if ud_account is not None and "balances" in ud_account.keys():
            balances = ud_account["balances"]
            if balances is not None and type(balances).__name__ == 'list':
                for balance in balances:
                    if str(balance["asset"]) == symbol:
                        return balance

    # 查询每日资产快照，/sapi/v1/accountSnapshot
    def get_UserData_accountSnapshot(self):
        """
        获取账户每日资产快照历史
        
        查询过去几天的账户资产快照，用于分析资产变化趋势。
        
        :return: 资产快照数据字典，包含最近5天的SPOT类型快照
        """
        stamp_now = int(round(time.time() * 1000))
        path = "https://www.binance.com/sapi/v1/accountSnapshot"
        params = {"type": "SPOT", "timestamp": stamp_now, "limit": 5}

        # res = self._post(path, params)
        res = self._get_with_sign(path, params).json()
        return res

    def buy_limit(self, market, quantity, rate):
        """
        创建现货限价买单
        
        以指定价格提交买入订单，订单将等待成交直到被完全执行或取消。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :param quantity: 购买数量（基础资产数量）
        :param rate: 限价（单价）
        :return: 订单响应字典，包含orderId、status、executedQty等信息
        """
        print("购买 " + market + "\t" + '%f 个, ' % quantity + "价格：%f" % rate)
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "BUY", rate)
        return self._post(path, params)

    # 测试专用，买入
    def buy_limit_test(self, market, quantity, rate):
        """
        创建模拟买入订单（仅用于测试）
        
        不进行实际交易，返回一个模拟的订单响应，用于测试交易逻辑。
        
        :param market: 交易对符号
        :param quantity: 购买数量
        :param rate: 购买价格
        :return: 模拟订单字典，状态为FILLED（已成交）
        """
        tStamp = int(1000 * time.time())
        dict = {'symbol': market, 'orderId': 924538226, 'orderListId': -1, 'clientOrderId': 'wtswxN4L8O6hZiWNiOxuaN', \
                'transactTime': tStamp, 'price': str(round(rate, 8)), 'origQty': str(round(quantity, 8)),
                'executedQty': str(round(quantity, 8)), \
                'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'fills': []}
        return dict

    # 测试专用，卖出
    def sell_limit_test(self, market, quantity, rate):
        """
        创建模拟卖出订单（仅用于测试）
        
        不进行实际交易，返回一个模拟的订单响应，用于测试交易逻辑。
        
        :param market: 交易对符号
        :param quantity: 卖出数量
        :param rate: 卖出价格
        :return: 模拟订单字典，状态为NEW（新订单）
        """
        tStamp = int(1000 * time.time())
        dict = {'symbol': market, 'orderId': 933997128, 'orderListId': -1, 'clientOrderId': 'uepwnRSgfVioZlBhXqTr03', \
                'transactTime': tStamp, 'price': str(round(rate, 8)), 'origQty': str(round(quantity, 8)),
                'executedQty': '0.00000000', \
                'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT',
                'side': 'SELL', 'fills': []}
        return dict

    def sell_limit(self, market, quantity, rate):
        """
        创建现货限价卖单
        
        以指定价格提交卖出订单，订单将等待成交直到被完全执行或取消。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :param quantity: 卖出数量（基础资产数量）
        :param rate: 限价（单价）
        :return: 订单响应字典，包含orderId、status、executedQty等信息
        """
        print("出售 " + market + "\t" + '%f 个, ' % quantity + "价格：%f" % rate)

        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "SELL", rate)
        return self._post(path, params)

    ### ----私有函数---- ###
    def _order(self, market, quantity, side, price=None):
        """
        构建订单参数字典
        
        根据订单类型（限价单或市价单）构建符合Binance API要求的订单参数。
        
        :param market: 交易对符号，例如 'BTCUSDT'、'ETHUSDT'
        :param quantity: 交易数量（基础资产数量）
        :param side: 订单方向，'BUY'（买入）或 'SELL'（卖出）
        :param price: 限价价格，不提供则创建市价单
        :return: 订单参数字典，包含symbol、side、quantity、type等字段
        """
        params = {}

        if price is not None:
            params["type"] = "LIMIT"
            params["price"] = self._format(price)
            params["timeInForce"] = "GTC"
        else:
            params["type"] = "MARKET"

        params["symbol"] = market
        params["side"] = side
        params["quantity"] = '%.8f' % quantity

        return params

    def _get_no_sign(self, path, params={}):
        """
        发送无需签名的GET请求
        
        用于访问公共API端点（如K线、价格等），不需要API密钥认证。
        
        :param path: API端点URL
        :param params: 请求参数字典
        :return: API响应的JSON解析结果
        """
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        return requests.get(url, timeout=180, verify=True).json()

    def _get_no_sign_header(self, path, params={}, header={}):
        """
        发送带自定义请求头的无签名GET请求
        
        :param path: API端点URL
        :param params: 请求参数字典
        :param header: 自定义请求头字典
        :return: API响应的JSON解析结果
        """
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        return requests.get(url, headers=header, timeout=180, verify=True).json()

    def _get_with_sign(self, path, params={}):
        """
        发送需要签名的GET请求
        
        用于访问私有API端点（如账户信息、订单查询等），需要API密钥和签名认证。
        自动计算HMAC-SHA256签名并添加到请求参数中。
        
        :param path: API端点URL
        :param params: 请求参数字典（不包含signature）
        :return: API响应的JSON解析结果
        """
        tmp_signature = self._signature(params)
        params.update({"signature": tmp_signature})
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        header = {"Content-Type": "application/json", "X-MBX-APIKEY": self.key}

        return requests.get(url, headers=header, timeout=180, verify=True).json()

    # 生成 signature
    def _signature(self, params={}):
        """
        生成HMAC-SHA256签名
        
        使用API私钥对请求参数进行签名，确保请求的完整性和身份验证。
        Binance API要求所有私有接口请求都必须携带签名。
        
        :param params: 请求参数字典（不包含signature）
        :return: 十六进制格式的签名字符串
        """
        data = params.copy()
        # ts = int(1000 * time.time())
        # data.update({"timestamp": ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        return signature

    def _sign(self, params={}):
        """
        生成完整的签名字典
        
        添加时间戳并计算签名，返回包含签名和时间戳的完整参数字典。
        
        :param params: 原始请求参数字典
        :return: 添加了timestamp和signature的完整参数字典
        """
        data = params.copy()

        ts = int(1000 * time.time())
        data.update({"timestamp": ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        data.update({"signature": signature})
        return data

    def _post(self, path, params={}):
        """
        发送POST请求创建订单
        
        用于提交新订单到交易所，自动处理签名、请求头和参数编码。
        
        :param path: API端点URL
        :param params: 订单参数字典（不包含signature和recvWindow）
        :return: API响应的JSON解析结果，包含订单详情
        """
        params.update({"recvWindow": recv_window})
        query = urlencode(self._sign(params))
        url = "%s" % (path)
        header = {"X-MBX-APIKEY": self.key}
        return requests.post(url, headers=header, data=query, timeout=180, verify=True).json()

    def _format(self, price):
        """
        格式化价格为8位小数精度的字符串
        
        确保价格符合Binance API的参数格式要求。
        
        :param price: 原始价格数值
        :return: 格式化后的价格字符串，保留8位小数
        """
        return "{:.8f}".format(price)

    # 合约
    def market_future_order(self, side, symbol, quantity, positionSide):
        """
        创建合约市价订单
        
        在币安合约市场创建市价开仓或平仓订单，支持双向持仓模式（LONG/SHORT）。
        
        :param side: 订单方向，'BUY'（开多/平空）或 'SELL'（开空/平多）
        :param symbol: 合约交易对符号，例如 'BTCUSDT'、'ETHUSDT'
        :param quantity: 合约数量
        :param positionSide: 持仓方向，'LONG'（多头）或 'SHORT'（空头）
        :return: 订单响应字典，包含orderId、status、executedQty等信息
        """
        path = "%s/fapi/v1/order" % self.FUTURE_URL
        params = self._order(symbol, quantity, side, positionSide)
        return self._post(path, params)


if __name__ == "__main__":
    instance = BinanceAPI(api_key, api_secret)
    # print(instance.buy_limit("EOSUSDT",5,2))
    # print(instance.get_ticker_price("WINGUSDT"))
    print(instance.get_ticker_24hour("WINGUSDT"))
