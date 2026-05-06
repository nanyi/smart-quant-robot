# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan

import datetime
import time

import schedule

from app.OrderManager import OrderManager
from app.notifier import get_notifier
from app.services import KlineService
from db.manager import DBManager
from runtime_config import config


def init_kline_data():
    """启动时初始化K线数据"""
    symbol = config.get('trade.binance_tradeCoin', 'DOGE') + config.get('trade.binance_coinBase', 'USDT')
    interval = config.get('trade.kLine_type', '15m')
    
    DBManager.get_instance().init_kline_table()
    
    kline_service = KlineService()
    count = kline_service.get_count(symbol, interval)
    
    if count < 100:
        print(f"K线数据不足（{count}条），正在从Binance获取...")
        kline_service.fetch_and_save(symbol, interval, limit=1000)
    else:
        print(f"数据库中已有 {count} 条K线数据")


init_kline_data()

orderManager_doge = OrderManager(
    config.get('trade.binance_coinBase', 'USDT'),
    config.get('trade.binance_coinBase_count', 20),
    config.get('trade.binance_tradeCoin', 'DOGE'),
    config.get('trade.binance_market', 'SPOT')
)

orderManager_eth = OrderManager(
    config.get('trade.binance_coinBase', 'USDT'),
    config.get('trade.binance_coinBase_count', 20),
    "ETH",
    config.get('trade.binance_market', 'SPOT')
)

msgDing = get_notifier()


def dingding_notifier(message, isDefaultToken):
    """
    发送钉钉消息通知
    :param message:
    :param isDefaultToken:
    :return:
    """
    # 记录执行时间
    now = datetime.datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    message = str(ts) + "\n" + message
    msgDing.send(message, isDefaultToken)


def binance_func():
    orderManager_doge.binance_func()
    # time.sleep(5)
    # orderManager_eth.binance_func()


def send_service_info():
    str = "服务正常--ok"
    dingding_notifier(str, True)


def tasklist():
    """
    创建循环任务
    :return:
    """
    print("服务启动")
    # 清空任务
    schedule.clear()
    # 创建一个按秒间隔执行任务
    # schedule.every().hours.at("04:05").do(binance_func)

    # 创建一个按秒间隔执行任务
    schedule.every(15).seconds.do(binance_func)

    # 创建一个按分钟间隔执行任务
    schedule.every(20).minutes.do(send_service_info)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n服务已停止")

# 调试看报错运行下面，正式运行用上面
if __name__ == "__main__":
    # 启动，先从币安获取交易规则：https://api.binance.com/api/v3/exchangeInfo
    # tasklist()

    binance_func()
    # t = orderManager_eth.get_spot_asset_by_symbol(binance_coinBase)
    # print(t)
