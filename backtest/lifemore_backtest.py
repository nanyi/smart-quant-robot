# -*- coding: utf-8 -*-
from backtest import BacktestEngine, BacktestReporter
from strategy import LivermoreStrategy
from app.services import KlineService
from db.kline_data import KlineData


if __name__ == '__main__':
    symbol = 'DOGEUSDT'

    kline_service = KlineService()
    klines = kline_service.get_from_db(symbol, '15m', limit=1000)
    df = KlineData.to_dataframe(klines)

    strategy = LivermoreStrategy(
        breakout_period=30,
        pyramid_ratio=0.05,
        stop_loss_ratio=0.10,
        exit_ratio=0.20,
    )

    engine = BacktestEngine(initial_capital=10000.0)

    print("开始利费莫尔策略回测...")
    stats = engine.run_with_data(strategy, df, symbol=symbol)

    print("回测报告")
    reporter = BacktestReporter(stats, engine.get_orders(), engine.get_trades())
    print(reporter.generate_text_report())
