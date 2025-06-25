# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan

import json, os, time, datetime, math
import traceback

from app.BinanceAPI import BinanceAPI

from app.authorization import api_key, api_secret
from app.dingding import Message
from strategy.DoubleAverageLinesStrategy import DoubleAverageLines
import schedule
from runtime_config import sellStrategy1, sellStrategy2, sellStrategy3, ma_x, ma_y, isOpenSellStrategy, kLine_type

binan = BinanceAPI(api_key, api_secret)
msg = Message()

dALines = DoubleAverageLines()


class ExchangeRule(object):
    """
    交易所交易规则配置类

    用于解析和存储Binance交易所的交易对规则信息，包括交易对基本信息、价格精度、
    数量精度以及交易限制（价格范围、数量范围、最小变动单位等）。
    这些规则用于在交易时格式化订单参数，确保符合交易所要求。
    """

    def __init__(self, dict):
        """
        初始化交易所规则对象

        从交易所信息字典中解析交易对的详细规则，包括基础资产信息、计价资产信息、
        价格过滤器（价格范围和精度）以及手数过滤器（数量范围和精度）。

        :param dict: 交易所返回的交易对信息字典，必须包含以下字段：
                     - 'symbol': 交易对符号（如 'BTCUSDT'）
                     - 'baseAsset': 基础资产（如 'BTC'）
                     - 'baseAssetPrecision': 基础资产精度
                     - 'quoteAsset': 计价资产（如 'USDT'）
                     - 'quoteAssetPrecision': 计价资产精度
                     - 'filters': 过滤器列表，包含价格过滤器和手数过滤器
        """
        if dict is not None and 'symbol' in dict:
            self.symbol = dict['symbol']
            self.baseAsset = dict['baseAsset']
            self.baseAssetPrecision = dict['baseAssetPrecision']
            self.quoteAsset = dict['quoteAsset']
            self.quoteAssetPrecision = dict['quoteAssetPrecision']

            filters = dict['filters']
            for filter in filters:
                if filter['filterType'] == 'PRICE_FILTER':
                    # "minPrice": "0.00001000",
                    # "maxPrice": "1000.00000000",
                    # "tickSize": "0.00001000"
                    self.minPrice = filter['minPrice']
                    self.maxPrice = filter['maxPrice']
                    self.tickSize = filter['tickSize']

                if filter['filterType'] == 'LOT_SIZE':
                    # "minQty": "0.10000000",
                    # "maxQty": "9000000.00000000",
                    # "stepSize": "0.10000000"
                    self.minQty = filter['minQty']
                    self.maxQty = filter['maxQty']
                    self.stepSize = filter['stepSize']


