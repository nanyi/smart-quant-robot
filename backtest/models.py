# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    entry_price: float
    current_price: float = 0
    unrealized_pnl: float = 0

    def update_current_price(self, price: float):
        self.current_price = price
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity


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
    initial_capital: float  # 初始资金
    final_capital: float # 最终资金
    total_trades: int = 0 # 总交易次数
    winning_trades: int = 0 # 盈利交易次数
    losing_trades: int = 0  # 亏损交易次数
    total_profit: float = 0  # 总盈利
    total_loss: float = 0  # 总亏损
    max_drawdown: float = 0 # 最大回撤
    max_drawdown_ratio: float = 0
    win_rate: float = 0 # 胜率
    profit_factor: float = 0  # 盈利因子
    sharpe_ratio: float = 0  # 夏普比率

    def calculate(self):
        self.total_trades = self.winning_trades + self.losing_trades
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        if self.total_loss != 0:
            self.profit_factor = abs(self.total_profit / self.total_loss)
        if self.initial_capital > 0:
            self.max_drawdown_ratio = self.max_drawdown / self.initial_capital
