# -*- coding: utf-8 -*-
from backtest import BacktestEngine, BacktestReporter
from strategy import NBreakStrategy
from app.services import KlineService
from db.kline_data import KlineData


if __name__ == '__main__':
    symbol = 'SOLUSDT'

    kline_service = KlineService()
    klines = kline_service.get_from_db(symbol, '4h', limit=1000)
    df = KlineData.to_dataframe(klines)

    strategy = NBreakStrategy(ma_period=20, strong_rise_period=10, strong_rise_body_ratio=1.2, atr_period=10)

    engine = BacktestEngine(initial_capital=100000.0)

    print("开始精准N破战法回测...")
    stats = engine.run_with_data(strategy, df, symbol=symbol)

    print("回测报告")
    reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
    print(reporter.generate_text_report())