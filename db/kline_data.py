# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass
class KlineData:
    """K线数据模型
    
    用于存储单个K线周期的完整数据信息。
    Binance API返回的K线数据格式：
    [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, 成交额, 成交笔数, 主动买入量, 主动买入额, 忽略]
    """
    symbol: str
    interval: str
    open_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    close_time: int
    turnover: float = 0
    trade_count: int = 0
    buy_volume: float = 0
    buy_turnover: float = 0
    is_candle_closed: int = 1
    id: Optional[int] = None

    def to_tuple(self) -> tuple:
        return (
            self.symbol,
            self.interval,
            self.open_time,
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
            self.volume,
            self.close_time,
            self.turnover,
            self.trade_count,
            self.buy_volume,
            self.buy_turnover,
            self.is_candle_closed,
        )

    @classmethod
    def from_api_list(cls, data: list, symbol: str, interval: str) -> "KlineData":
        """从Binance API返回的列表数据创建KlineData
        
        :param data: Binance API返回的K线数据列表
        :param symbol: 交易对符号
        :param interval: K线周期
        :return: KlineData实例
        """
        return cls(
            symbol=symbol,
            interval=interval,
            open_time=int(data[0]),
            open_price=float(data[1]),
            high_price=float(data[2]),
            low_price=float(data[3]),
            close_price=float(data[4]),
            volume=float(data[5]),
            close_time=int(data[6]),
            turnover=float(data[7]) if len(data) > 7 else 0,
            trade_count=int(data[8]) if len(data) > 8 else 0,
            buy_volume=float(data[9]) if len(data) > 9 else 0,
            buy_turnover=float(data[10]) if len(data) > 10 else 0,
            is_candle_closed=1,
        )

    @classmethod
    def from_row(cls, row: dict) -> "KlineData":
        """从数据库行字典创建KlineData
        
        :param row: 数据库行字典
        :return: KlineData实例
        """
        return cls(
            id=row.get("id"),
            symbol=row["symbol"],
            interval=row["interval"],
            open_time=row["open_time"],
            open_price=row["open_price"],
            high_price=row["high_price"],
            low_price=row["low_price"],
            close_price=row["close_price"],
            volume=row["volume"],
            close_time=row["close_time"],
            turnover=row.get("turnover", 0),
            trade_count=row.get("trade_count", 0),
            buy_volume=row.get("buy_volume", 0),
            buy_turnover=row.get("buy_turnover", 0),
            is_candle_closed=row.get("is_candle_closed", 1),
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "interval": self.interval,
            "open_time": self.open_time,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "close_price": self.close_price,
            "volume": self.volume,
            "close_time": self.close_time,
            "turnover": self.turnover,
            "trade_count": self.trade_count,
            "buy_volume": self.buy_volume,
            "buy_turnover": self.buy_turnover,
            "is_candle_closed": self.is_candle_closed,
        }

    @staticmethod
    def to_dataframe(klines: List["KlineData"]) -> pd.DataFrame:
        """将KlineData列表转换为DataFrame
        
        :param klines: KlineData列表
        :return: DataFrame格式的K线数据
        """
        if not klines:
            return pd.DataFrame()

        data = {
            "openTime": [k.open_time for k in klines],
            "openPrice": [k.open_price for k in klines],
            "highPrice": [k.high_price for k in klines],
            "lowPrice": [k.low_price for k in klines],
            "closePrice": [k.close_price for k in klines],
            "volume": [k.volume for k in klines],
            "closeTime": [k.close_time for k in klines],
            "turnover": [k.turnover for k in klines],
            "tradeCount": [k.trade_count for k in klines],
            "buyVolume": [k.buy_volume for k in klines],
            "buyTurnover": [k.buy_turnover for k in klines],
        }
        df = pd.DataFrame(data)
        return df

    @staticmethod
    def from_api_list_to_dataframe(api_data: list, symbol: str, interval: str) -> pd.DataFrame:
        """将Binance API返回的列表直接转换为DataFrame
        
        :param api_data: Binance API返回的K线数据列表
        :param symbol: 交易对符号
        :param interval: K线周期
        :return: DataFrame格式的K线数据
        """
        if not api_data:
            return pd.DataFrame()

        klines = [KlineData.from_api_list(d, symbol, interval) for d in api_data]
        return KlineData.to_dataframe(klines)
