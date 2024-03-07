# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan
from app.dingding import Message
from app.OrderManager import OrderManager

import datetime
import time

import schedule
import math
import json,os
from runtime_config import binance_market,binance_coinBase,binance_tradeCoin, binance_coinBase_count


orderManager_doge = OrderManager("USDT", 100, "DOGE", binance_market)

orderManager_eth = OrderManager("USDT", 100, "ETH", binance_market)

msgDing = Message()

# 发送消息通知

def dingding_notifier(message, isDefaultToken):
    # 记录执行时间
    now = datetime.datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    message = str(ts) + "\n" + message
    msgDing.dingding_warn(message, isDefaultToken)


def binance_func():
    orderManager_doge.binance_func()
    # time.sleep(5)
    # orderManager_eth.binance_func()


def send_service_info():
    str = "服务正常--ok"
    dingding_notifier(str, True)


# 创建循环任务
def tasklist():
    #清空任务
    print("服务启动")
    # 清空任务
    schedule.clear()
    # 创建一个按秒间隔执行任务
    # schedule.every().hours.at("04:05").do(binance_func)

    # 创建一个按秒间隔执行任务
    schedule.every(15).seconds.do(binance_func)

    # 创建一个按分钟间隔执行任务
    schedule.every(20).minutes.do(send_service_info)

    while True:
        schedule.run_pending()
        time.sleep(1)


# 调试看报错运行下面，正式运行用上面
if __name__ == "__main__":

    # 启动，先从币安获取交易规则， https://api.binance.com/api/v3/exchangeInfo
    tasklist()

    # binance_func()

