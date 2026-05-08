# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class BacktestOrder:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    filled_quantity: float = 0
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)

    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED


@dataclass
class BacktestPosition:
    symbol: str
    side: PositionSide
    quantity: float
    avg_entry_price: float
    current_price: float = 0
    unrealized_pnl: float = 0
    unrealized_pnl_ratio: float = 0
    open_time: Optional[datetime] = None

    def update_current_price(self, price: float):
        self.current_price = price
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (price - self.avg_entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.avg_entry_price - price) * self.quantity
        if self.avg_entry_price > 0 and self.quantity > 0:
            self.unrealized_pnl_ratio = self.unrealized_pnl / (self.avg_entry_price * self.quantity)

    @property
    def position_value(self) -> float:
        return self.current_price * self.quantity


@dataclass
class PositionRecord:
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_ratio: float
    commission: float
    open_time: datetime
    close_time: datetime
    hold_seconds: int

    @property
    def hold_days(self) -> float:
        return self.hold_seconds / 86400


@dataclass
class BacktestTrade:
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    turnover: float
    commission: float = 0
    trade_time: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestStats:
    initial_capital: float
    final_capital: float = 0
    cash: float = 0
    position_value: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0
    total_loss: float = 0
    max_drawdown: float = 0
    max_drawdown_ratio: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    sharpe_ratio: float = 0
    position_records: List[PositionRecord] = field(default_factory=list)
    current_positions: Dict[str, BacktestPosition] = field(default_factory=dict)

    def calculate(self):
        self.total_trades = self.winning_trades + self.losing_trades
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        if self.total_loss != 0:
            self.profit_factor = abs(self.total_profit / self.total_loss)
        if self.initial_capital > 0:
            self.max_drawdown_ratio = self.max_drawdown / self.initial_capital
