# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from typing import List, Optional, Dict
import pandas as pd

from backtest.models import (
    BacktestOrder,
    BacktestPosition,
    BacktestTrade,
    BacktestStats,
    OrderSide,
    OrderType,
    OrderStatus,
    PositionSide,
)
from strategy.base import Signal, SignalType
from db.kline_repo import KlineRepo
from db.kline_data import KlineData


class BacktestEngine:
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate

        self.orders: List[BacktestOrder] = []
        self.trades: List[BacktestTrade] = []
        self.positions: Dict[str, BacktestPosition] = {}
        self.stats = BacktestStats(initial_capital=initial_capital, final_capital=initial_capital)

        self.kline_repo = KlineRepo()

    def load_data(
        self,
        symbol: str,
        interval: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        klines = self.kline_repo.get_by_symbol_interval(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
        if not klines:
            return pd.DataFrame()

        data = {
            "open_time": [k.open_time for k in klines],
            "open": [k.open_price for k in klines],
            "high": [k.high_price for k in klines],
            "low": [k.low_price for k in klines],
            "close": [k.close_price for k in klines],
            "volume": [k.volume for k in klines],
        }
        df = pd.DataFrame(data)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df

    def load_data_from_list(self, klines: List[KlineData]) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()

        data = {
            "open_time": [k.open_time for k in klines],
            "open": [k.open_price for k in klines],
            "high": [k.high_price for k in klines],
            "low": [k.low_price for k in klines],
            "close": [k.close_price for k in klines],
            "volume": [k.volume for k in klines],
        }
        df = pd.DataFrame(data)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df

    def run(
        self,
        strategy,
        symbol: str,
        interval: str,
        start_time: int = None,
        end_time: int = None,
        limit: int = 1000,
    ) -> BacktestStats:
        df = self.load_data(symbol, interval, start_time, end_time, limit)
        if df.empty:
            return self.stats

        return self.run_with_data(strategy, df, symbol)

    def run_with_data(self, strategy, df: pd.DataFrame, symbol: str) -> BacktestStats:
        for idx in range(len(df)):
            current_bar = df.iloc[idx] # K线
            current_price = current_bar["closePrice"] # 当前价格
            current_time = current_bar["openTime"] # 当前时间

            # 检查订单
            self._check_and_fill_orders(current_price, current_time)

            signal = strategy.calculate(df[:idx + 1], idx)
            if signal and signal.signal_type == SignalType.BUY:
                self._execute_buy(symbol, current_price, current_time, signal.weight)
            elif signal and signal.signal_type == SignalType.SELL:
                self._execute_sell(symbol, current_price, current_time)

            self._update_positions(current_price)

        self.stats.final_capital = self.current_capital
        self._calculate_stats()
        return self.stats

    def _check_and_fill_orders(self, current_price: float, current_time: datetime):
        for order in self.orders:
            if order.status != OrderStatus.PENDING:
                continue
            if order.side == OrderSide.BUY and order.price >= current_price:
                self._fill_order(order, current_price, current_time)
            elif order.side == OrderSide.SELL and order.price <= current_price:
                self._fill_order(order, current_price, current_time)

    def _fill_order(self, order: BacktestOrder, fill_price: float, fill_time: datetime):
        order.filled_quantity = order.quantity
        order.status = OrderStatus.FILLED
        order.update_time = pd.to_datetime(fill_time, unit="ms")

        commission = fill_price * order.quantity * self.commission_rate

        if order.side == OrderSide.BUY:
            self.current_capital -= fill_price * order.quantity + commission
            position = BacktestPosition(
                symbol=order.symbol,
                side=PositionSide.LONG,
                quantity=order.quantity,
                entry_price=fill_price,
                current_price=fill_price,
            )
            self.positions[order.symbol] = position
        else:
            self.current_capital += fill_price * order.quantity - commission
            if order.symbol in self.positions:
                del self.positions[order.symbol]

        trade = BacktestTrade(
            trade_id=str(uuid.uuid4()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            turnover=fill_price * order.quantity,
            commission=commission,
            trade_time=pd.to_datetime(fill_time, unit="ms"),
        )
        self.trades.append(trade)

    def _execute_buy(
        self, symbol: str, price: float, time: datetime, quantity_ratio: float = 1.0
    ):
        if symbol in self.positions:
            return

        usable_capital = self.current_capital * 0.95
        quantity = (usable_capital / price) * quantity_ratio

        if quantity * price < 10:
            return

        order = BacktestOrder(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
        )
        self.orders.append(order)
        self._fill_order(order, price, time)

    def _execute_sell(self, symbol: str, price: float, time: datetime):
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        order = BacktestOrder(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=position.quantity,
        )
        self.orders.append(order)
        self._fill_order(order, price, time)

    def _update_positions(self, current_price: float):
        for symbol, position in self.positions.items():
            position.update_current_price(current_price)

    def _calculate_stats(self):
        total_profit = 0.0
        total_loss = 0.0
        peak_capital = self.initial_capital
        max_drawdown = 0.0

        capital_curve = [self.initial_capital]

        for trade in self.trades:
            if trade.side == OrderSide.SELL:
                sell_revenue = trade.price * trade.quantity
                
                buy_cost = 0.0
                for prev_trade in self.trades:
                    if (prev_trade.symbol == trade.symbol and 
                        prev_trade.side == OrderSide.BUY and
                        prev_trade.trade_time <= trade.trade_time):
                        buy_cost += prev_trade.price * prev_trade.quantity
                
                pnl = sell_revenue - buy_cost - trade.commission
                
                if pnl > 0:
                    total_profit += pnl
                    self.stats.winning_trades += 1
                else:
                    total_loss += abs(pnl)
                    self.stats.losing_trades += 1

            current_capital = self.current_capital
            for symbol, position in self.positions.items():
                current_capital += position.unrealized_pnl

            capital_curve.append(current_capital)

            if current_capital > peak_capital:
                peak_capital = current_capital
            drawdown = peak_capital - current_capital
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        self.stats.total_profit = total_profit
        self.stats.total_loss = total_loss
        self.stats.max_drawdown = max_drawdown
        self.stats.calculate()

    def get_orders(self) -> List[BacktestOrder]:
        return self.orders

    def get_trades(self) -> List[BacktestTrade]:
        return self.trades

    def get_positions(self) -> Dict[str, BacktestPosition]:
        return self.positions
