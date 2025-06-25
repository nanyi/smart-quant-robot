# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan

import requests,json

# windows
from app.authorization import dingding_token, dingding_token2, recv_window,api_secret,api_key
from app.BinanceAPI import BinanceAPI
# linux
# from app.authorization import dingding_token

class Message:
    """
    钉钉消息通知类
    
    封装钉钉机器人API，用于发送交易相关的通知和告警信息。支持买入、卖出订单的
    自动通知以及异常情况的告警推送。可配置多个钉钉token实现分级通知。
    """

    def buy_limit_msg(self, market, quantity, rate):
        """
        执行限价买单并发送钉钉通知
        
        调用Binance API创建限价买单，根据下单结果发送成功或失败的钉钉通知。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :param quantity: 购买数量
        :param rate: 限价价格
        :return: 成功时返回订单响应字典，失败时无返回值
        """
        try:
            res = BinanceAPI(api_key, api_secret).buy_limit(market, quantity, rate)
            if res['orderId']:
                buy_info = "报警：币种为：{cointype}。买单价为：{price}。买单量为：{num}".format(cointype=market, price=rate,
                                                                                           num=quantity)
                self.dingding_warn(buy_info)
                return res
        except BaseException as e:
            error_info = "报警：币种为：{cointype},买单失败.api返回内容为:{reject}".format(cointype=market,
                                                                                         reject=res['msg'])
            self.dingding_warn(error_info)

    def sell_limit_msg(self, market, quantity, rate):
        """
        执行限价卖单并发送钉钉通知
        
        调用Binance API创建限价卖单，根据下单结果发送成功或失败的钉钉通知。
        
        :param market: 交易对符号，例如 'BTCUSDT'
        :param quantity: 卖出数量
        :param rate: 限价价格
        :return: 订单响应字典（无论成功或失败都返回）
        """
        try:
            res = BinanceAPI(api_key, api_secret).sell_limit(market, quantity, rate)
            if res['orderId']:
                buy_info = "报警：币种为：{cointype}。卖单价为：{price}。卖单量为：{num}".format(cointype=market, price=rate,
                                                                                           num=quantity)
                self.dingding_warn(buy_info)
                return res
        except BaseException as e:
            error_info = "报警：币种为：{cointype},卖单失败.api返回内容为:{reject}".format(cointype=market,
                                                                                         reject=res['msg'])
            self.dingding_warn(error_info + str(res))
            return res

    def dingding_warn(self, text, isDefaultToken=True):
        """
        发送钉钉告警消息
        
        通过钉钉机器人Webhook发送文本消息。支持使用不同的token实现分级通知，
        当token未配置时会降级为控制台输出。
        
        :param text: 要发送的消息内容
        :param isDefaultToken: 是否使用默认token，True使用主token，False使用备用token
        """
        tmpToken = dingding_token if isDefaultToken else dingding_token2
        if (tmpToken == ''):
            print('dingidng:' + text)
            return
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        api_url = "https://oapi.dingtalk.com/robot/send?access_token=%s" % tmpToken
        print("api_url=")
        print(api_url)
        json_text = self._msg(text + "\n______")
        response = requests.post(api_url, json.dumps(json_text), headers=headers).content
        print(response)

    def _msg(self, text):
        """
        构建钉钉消息JSON格式
        
        将文本内容封装为钉钉机器人API要求的JSON格式，包含@提醒配置。
        
        :param text: 消息文本内容
        :return: 符合钉钉API规范的字典对象
        """
        json_text = {
            "msgtype": "text",
            "at": {
                "atMobiles": [
                    "11111"
                ],
                "isAtAll": False
            },
            "text": {
                "content": text
            }
        }
        return json_text

if __name__ == "__main__":
    msg = Message()
    print(msg.buy_limit_msg("EOSUSDT",4,2))