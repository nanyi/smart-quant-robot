# -*- coding: utf-8 -*-
from backtest import BacktestEngine, BacktestReporter
from strategy import CompositeStrategy, MAStrategy, RSIStrategy
from app.services import KlineService
from db.kline_data import KlineData

if __name__ == '__main__':
    symbol = 'DOGEUSDT'

    # 创建K线服务
    kline_service = KlineService()

    # 从数据库加载K线数据
    klines = kline_service.get_from_db(symbol, '15m', limit=1000)

    # 转换为DataFrame
    df = KlineData.to_dataframe(klines)

    # 创建策略组合
    strategies = [MAStrategy(short_period=5, long_period=60), RSIStrategy(period=14)]
    composite = CompositeStrategy(strategies, weights={'ma': 1.0, 'rsi': 0.8})

    # 创建回测引擎
    engine = BacktestEngine(initial_capital=10000.0)

    # 运行回测
    print("开始回测...")
    stats = engine.run_with_data(composite, df, symbol=symbol)

    # 生成JSON格式报告
    print("回测报告")
    reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
    # report_json = reporter.generate_json_report()
    #　print(report_json)
    print(reporter.generate_text_report())