class OrderManager(object):
    """
    订单管理器类

    负责管理加密货币交易订单的完整生命周期，包括买入、卖出、订单信息持久化、
    分批出售策略执行等功能。该类封装了与Binance交易所的交互逻辑，并提供
    自动化的交易决策和风险控制机制。
    """

    def __init__(self, coinBase, coinBaseCount, tradeCoin, market):
        """
        初始化订单管理器

        :param coinBase: 基础计价货币，例如 'USDT'、'BTC' 等
        :param coinBaseCount: 用于购买的最大资金量（以基础计价货币计）
        :param tradeCoin: 要交易的币种，例如 'DOGE'、'BTC' 等
        :param market: 交易市场类型，例如 'SPOT'（现货）、'FUTURES'（合约）等
        """
        self.coin_base = coinBase  # 基础币，例如USDT
        self.coin_base_count = coinBaseCount  # 买币时最多可用资金量
        self.trade_coin = tradeCoin  # 买卖币种，例如 DOGER
        self.market = market  # 市场，例如：现货 "SPOT"
        self.symbol = tradeCoin + coinBase  # 交易符号，例如"DOGEUSDT"
        self.exchangeRule = None
        self.orderInfoSavePath = "./" + self.symbol + "_buyOrderInfo.json"  # 订单信息存储路径

    def gain_exchangeRule(self, theSymbol):
        """
        获取并缓存指定交易对的交易所规则

        从Binance API获取交易对的详细规则信息（包括价格精度、数量限制等），
        并缓存到本地以避免重复请求。仅在首次调用时获取。

        :param theSymbol: 交易对符号，例如 'BTCUSDT'
        """
        if self.exchangeRule is None:
            dict = binan.exchangeInfo()
            if dict is not None and 'symbols' in dict:
                symbol_list = dict['symbols']
                for tmp_symbol in symbol_list:
                    if tmp_symbol['symbol'] == theSymbol:
                        self.exchangeRule = ExchangeRule(tmp_symbol)
                        break;

        # return self.exchangeRule

    #  执行卖出
    def doSellFunc(self, symbol, quantity, cur_price):
        """
        执行限价卖出订单

        创建限价卖单并确保订单总价值满足交易所最低要求（10 USDT）。
        如果初始数量不满足要求，会逐步增加数量直到满足条件。

        :param symbol: 交易对符号，例如 'BTCUSDT'
        :param quantity: 卖出数量
        :param cur_price: 当前价格（限价）
        :return: 格式化后的卖出结果消息字符串
        """
        print("马上卖出 " + str(symbol) + " " + str(quantity) + " 个，单价：" + str(cur_price))

        # 如果总价值小于10
        if (quantity * cur_price) < 10:
            quantity = self.format_trade_quantity(11.0 / cur_price)
            if (quantity * cur_price) < 10:
                quantity = self.format_trade_quantity(13.0 / cur_price)
                if (quantity * cur_price) < 10:
                    quantity = self.format_trade_quantity(16.0 / cur_price)
                    if (quantity * cur_price) < 10:
                        quantity = self.format_trade_quantity(20.0 / cur_price)

        # 卖出
        res_order_sell = binan.sell_limit(symbol, quantity, cur_price)
        print("出售部分结果：")
        print("量：" + str(quantity) + ", 价格：" + str(cur_price) + ", 总价值：" + str(quantity * cur_price))
        print(res_order_sell)
        order_result_str = self.printOrderJsonInfo(res_order_sell)
        msgInfo = "卖出结果：\n" + str(order_result_str)

        return msgInfo

    # 分批出售策略
    def sellStrategy(self, filePath):
        """
        执行分批卖出策略

        根据预设的多级止盈策略（sellStrategy1/2/3），当价格达到目标价位时
        自动执行部分或全部卖出操作。策略按照从高级到低级的顺序检查，
        每触发一个策略就会删除该策略配置并更新本地订单文件。

        :param filePath: 订单信息JSON文件的保存路径
        :return: 卖出操作的结果消息字符串，无操作时返回空字符串
        """
        msgInfo = ""
        dictOrder = self.readOrderInfo(filePath)
        if dictOrder is None:
            return msgInfo

        # 读取上次买入的价格
        buyPrice = self.priceOfPreviousOrder(self.orderInfoSavePath)
        if buyPrice > 0:
            # 查询当前价格
            cur_price = binan.get_ticker_price(self.symbol)
            print("当前 " + str(self.symbol) + " 价格：" + str(cur_price))
            # 查询当前资产
            asset_coin = binan.get_spot_asset_by_symbol(self.trade_coin)
            print(self.trade_coin + " 资产2：")
            print(asset_coin)

            if "sellStrategy3" in dictOrder:
                print("sellStrategy--sellStrategy3--1")
                tmpSellStrategy = dictOrder['sellStrategy3']
                print("买入价格：" + str(buyPrice) + " * " + str(tmpSellStrategy) + " = " + str(
                    buyPrice * tmpSellStrategy['profit']) + " 和 当前价格：" + str(cur_price) + " 比较")
                if buyPrice * tmpSellStrategy['profit'] <= cur_price:
                    print("sellStrategy--sellStrategy3--2")

                    quantity = self.format_trade_quantity(float(asset_coin["free"]) * tmpSellStrategy['sell'])
                    # 卖出
                    msgInfo = msgInfo + self.doSellFunc(self.symbol, quantity, cur_price)
                    del dictOrder['sellStrategy3']
                    self.writeOrderInfo(filePath, dictOrder)
                    dictOrder = self.readOrderInfo(filePath)
                    print("部分卖出--sellStrategy3")

            if "sellStrategy2" in dictOrder:
                tmpSellStrategy = dictOrder['sellStrategy2']
                print("sellStrategy--sellStrategy2--1")
                print("买入价格：" + str(buyPrice) + " * " + str(tmpSellStrategy) + " = " + str(
                    buyPrice * tmpSellStrategy['profit']) + " 和 当前价格：" + str(cur_price) + " 比较")

                if buyPrice * tmpSellStrategy['profit'] <= cur_price:
                    print("sellStrategy--sellStrategy2--2")

                    quantity = self.format_trade_quantity(float(asset_coin["free"]) * tmpSellStrategy['sell'])
                    # 卖出
                    msgInfo = msgInfo + self.doSellFunc(self.symbol, quantity, cur_price)
                    del dictOrder['sellStrategy2']
                    self.writeOrderInfo(filePath, dictOrder)
                    dictOrder = self.readOrderInfo(filePath)
                    print("部分卖出--sellStrategy2")

            if "sellStrategy1" in dictOrder:
                tmpSellStrategy = dictOrder['sellStrategy1']
                print("sellStrategy--sellStrategy1--1")
                print("买入价格：" + str(buyPrice) + " * " + str(tmpSellStrategy) + " = " + str(
                    buyPrice * tmpSellStrategy['profit']) + " 和 当前价格：" + str(cur_price) + " 比较")

                if buyPrice * tmpSellStrategy['profit'] <= cur_price:
                    print("sellStrategy--sellStrategy1--2")

                    quantity = self.format_trade_quantity(float(asset_coin["free"]) * tmpSellStrategy['sell'])
                    # 卖出
                    msgInfo = msgInfo + self.doSellFunc(self.symbol, quantity, cur_price)
                    del dictOrder['sellStrategy1']
                    self.writeOrderInfo(filePath, dictOrder)
                    dictOrder = self.readOrderInfo(filePath)
                    print("部分卖出--sellStrategy1")

        return msgInfo

    # 格式化交易信息结果
    def printOrderJsonInfo(self, orderJson):
        """
        将订单JSON对象格式化为可读字符串

        解析Binance返回的订单JSON数据，提取关键信息（时间、币种、价格、数量、方向）
        并格式化为人类可读的字符串格式，用于钉钉通知或日志记录。

        :param orderJson: Binance订单响应字典或任意对象
        :return: 格式化后的订单信息字符串
        """
        str_result = ""
        if type(orderJson).__name__ == 'dict':
            all_keys = orderJson.keys()
            if 'symbol' in orderJson and 'orderId' in orderJson:

                time_local = time.localtime(orderJson['transactTime'] / 1000)
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time_local)

                str_result = str_result + "时间：" + str(time_str) + "\n"
                str_result = str_result + "币种：" + str(orderJson['symbol']) + "\n"
                str_result = str_result + "价格：" + str(orderJson['price']) + "\n"
                str_result = str_result + "数量：" + str(orderJson['origQty']) + "\n"
                str_result = str_result + "方向：" + str(orderJson['side']) + "\n"
            else:
                str_result = str(orderJson)
        else:
            str_result = str(orderJson)

        return str_result

    # 读取本地存储的买入订单信息
    def readOrderInfo(self, filePath):
        """
        从本地JSON文件读取买入订单信息

        读取并验证保存在本地的订单数据，确保必要的字段存在。

        :param filePath: 订单信息JSON文件的路径
        :return: 包含订单信息的字典，文件不存在或数据无效时返回None
        """
        if os.path.exists(filePath) is False:
            return None

        with open(filePath, 'r') as f:
            data = json.load(f)
            print("读取--买入信息：")
            print(data)
            if 'symbol' in data and 'orderId' in data and 'price' in data:
                return data
            else:
                return None

    # 比较本次买入提示的str是否重复
    def judgeToBuyCommand(self, filePath, theToBuyCommand):
        """
        判断买入信号是否重复

        通过比较当前买入信号与上次记录的买入信号，避免在同一时间点
        重复执行买入操作。

        :param filePath: 订单信息JSON文件的路径
        :param theToBuyCommand: 当前的买入信号标识字符串
        :return: True表示可以执行买入（不重复），False表示信号重复不应买入
        """
        orderDict = self.readOrderInfo(filePath)

        if orderDict is None:
            return True  # 购买

        if "toBuy" in orderDict:
            if orderDict["toBuy"] == theToBuyCommand:
                print('本次购买时间是 ' + str(theToBuyCommand) + ' ，重复，不执行购买')
                return False  # 不执行购买，因为重复

        return True

    # 获取 上次买入订单中的价格Price
    def priceOfPreviousOrder(self, filePath):
        """
        获取上次买入订单的成交价格

        从本地订单文件中提取上次买入的价格，用于计算收益率和判断
        是否触发卖出策略。

        :param filePath: 订单信息JSON文件的路径
        :return: 上次买入价格（float），无订单时返回0.0
        """
        dataDict = self.readOrderInfo(filePath)
        thePrice = 0.0

        if dataDict is not None and 'price' in dataDict:
            thePrice = float(dataDict['price'])

        return thePrice

    # 清理 本地存储的买入订单信息
    def clearOrderInfo(self, filePath):
        """
        删除本地存储的订单信息文件

        在卖出完成后清理本地订单数据，为下一次买入做准备。

        :param filePath: 要删除的订单信息文件路径
        """
        if os.path.exists(filePath) is True:
            os.remove(filePath)
            print("清理订单信息---do")

    # 存储 买入订单信息
    def writeOrderInfo(self, filePath, dictObj):
        """
        将订单信息保存到本地JSON文件

        先清除旧文件，再将新的订单数据写入JSON文件进行持久化存储。

        :param filePath: 订单信息JSON文件的保存路径
        :param dictObj: 要保存的订单信息字典对象
        """

        self.clearOrderInfo(filePath)
        print("写入--买入信息：")
        print(dictObj)
        with open(filePath, 'w') as f:
            json.dump(dictObj, f)

    def writeOrderInfoWithSellStrategy(self, filePath, dictObj):
        """
        保存订单信息并附加卖出策略配置

        在全局配置启用了卖出策略时，将三级止盈策略参数添加到订单信息中
        一并保存，供后续自动卖出时使用。

        :param filePath: 订单信息JSON文件的保存路径
        :param dictObj: 要保存的订单信息字典对象
        """

        if isOpenSellStrategy:
            dictObj["sellStrategy1"] = sellStrategy1
            dictObj["sellStrategy2"] = sellStrategy2
            dictObj["sellStrategy3"] = sellStrategy3

        self.writeOrderInfo(filePath, dictObj)

    def gain_kline(self, symbol, timeInterval='15m'):
        """
        获取指定交易对的K线数据

        从Binance API获取历史K线数据，用于技术分析。默认获取最近1000条K线记录，
        注意第一条数据可能因计算周期不完整而产生虚假信号。

        :param symbol: 交易对符号，例如 'BTCUSDT'、'DOGEUSDT' 等
        :param timeInterval: K线时间周期，支持的值包括 '1m', '3m', '5m', '15m', '30m',
                            '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
                            默认为 '15m'（15分钟）
        :return: 成功时返回K线数据列表（list），每个元素包含[开盘时间, 开盘价, 最高价,
                 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, 主动买入量, 主动买入额]；
                 失败时返回 None
        """
        # 结束时间
        millis_stamp = int(round(time.time() * 1000))

        # 如何处理虚假买点和虚假卖点，1000条数据中，第一条可能产生虚假的买点和卖点
        kline_json = binan.get_klines(symbol, timeInterval, 1000, None, millis_stamp)
        if type(kline_json).__name__ == 'list':
            return kline_json
        else:
            return None

    # 根据交易规则，格式化交易量
    def format_trade_quantity(self, originalQuantity):
        """
        根据交易所规则格式化交易数量

        将原始交易数量调整为符合交易所LOT_SIZE规则的值，确保数量为stepSize的整数倍，
        并且不小于最小交易量要求。

        :param originalQuantity: 原始期望的交易数量
        :return: 格式化后的合规交易数量
        """
        minQty = float(self.exchangeRule.minQty)
        print(self.symbol + " 原始交易量= " + str(originalQuantity))
        print(self.symbol + " 最小交易量限制= " + str(minQty))

        if self.exchangeRule is not None and minQty > 0:
            newQuantity = (originalQuantity // minQty) * minQty
        else:
            newQuantity = math.floor(originalQuantity)
        print(self.symbol + " 交易量格式化= " + str(newQuantity))
        return newQuantity

    def binance_func(self):
        """
        执行完整的自动化交易流程

        这是主要的交易入口函数，按以下步骤执行：
        1. 获取交易所规则
        2. 获取K线数据并转换为DataFrame
        3. 使用双均线策略判断交易方向
        4. 根据交易方向执行买入或卖出操作
        5. 如果没有明确信号且开启了卖出策略，则执行分批卖出检查
        6. 发送钉钉通知（异常情况或重要操作）

        异常处理：捕获所有异常并打印堆栈跟踪，同时通过钉钉发送错误信息。
        """
        print("交易币种: " + self.trade_coin)
        try:
            self.gain_exchangeRule(self.symbol)

            msgInfo = ""  # 钉钉消息
            isDefaultToken = False

            # 记录执行时间
            now = datetime.datetime.now()
            ts = now.strftime('%Y-%m-%d %H:%M:%S')
            print('执行开始时间：', ts)
            msgInfo = msgInfo + str(ts) + "\n"

            # 获取K线数据
            kline_list = self.gain_kline(self.symbol, kLine_type)
            # k线数据转为 DataFrame格式
            kline_df = dALines.klinesToDataFrame(kline_list)

            # 判断交易方向
            trade_direction = dALines.release_trade_stock(ma_x, ma_y, self.symbol, kline_df)

            if trade_direction is not None:

                if "buy," in trade_direction:

                    isToBuy = self.judgeToBuyCommand(self.orderInfoSavePath, trade_direction)

                    if isToBuy is False:
                        msgInfo = msgInfo + "服务正常3"
                        isDefaultToken = True
                    else:
                        isDefaultToken = False

                        # coin_base = "USDT"
                        asset_coin = binan.get_spot_asset_by_symbol(self.coin_base)
                        print(self.coin_base + " 资产：" + str(asset_coin))

                        # 购买，所用资金量
                        coin_base_count = float(asset_coin["free"])
                        if self.coin_base_count <= coin_base_count:
                            coin_base_count = self.coin_base_count

                        print("binance_func--可用资金量coin_base_count= " + str(coin_base_count))
                        # 查询当前价格
                        cur_price = binan.get_ticker_price(self.symbol)
                        # 购买量
                        quantity = self.format_trade_quantity(coin_base_count / float(cur_price))
                        # 购买
                        res_order_buy = binan.buy_limit(self.symbol, quantity, cur_price)
                        print("购买结果：")
                        print(res_order_buy)

                        # 存储买入订单信息
                        if res_order_buy is not None and "symbol" in res_order_buy:
                            res_order_buy["toBuy"] = trade_direction
                            self.writeOrderInfoWithSellStrategy(self.orderInfoSavePath, res_order_buy)

                        order_result_str = self.printOrderJsonInfo(res_order_buy)
                        msgInfo = "购买结果：\n" + order_result_str

                elif "sell," in trade_direction:
                    dictOrder = self.readOrderInfo(self.orderInfoSavePath)

                    if dictOrder is None:
                        msgInfo = msgInfo + "服务正常4--已无可售"
                        isDefaultToken = True
                    else:

                        asset_coin = binan.get_spot_asset_by_symbol(self.trade_coin)
                        print(self.trade_coin + " 资产：")
                        print(asset_coin)

                        quantity = self.format_trade_quantity(float(asset_coin["free"]))

                        # 查询当前价格
                        cur_price = binan.get_ticker_price(self.symbol)

                        if quantity <= 0:
                            msgInfo = msgInfo + "服务正常5--已无可售"
                            isDefaultToken = True
                        else:
                            isDefaultToken = False
                            # 卖出
                            res_order_sell = binan.sell_limit(self.symbol, quantity, cur_price)
                            # 清理本地订单信息
                            self.clearOrderInfo(self.orderInfoSavePath)
                            print("出售结果：")
                            print(res_order_sell)
                            order_result_str = self.printOrderJsonInfo(res_order_sell)
                            msgInfo = "卖出结果：\n" + str(order_result_str)

            else:
                if isOpenSellStrategy:
                    print("开启卖出策略---1")
                    msgInfo = self.sellStrategy(self.orderInfoSavePath)

                if msgInfo == "":
                    msgInfo = msgInfo + str(ts) + "\n"
                    print("暂不执行任何交易2")
                    msgInfo = msgInfo + "服务正常2"
                    isDefaultToken = True

            print("-----------------------------------------------\n")
        except Exception as ex:
            traceback.print_exc()  # 打印完整堆栈
            err_str = "出现如下异常：%s" % ex
            print(err_str)
            msgInfo = msgInfo + str(err_str) + "\n"

        finally:
            if "服务正常" in msgInfo:
                pass
            else:
                msg.dingding_warn(msgInfo, isDefaultToken)
