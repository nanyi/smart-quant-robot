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
    PositionRecord,
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
            current_bar = df.iloc[idx]
            current_price = current_bar["closePrice"]
            current_time = current_bar["openTime"]
            current_time = current_time if isinstance(current_time, datetime) else pd.to_datetime(current_time, unit="ms")

            self._check_and_fill_orders(current_price, current_time)

            before_df = df[:idx + 1]
            signal = strategy.calculate(before_df, idx)
            if signal and signal.signal_type == SignalType.BUY:
                self._execute_buy(symbol, current_price, current_time, signal.weight)
            elif signal and signal.signal_type == SignalType.SELL:
                self._execute_sell(symbol, current_price, current_time)

            self._update_positions(current_price)

        self._calculate_final_stats()
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
        order.update_time = fill_time

        commission = fill_price * order.quantity * self.commission_rate

        if order.side == OrderSide.BUY:
            self.current_capital -= fill_price * order.quantity + commission
            if order.symbol in self.positions:
                position = self.positions[order.symbol]
                total_cost = position.avg_entry_price * position.quantity + fill_price * order.quantity
                total_qty = position.quantity + order.quantity
                position.avg_entry_price = total_cost / total_qty
                position.quantity = total_qty
                position.current_price = fill_price
            else:
                position = BacktestPosition(
                    symbol=order.symbol,
                    side=PositionSide.LONG,
                    quantity=order.quantity,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                    open_time=fill_time,
                )
                self.positions[order.symbol] = position
        else:
            if order.symbol in self.positions:
                position = self.positions[order.symbol]
                pnl = (fill_price - position.avg_entry_price) * order.quantity - commission
                pnl_ratio = pnl / (position.avg_entry_price * order.quantity)
                hold_seconds = int((fill_time - position.open_time).total_seconds()) if position.open_time else 0

                record = PositionRecord(
                    symbol=order.symbol,
                    side=position.side,
                    quantity=order.quantity,
                    entry_price=position.avg_entry_price,
                    exit_price=fill_price,
                    pnl=pnl,
                    pnl_ratio=pnl_ratio,
                    commission=commission,
                    open_time=position.open_time or fill_time,
                    close_time=fill_time,
                    hold_seconds=hold_seconds,
                )
                self.stats.position_records.append(record)

                self.current_capital += fill_price * order.quantity - commission
                del self.positions[order.symbol]
            else:
                self.current_capital += fill_price * order.quantity - commission

        trade = BacktestTrade(
            trade_id=str(uuid.uuid4()),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            turnover=fill_price * order.quantity,
            commission=commission,
            trade_time=fill_time,
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

    def _calculate_final_stats(self):
        position_value = sum(p.position_value for p in self.positions.values())
        self.stats.cash = self.current_capital
        self.stats.position_value = position_value
        self.stats.final_capital = self.current_capital + position_value
        self.stats.current_positions = self.positions

        total_profit = 0.0
        total_loss = 0.0
        peak_capital = self.initial_capital
        max_drawdown = 0.0

        for record in self.stats.position_records:
            if record.pnl > 0:
                total_profit += record.pnl
            else:
                total_loss += abs(record.pnl)

        realized_pnl = total_profit - total_loss
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        current_capital = self.current_capital + unrealized_pnl

        capital_curve = [self.initial_capital, current_capital]

        if current_capital > peak_capital:
            peak_capital = current_capital
        drawdown = peak_capital - current_capital
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        self.stats.total_profit = total_profit
        self.stats.total_loss = total_loss
        self.stats.winning_trades = len([r for r in self.stats.position_records if r.pnl > 0])
        self.stats.losing_trades = len([r for r in self.stats.position_records if r.pnl <= 0])
        self.stats.max_drawdown = max_drawdown
        self.stats.calculate()

    def get_orders(self) -> List[BacktestOrder]:
        return self.orders

    def get_trades(self) -> List[BacktestTrade]:
        return self.trades

    def get_positions(self) -> Dict[str, BacktestPosition]:
        return self.positions
